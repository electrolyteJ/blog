---
layout: post
title: 网络 --- Volley vs. OkHttp
description: 面向Socket编程：OkHttp = Volley + HttpURLConnection
author: 电解质
date: 2020-10-19 22:50:00
share: true
comments: true
tag: 
- app-design/network
published : true
---
## *1.Summary*{:.header2-font}
========================
Volley
=========================
![network]({{site.baseurl}}/asset/network/Volley.jpg)

========================
OkHttp
=========================
![network]({{site.baseurl}}/asset/network/OkHttp.jpg)
&emsp;&emsp;由于Volley是在HttpURLConnection的基础上完成的网路库，所以我们只对比Volley和OkHttp共有的部分。
- request/response的网络请求池
- cache池
- retry次数

## *2.Introduction*{:.header2-font}
## *a.Dispatcher*{:.header3-font}
========================
Volley
=========================
&emsp;&emsp;Volley的Dispatcher主要有两个队列
```
mNetworkQueue
mWaitingRequestQueue

NetworkDispatcher的线程池大小为4
创建了一个ByteArrayPool最多只能读4k的buf
```
&emsp;&emsp;Volley并不存在同步请求，都是采用异步请求。所以只要两个队列就行。对于处于in flight的request也多是暂时找了个队列存放起来。由于网络请求池子被限制最多只能跑4个线，`所以对于Volley来说只能并发4个线程`。

========================
OkHttp
=========================
&emsp;&emsp;OkHttp的Dispatcher主要有如下三个队列
```
runningSyncCalls: ArrayDeque<RealCall>
readyAsyncCalls:ArrayDeque<AsyncCall>
runningAsyncCalls:ArrayDeque<AsyncCall>

maxRequests = 64
maxRequestsPerHost = 5
//线程数最大为整型最大值2^31-1，1min保活，该池子主要用于异步发送请求
executorService/executorServiceOrNull(corePoolSize = 0,maximumPoolSize = Int.MAX_VALUE,keepAliveTime = 60,unit = s,workQueue=SynchronousQueue ) 
```
&emsp;&emsp;每一次网络请求都会被当成一次call并且被推到队列里面。有时候是同步请求有时候是异步请求，所以OkHttp会初始化三个目的不一样的队列。`对于正在并发请求的数量(runningAsyncCalls size)，OkHttp最多64个，每个host最多5个`，请求池最多可容纳整型的最大值，可以近似看成无穷大，每个线程保活1分钟，没有核心固定的线程,相当于JDK中提供的Executors#newCachedThreadPool,也就是缓存池。

&emsp;&emsp;对比一下Volley和OkHttp的并发数量，显然太少，并发的数量更多需要根据cpu核数以及网络类型来计算。所以使用JDK提供的一系列Executor工具，就能高效使用简单控制线程。


## *b.Cache*{:.header3-font}
&emsp;&emsp;首先得了解HTTP是如何处理缓存的
```
通用首部字段
cache control
请求首部字段
If-Match / If-None-Match
If-Modified-Since / If-Unmodified-Since
响应首部字段
ETag
Expires
Last-Modified
Date
Age
```
### 1. 新鲜度检查（freshness）
response缓存的字段
```
Date:获取服务器时间（绝对时间）
Age：过期时间（相对时间）
ETag：tag号
Last-Modified：最后被修改的时间（绝对时间）

# HTTP1.0使用
Expires：过期时间（绝对时间）
# HTTP1.1使用
cache control 
- noCache：跳过本地、CDN等新鲜度验证，必须与源服务器验证。
- must-revalidate:本地cache到期，必须跳过CDN等缓存服务器，到源服务器验证
- noStore：禁止使用缓存
- onlyIfCached:只取本地缓存
- maxAgeSeconds：缓存时长(相对时间)
- private：只保留本地，其他中间缓存服务部保留
- public：不能缓存的也多变成能缓存，比如身份验证
- maxStaleSeconds:客户端可以接受超过多久的缓存响应
- minFreshSeconds：期望在指定时间内的响应仍有效
```
&emsp;&emsp;第一次请求服务器要数据的时候，响应客户端请求的response header会增加一些缓存字段，来告诉客户端下发的文件是有缓存有效期的，然后当下次客户端再次请求时，就会对文件的新鲜度进行检查，如果还可以用就使用之前保存下来的副本，反之，则重新进行网络请求。所以新鲜度的检查是在本地完成的。

