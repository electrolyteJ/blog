---
layout: post
title: 网络 | OkHttp的金牌讲师Exchange
description: HTTP1 && HTTP2
author: 电解质
date: 2021-04-29 22:50:00
share: true
tag: 
- elementary/network
- android
---
* TOC
{:toc}
如果说Connection是ConnectInterceptor的最佳发言人，那么Exchange绝对是CallServerInterceptor的金牌讲师,接下来我们就来讲讲Exchange如何在CallServerInterceptor这里发光发热。

CallServerInterceptor
{:.filename}
```java
class CallServerInterceptor(private val forWebSocket: Boolean) : Interceptor {

  @Throws(IOException::class)
  override fun intercept(chain: Interceptor.Chain): Response {
    val realChain = chain as RealInterceptorChain
    val exchange = realChain.exchange!!
    val request = realChain.request
    val requestBody = request.body
    val sentRequestMillis = System.currentTimeMillis()
    ...
    var responseBuilder: Response.Builder? = null
    var sendRequestException: IOException? = null
    try {
      exchange.writeRequestHeaders(request)

      if (HttpMethod.permitsRequestBody(request.method) && requestBody != null) {
        ...
      } else {
        exchange.noRequestBody()
      }

      if (requestBody == null || !requestBody.isDuplex()) {
        exchange.finishRequest()
      }
    } catch (e: IOException) {
      ...
    }

    try {
      if (responseBuilder == null) {
        responseBuilder = exchange.readResponseHeaders(expectContinue = false)!!
        ...
      }
      var response = responseBuilder
          .request(request)
          .handshake(exchange.connection.handshake())
          .sentRequestAtMillis(sentRequestMillis)
          .receivedResponseAtMillis(System.currentTimeMillis())
          .build()
      ...
      response = if (forWebSocket && code == 101) {
        // Connection is upgrading, but we need to ensure interceptors see a non-null response body.
        response.newBuilder()
            .body(EMPTY_RESPONSE)
            .build()
      } else {
        response.newBuilder()
            .body(exchange.openResponseBody(response))
            .build()
      }
      ...
      return response
    } catch (e: IOException) {
      ...
    }
  }
}
```
首先我们假设发送的请求为get，那么起流程就是如下面这样
1. exchange.writeRequestHeaders(request)
2. exchange.finishRequest()
3. responseBuilder = exchange.readResponseHeaders(expectContinue = false)!!
4. response.newBuilder().body(exchange.openResponseBody(response)).build()

先将request header写入buffer然后flush完成发送请求，当服务器响应了请求再读取response header和body，然后将他们构建出一个新的response发送给上层应用。

再来说说post请求
1. exchange.writeRequestHeaders(request)
2. val bufferedRequestBody = exchange.createRequestBody(request, false).buffer()
3. exchange.finishRequest()
4. responseBuilder = exchange.readResponseHeaders(expectContinue = false)!!
5. response.newBuilder().body(exchange.openResponseBody(response)).build()

post数据时会createRequestBody出一个输出流将body数据写入。post请求提出了一种优化post大文件的方案，就是在request header加入`Expect: 100-continue`,在libcurl中如果是post大于1024字节的数据，才会通过100-continue去询问服务器愿不愿意接收客户端的请求body，如果愿意就放回100，不愿意就不能发送请求body数据。Okhttp中也是提供`Expect: 100-continue`，不过要不要使用并不是由Okhttp检查post的字节数大于1024，而是取决于request header是不是有这个字段。

Exchange在这个发送请求，接收响应的过程中有着重要的地位，但是深入阅读这个类你会发现，它其实是个工具人，对于数据的编解码具体实现可以说基本没有，全全加给你了ExchangeCodec。ExchangeCodec类是个高度抽象的接口，它提出了要进行流的编解码应该具备一些什么功能，而其追随者Http1ExchangeCodec与Http2ExchangeCodec,将来可能还有Http3ExchangeCodec，它们都是具体的实践者，实现了一整套编解码方法。在http2协议中，每个请求多会有一个自己的stream和codec，多个codec会同时使用Http2Writer写入/Http2Reader读取帧数据到tcp连接通道

这里先认识几个http2协议中的角色
- Http2Writer/Http2Reader: http2中二进制帧的编解码类，其作用是将上层的数据编解码成二进制帧数据并且写入到tcp连接buffer
- Http2Stream/Http2ExchangeCodec：一个tcp连接存在多个Http2Stream/Http2ExchangeCodec对多个请求响应进行codec，Http2Stream每次进行帧处理都会去调用Http2Writer/Http2Reader，所以相对来更上层。
- Http2Connection：一个Http2Connection表示一个tcp连接，保存了多个Http2Stream
- ReaderRunnable：一个不停read帧数据的任务(Http2Reader的封装类)

