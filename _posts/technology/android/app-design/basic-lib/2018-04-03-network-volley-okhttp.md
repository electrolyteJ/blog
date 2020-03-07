---
layout: post
title: 网络 --- Volley vs. OkHttp
description: 面向Socket编程：OkHttp = Volley + HttpURLConnection
author: 电解质
date: 2018-04-03 22:50:00
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
&emsp;&emsp;
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
&emsp;&emsp;Volley并不存在同步请求，都是采用异步请求。所以只要两个队列就行。对于处于in flight的request也多是暂时找了个队列存放起来。由于网络请求池子被限制最多只能跑4个线，所以对于Volley来说只能并发4个线程。

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
//线程数最大为整型最大值2^31-1，一分钟保活，该池子主要用于异步发送请求
executorService/executorServiceOrNull(corePoolSize = 0,maximumPoolSize = Int.MAX_VALUE,keepAliveTime = 60,unit = s,workQueue=SynchronousQueue ) 
```
&emsp;&emsp;每一次网络请求都会被当成一次call并且被推到队列里面。有时候是同步请求有时候是异步请求，所以OkHttp会初始化三个目的不一样的队列。对于正在并发请求的数量(runningAsyncCalls size)，OkHttp最多64个，每个host最多5个，网络请求池最多可容纳整型的最大值，可以近似看成无穷大，每个线程闲置1分钟，没有核心固定的线程,相当于JDK中提供的Executors#newCachedThreadPool,也就是缓存池。

&emsp;&emsp;对比一下Volley和OkHttp的并发数量，显然太少，并发的数量更多需要根据cpu核数以及网络类型来计算。所以使用JDK提供的一系列Executor工具，就能高效使用简单控制线程。


## *b.Cache*{:.header3-font}
&emsp;&emsp;cache这块两个库都是采用lru算法来管理disk资源,也可以说OkHttp借鉴了Volley这块很多代码处理，OkHttp为了支持高并发，拿掉了response body在内存中的缓存，保存了header等一些相关信息。

========================
Volley
=========================
&emsp;&emsp;Volley的cache一些基本信息
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
&emsp;&emsp;Volley的缓存body:主要缓存 key(getFilenameForKey方法)对应的文件(response body为存储内容)，可以简单理解一个url对应一个缓存文件。缓存文件存放的位置并不是sd卡，而是保存在ROM分配给apk的cache位置。当缓存数据超过5m就会调用pruneIfNeeded清理lru算出来的数据。

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

# 缓存body
ENTRY_COUNT = 2
会创建两种类型缓存文件，总计4个文件
- clean(<url>.md5().hex().0 <url>.md5().hex().1)
- dirty(<url>.md5().hex().0.tmp <url>.md5().hex().1.tmp)

#日报
JOURNAL_FILE = "journal"
JOURNAL_FILE_TEMP = "journal.tmp"
JOURNAL_FILE_BACKUP = "journal.bkp"

```
&emsp;&emsp;OkHttp的缓存设计和Volley大同小异，内存中保留一份header相关，disk保存body，他们都是来源于Snapshot(封装了io流)。当然也有不同的地方，比如代码整体可读性更高，还有提供了缓存的日报。日报中当用户记录超过2000则会使用lru清理，最大字节数需要使用者设置
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
缓存的日报大致如下
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

## *3.Reference*{:.header2-font}
[Volley 源码解析](http://a.codekk.com/detail/Android/grumoon/Volley%20%E6%BA%90%E7%A0%81%E8%A7%A3%E6%9E%90)