### 2. 再验证
条件请求
```
If-None-Match+ETag：若客户端的etag和服务的etag相同则再验证命中，返回304，未命中返回200 ok
If-Modified-Since+Last-Modified：上次缓存之后若无被修改则再验证命中，返回304，未命中返回200 ok
```
&emsp;&emsp;这里接着新鲜度检查往下走，如果过期了，客户端可以携带If-xxx-xxx的字段发送条件请求，对服务器的资源进行再次检验，服务器通过客户端给的ETag值 or Last-Modified值对资源进行验证，如果发现命中缓存，就返回304，没有的话返回200并给新的资源
&emsp;&emsp;cache这块两个库都是采用lru算法来管理disk资源,也可以说OkHttp借鉴了Volley这块很多代码处理，OkHttp为了支持高并发，拿掉了response body在内存中的缓存，保存了header等一些相关信息。

========================
Volley
=========================
&emsp;&emsp;Volley cache一些基本信息
```
Cache接口
Cache&Entry
DiskBasedCache
//缓存heard
mEntries = new LinkedHashMap<Stirng,CacheHeader>(16, .75f, true);
//缓存body
- size :disk cacah =5 * 1024 * 1024(5m) 
- directory:缓存位置/data/data/<application package>/cache/volley
```
&emsp;&emsp;Volley的缓存header:主要缓存key(http method+url)对应的CacheHeader(跟过期相关的字段还有response的header）
```java
    static class CacheHeader {
        /**
         * The size of the data identified by this CacheHeader on disk (both header and data).
         *
         * <p>Must be set by the caller after it has been calculated.
         *
         * <p>This is not serialized to disk.
         */
        long size;

        /** The key that identifies the cache entry. */
        final String key;

        /** ETag for cache coherence. */
        final String etag;

        /** Date of this response as reported by the server. */
        final long serverDate;

        /** The last modified date for the requested object. */
        final long lastModified;

        /** TTL for this record. */
        final long ttl;

        /** Soft TTL for this record. */
        final long softTtl;

        /** Headers from the response resulting in this cache entry. */
        final List<Header> allResponseHeaders;
}
private String getFilenameForKey(String key) {
        int firstHalfLength = key.length() / 2;
        String localFilename = String.valueOf(key.substring(0, firstHalfLength).hashCode());
        localFilename += String.valueOf(key.substring(firstHalfLength).hashCode());
        return localFilename;
    }
```
&emsp;&emsp;Volley的缓存body:主要缓存 key(getFilenameForKey方法)对应的文件(response body为存储内容)，可以简单理解一个url对应一个缓存文件。缓存文件存放的位置并不是sd卡，而是保存在ROM分配给apk的cache位置。当缓存数据`超过5M`就会调用`pruneIfNeeded`清理lru算出来的数据。

========================
OkHttp
=========================
&emsp;&emsp;OkHttp的cache一些基本信息
```
Cache(Entry描述的是缓存日志的内容信息)

DiskLruCache(Snapshot、Entry描述的是缓存日志的文件名信息)
 
 #缓存meta 和 body的快照
 Snapshot

# 能在缓存日志中存多少个文件名信息是由maxSize决定
#缓存header
lruEntries = LinkedHashMap<String, Entry>(0, 0.75f, true)

#lruEntries的日报
JOURNAL_FILE = "journal"
JOURNAL_FILE_TEMP = "journal.tmp"
JOURNAL_FILE_BACKUP = "journal.bkp"

# 缓存body ENTRY_COUNT = 2
会创建两种类型缓存文件，总计4个文件
- clean(<url>.md5().hex().0 <url>.md5().hex().1)
- dirty(<url>.md5().hex().0.tmp <url>.md5().hex().1.tmp)
```
&emsp;&emsp;OkHttp的缓存设计和Volley大同小异，内存中保留一份header相关，disk保存body，他们都是来源于Snapshot(封装了io流)。当然也有不同的地方，比如代码整体可读性更高，还有提供了缓存的日报。如果用户对cache操作记录超过2000次,则会将内存中的lruEntries写入到日报中。`最大字节数和缓存目录需要使用者设置`,如果超过使用者设置的字节数，则会调用trimToSize使用lru清理。
缓存的header内容大致如下
```
     *
     * ```
     * http://google.com/foo
     * GET
     * 2
     * Accept-Language: fr-CA
     * Accept-Charset: UTF-8
     * HTTP/1.1 200 OK
     * 3
     * Content-Type: image/png
     * Content-Length: 100
     * Cache-Control: max-age=600
     * ```
     *
     * A typical HTTPS file looks like this:
     *
     * ```
     * https://google.com/foo
     * GET
     * 2
     * Accept-Language: fr-CA
     * Accept-Charset: UTF-8
     * HTTP/1.1 200 OK
     * 3
     * Content-Type: image/png
     * Content-Length: 100
     * Cache-Control: max-age=600
     *
     * AES_256_WITH_MD5
     * 2
     * base64-encoded peerCertificate[0]
     * base64-encoded peerCertificate[1]
     * -1
     * TLSv1.2
     * ```
```
缓存的日报的记录大致如下
```
   *
   *     libcore.io.DiskLruCache
   *     1
   *     100
   *     2
   *
   *     CLEAN 3400330d1dfc7f3f7f4b8d4d803dfcf6 832 21054
   *     DIRTY 335c4c6028171cfddfbaae1a9c313c52
   *     CLEAN 335c4c6028171cfddfbaae1a9c313c52 3934 2342
   *     REMOVE 335c4c6028171cfddfbaae1a9c313c52
   *     DIRTY 1ab96a171faeeee38496d8b330771a7a
   *     CLEAN 1ab96a171faeeee38496d8b330771a7a 1600 234
   *     READ 335c4c6028171cfddfbaae1a9c313c52
   *     READ 3400330d1dfc7f3f7f4b8d4d803dfcf6
   *
```

缓存策略
```kotlin
      val responseCaching = cacheResponse.cacheControl

      val ageMillis = cacheResponseAge()
      var freshMillis = computeFreshnessLifetime()

      if (requestCaching.maxAgeSeconds != -1) {
        freshMillis = minOf(freshMillis, SECONDS.toMillis(requestCaching.maxAgeSeconds.toLong()))
      }

    //在某个时间段内依然有效
      var minFreshMillis: Long = 0
      if (requestCaching.minFreshSeconds != -1) {
        minFreshMillis = SECONDS.toMillis(requestCaching.minFreshSeconds.toLong())
      }

      var maxStaleMillis: Long = 0
      if (!responseCaching.mustRevalidate && requestCaching.maxStaleSeconds != -1) {
        maxStaleMillis = SECONDS.toMillis(requestCaching.maxStaleSeconds.toLong())
      }

      if (!responseCaching.noCache && ageMillis + minFreshMillis < freshMillis + maxStaleMillis) {
        val builder = cacheResponse.newBuilder()
        if (ageMillis + minFreshMillis >= freshMillis) {
          builder.addHeader("Warning", "110 HttpURLConnection \"Response is stale\"")
        }
        val oneDayMillis = 24 * 60 * 60 * 1000L
        if (ageMillis > oneDayMillis && isFreshnessLifetimeHeuristic()) {
          builder.addHeader("Warning", "113 HttpURLConnection \"Heuristic expiration\"")
        }
        return CacheStrategy(null, builder.build())
      }
```

&emsp;&emsp;这里对比一下Volley和OkHttp

## *c.Retry*{:.header3-font}

========================
Volley
=========================
```
socket连接时间2.5s
最多retry一次
超时乘积因子(The default backoff multiplier)=1

retry一次，连接时间就等于2.5 * 1+2.5 =5s
```

========================
OkHttp
=========================
```kotlin
        } catch (e: RouteException) {
          // The attempt to connect via a route failed. The request will not have been sent.
          if (!recover(e.lastConnectException, call, request, requestSendStarted = false)) {
            throw e.firstConnectException.withSuppressed(recoveredFailures)
          } else {
            recoveredFailures += e.firstConnectException
          }
          newExchangeFinder = false
          continue
        }
```
&emsp;&emsp;retry过程会不停的切route来尝试连接可以用的网络，只有遇到不可retry的情况ProtocolException SocketTimeoutException SSLHandshakeException/CertificateException SSLPeerUnverifiedException FileNotFoundException才会终止retry


## *3.More*{:.header2-font}
========================
OkHttp ConnectInterceptor/CallServerInterceptor
=========================
&emsp;&emsp;OkHttp定义了连接的类RealConnection(Connection)，对于如何管理连接这种资源，采用池子的方式RealConnectionPool(ConnectionPool)。`连接池最多只能空闲5个连接，每个连接最多保活5min`，这个连接池并不存在上限，也就是有多少连接存多少。相对于请求池保活1分钟，连接池保活5分钟,其连接过程是一种巨大的时间与空间的消耗。
&emsp;&emsp;既然有了管理连接的池子，OkHttp也提供了find/retry连接的类，可能为了遵循设计模式中的单一原则并没有将find/retry放在RealConnectionPool类中去实现，而是通过ExchangeFinder这样一个类提供了这样一些功能。
&emsp;&emsp;这里我们需要讲讲组合成连接的组件们
- 地址路由Route 路由选择器RouteSelector 路由失败的名单RouteDatabase
- 数据交换器Exchange  ExchangeCodec(Http1ExchangeCodec、Http2ExchangeCodec)

## *4.Reference*{:.header2-font}
[Volley 源码解析](http://a.codekk.com/detail/Android/grumoon/Volley%20%E6%BA%90%E7%A0%81%E8%A7%A3%E6%9E%90)
[HTTP cache](https://developers.google.com/web/fundamentals/performance/optimizing-content-efficiency/http-caching)