ExchangeCodec
{:.filename}
```java
/** Encodes HTTP requests and decodes HTTP responses. */
interface ExchangeCodec {
  /** Returns the connection that carries this codec. */
  val connection: RealConnection

  /** Returns an output stream where the request body can be streamed. */
  @Throws(IOException::class)
  fun createRequestBody(request: Request, contentLength: Long): Sink

  /** This should update the HTTP engine's sentRequestMillis field. */
  @Throws(IOException::class)
  fun writeRequestHeaders(request: Request)

  /** Flush the request to the underlying socket. */
  @Throws(IOException::class)
  fun flushRequest()

  /** Flush the request to the underlying socket and signal no more bytes will be transmitted. */
  @Throws(IOException::class)
  fun finishRequest()

  /**
   * Parses bytes of a response header from an HTTP transport.
   *
   * @param expectContinue true to return null if this is an intermediate response with a "100"
   * response code. Otherwise this method never returns null.
   */
  @Throws(IOException::class)
  fun readResponseHeaders(expectContinue: Boolean): Response.Builder?

  @Throws(IOException::class)
  fun openResponseBodySource(response: Response): Source

  ....
}
```
ExchangeCodec接口中主要有四个方法需要关注，处理request的header和body(writeRequestHeaders、createRequestBody)；处理response的header和body(readResponseHeaders、openResponseBodySource)。HTTP1的header采用的是文本形式，body有像json这样的文本形式，也有采用protobuf这样的二进制。HTTP2强制header和body都采用二进制形式，其中就引入了帧的概念。

```java
class Http2ExchangeCodec(
  client: OkHttpClient,
  override val connection: RealConnection,
  private val chain: RealInterceptorChain,
  private val http2Connection: Http2Connection
) : ExchangeCodec {
  ...

  override fun writeRequestHeaders(request: Request) {
    if (stream != null) return

    val hasRequestBody = request.body != null
    val requestHeaders = http2HeadersList(request)
    stream = http2Connection.newStream(requestHeaders, hasRequestBody)
    // We may have been asked to cancel while creating the new stream and sending the request
    // headers, but there was still no stream to close.
    if (canceled) {
      stream!!.closeLater(ErrorCode.CANCEL)
      throw IOException("Canceled")
    }
    stream!!.readTimeout().timeout(chain.readTimeoutMillis.toLong(), TimeUnit.MILLISECONDS)
    stream!!.writeTimeout().timeout(chain.writeTimeoutMillis.toLong(), TimeUnit.MILLISECONDS)
  }

  override fun createRequestBody(request: Request, contentLength: Long): Sink {
    return stream!!.getSink()
  }
  ...
}
```
当发起一个请求，调用者构建的request header经过writeRequestHeaders会被encode为二进制。首先对request各个header进行utf-8编码，然后将编码之后的数据通过Http2Writer#headers进一步压缩编码(其中压缩编码采用的是Hpack)以头部帧的形式写入到tcp连接buffer中。http2中定义了10种帧类型，这里讲到的头部帧是其中一个，还有其他可以看下面的代码。
```java
  const val TYPE_DATA = 0x0 //数据帧
  const val TYPE_HEADERS = 0x1 //头部帧
  const val TYPE_PRIORITY = 0x2  //服务器处理流的优先级
  const val TYPE_RST_STREAM = 0x3 //终止流帧
  const val TYPE_SETTINGS = 0x4 //网络配置帧
  const val TYPE_PUSH_PROMISE = 0x5 
  const val TYPE_PING = 0x6 //心跳，rtt帧
  const val TYPE_GOAWAY = 0x7 
  const val TYPE_WINDOW_UPDATE = 0x8 //流量控制帧，为什么需要这个帧？由于http2中一个tcp可以有多个stream同时写入任意个请求，所以需要控制网络中的流量，避免失控。
  const val TYPE_CONTINUATION = 0x9
```
接下来我们来看看body逻辑，createRequestBody的方法体很简单`return stream!!.getSink()`,Http2Stream中的getSink获得到的是FramingSink,将body数据encode为帧。request body中的data通过FramingSink被写入到内部的sendBuffer缓存(最大16k).


```java
class Http2ExchangeCodec(
  client: OkHttpClient,
  override val connection: RealConnection,
  private val chain: RealInterceptorChain,
  private val http2Connection: Http2Connection
) : ExchangeCodec {
  ...

 override fun readResponseHeaders(expectContinue: Boolean): Response.Builder? {
    val stream = stream ?: throw IOException("stream wasn't created")
    val headers = stream.takeHeaders()
    val responseBuilder = readHttp2HeadersList(headers, protocol)
    return if (expectContinue && responseBuilder.code == HTTP_CONTINUE) {
      null
    } else {
      responseBuilder
    }
  }
  override fun openResponseBodySource(response: Response): Source {
    return stream!!.source
  }


  ...
}
```
Http2Stream#takeHeaders获取头部帧，其数据来源于Http2Connection$ReaderRunnable任务，其任务会不停的重Http2Reader#nextFrame取并传给Http2Stream#takeHeaders


## *参考资料*{:.header2-font}
[HTTP 协议入门](http://www.ruanyifeng.com/blog/2016/08/http.html)
[[译] HPACK：http2中沉默的杀手](https://juejin.im/post/6844904047594438670)
[HTTP/2 中的帧定义](https://halfrost.com/http2-http-frames-definitions/)
[HTTP/3 详解](https://www.bookstack.cn/read/http3-explained-zh/h3-h2.md)