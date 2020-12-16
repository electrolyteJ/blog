---
layout: post
title: 网络 --- OkHttp Protocol
description: HTTP1 && HTTP2 && QUIC
author: 电解质
date: 2020-11-02 22:50:00
share: true
comments: true
tag: 
- app-design/network
---
## *1.Summary*{:.header2-font}
这一篇文章我们来讲讲HTTP1 && HTTP2 && QUIC

## *2.Introduction*{:.header2-font}

OkHttp中将编码request和解码response抽到`ExchangeCodec`类,HTTP1协议的实现类为Http1ExchangeCodec，HTTP2协议的实现类为Http2ExchangeCodec。
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
ExchangeCodec接口中主要有四个方法需要关注，处理request的header和body(writeRequestHeaders、createRequestBody)；处理response的header和body(readResponseHeaders、openResponseBodySource)。HTTP1的header采用的是文本形式，body有像json这样的文本形式，也有采用protobuf这样的二进制(其编解码过程被熟知已被破解)。HTTP2强制header和body都采用二进制形式，其中就引入了帧的概念。

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
当发起一个请求，调用者构建的request header经过writeRequestHeaders会被encode为二进制。首先先对request各个header进行utf-8编码，然后将编码之后的数据通过Http2Writer#header进一步压缩编码(其中压缩编码采用的是Hpack)。HTTP2中定义了10种帧类型，这里讲到的头部帧是其中一个，还有其他可以看下面的代码。
```java
  const val TYPE_DATA = 0x0
  const val TYPE_HEADERS = 0x1
  const val TYPE_PRIORITY = 0x2
  const val TYPE_RST_STREAM = 0x3
  const val TYPE_SETTINGS = 0x4
  const val TYPE_PUSH_PROMISE = 0x5
  const val TYPE_PING = 0x6
  const val TYPE_GOAWAY = 0x7
  const val TYPE_WINDOW_UPDATE = 0x8
  const val TYPE_CONTINUATION = 0x9
```
接下来我们来看看body逻辑，createRequestBody的方法体很简单`return stream!!.getSink()`,Http2Stream中的getSink获得到的是FramingSink，其重写了Sink#write。request body中的data通过FramingSink被写入到内部的sendBuffer缓存(最大16k).


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


## *2.Reference*{:.header2-font}
[HTTP 协议入门](http://www.ruanyifeng.com/blog/2016/08/http.html)
[[译] HPACK：http2中沉默的杀手](https://juejin.im/post/6844904047594438670)
[HTTP/2 中的帧定义](https://halfrost.com/http2-http-frames-definitions/)