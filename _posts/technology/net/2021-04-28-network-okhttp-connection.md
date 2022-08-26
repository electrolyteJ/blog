---
layout: post
title: 网络 --- Okhttp Connection的备胎之路
description: socket管理
author: 电解质
date: 2021-04-28 22:50:00
share: true
tag: 
- app-design/network
---
## *1.Summary*{:.header2-font}
整理技术笔记才发现还有一些文章草稿没有收尾，2018年写到一半的文章准备发博客却因为一些不可控制的外力导致搁置，现在重新拿出来并且整理一下。Okhttp系列 ，I‘m back.
## *2.Introduction*{:.header2-font}
前面我们在Okhttp和Volley这两个开源项目比较重试/重定向、缓存、请求池的设计 ，出门左转文件传送门[网络 --- Volley vs. OkHttp]({{site.baseurl}}/2018-04-19/network-volley-okhttp)，接下来我们只讲Okhttp怎么设计连接池。

这还得从一个call调用开始说起，当应用层调用请求，紧接而来的就是责任链的一系列调用，对于责任链模式可以看这里的[JavaChainOfResponsibility](https://github.com/electrolyteJ/DesignPatterns/blob/master/src/main/java/behavioral/JavaChainOfResponsibility.java)。简单理解就是一个请求经过一条链式时，链上的每个节点会根据情况选择性的处理，如果其中有一节点不处理了往下的节点也就不会处理了。咦？这味道是不是有点熟悉，Android View树事件的分发。我们再把话题重新拉回来，在Okhttp中称呼这条链上的节点叫做拦截器，从应用层往下分别是：RetryAndFollowUpInterceptor、BridgeInterceptor、CacheInterceptor、ConnectInterceptor、CallServerInterceptor，这一节我们要将的就是ConnectInterceptor这个拦截器了。

ConnectInterceptor的代码不多，但是其实都是被封装起来了，让我们来一层层剥开它。
```java
object ConnectInterceptor : Interceptor {

  @Throws(IOException::class)
  override fun intercept(chain: Interceptor.Chain): Response {
    val realChain = chain as RealInterceptorChain
    val request = realChain.request()
    val transmitter = realChain.transmitter()

    // We need the network to satisfy this request. Possibly for validating a conditional GET.
    val doExtensiveHealthChecks = request.method != "GET"
    val exchange = transmitter.newExchange(chain, doExtensiveHealthChecks)

    return realChain.proceed(request, transmitter, exchange)
  }
}
```
先来认识几个重要的角色

- Exchange:数据交换器
- ExchangeCodec：数据交换器的流编解码模块，用于处理http1.x还是http2.x协议
- ExchangeFinder：数据交换器的流编解码模块的finder
- Connection：连接器
- Transmitter：发射器(由数据交换器+连接器构成) 
- Route/RouteSelector：网络路由/路由选择器，网络路由持有代理对象，如果当前网络不可用可以切换Proxy提供的线路，我们经常看到视频网站的某个视频会提供很多个数据源线路
- Proxy/ProxySelector：代理/代理选择器


首先Transmitter(`OkHttp最新代码(commit-id 4ebc5f644c92ad08e41908db2ccaff4819cd0cbe)已经没有这个类了，被合并到RealCall,不过对于那些被封装的代码来说不过是换了个妈，本质没变`)是应用层和网络层的桥(这里应用层和网络层指的是Okhttp定义的，BridgeInterceptor以上为应用层，往下为网络层)，它管理者Exchange和Connection，可以认为一个call就会有一个Transmitter用于创造属于这个call调用的交互器Exchange和端与端的连接器Connection，所以上面的代码不难看出newExchange方法的意思。

Transmitter
{:.filename}
```java
  internal fun newExchange(chain: Interceptor.Chain, doExtensiveHealthChecks: Boolean): Exchange {
    synchronized(connectionPool) {
      check(!noMoreExchanges) { "released" }
      check(exchange == null) {
        "cannot make a new request because the previous response is still open: " +
            "please call response.close()"
      }
    }

    val codec = exchangeFinder!!.find(client, chain, doExtensiveHealthChecks)
    val result = Exchange(this, call, eventListener, exchangeFinder!!, codec)

    synchronized(connectionPool) {
      this.exchange = result
      this.exchangeRequestDone = false
      this.exchangeResponseDone = false
      return result
    }
  }
```

紧接着我们看到了通过finder找到了交换器的编解码模块，那么如何找到的呢？

ExchangeFinder
{:.filename}
```java
  fun find(
    ...
  ): ExchangeCodec {
    ...
    try {
      val resultConnection = findHealthyConnection(
        ...
      )
      return resultConnection.newCodec(client, chain)
    ...
  }
  ...
  @Throws(IOException::class)
  private fun findHealthyConnection(
    ...
  ): RealConnection {
    while (true) {
      val candidate = findConnection(
          connectTimeout = connectTimeout,
          readTimeout = readTimeout,
          writeTimeout = writeTimeout,
          pingIntervalMillis = pingIntervalMillis,
          connectionRetryEnabled = connectionRetryEnabled
      )

      // If this is a brand new connection, we can skip the extensive health checks.
      synchronized(connectionPool) {
        if (candidate.successCount == 0) {
          return candidate
        }
      }

      // Do a (potentially slow) check to confirm that the pooled connection is still good. If it
      // isn't, take it out of the pool and start again.
      if (!candidate.isHealthy(doExtensiveHealthChecks)) {
        candidate.noNewExchanges()
        continue
      }

      return candidate
    }
  }
```
代码也很简单，真正难点在于findConnection方法如何找有有效的备胎。

ExchangeFinder
{:.filename}
```java
 @Throws(IOException::class)
  private fun findConnection(
    ...
  ): RealConnection {
    ...
    synchronized(connectionPool) {
      if (transmitter.isCanceled) throw IOException("Canceled")
      hasStreamFailure = false // This is a fresh attempt.

      releasedConnection = transmitter.connection
      toClose = if (transmitter.connection != null && transmitter.connection!!.noNewExchanges) {
        transmitter.releaseConnectionNoEvents()
      } else {
        null
      }

      if (transmitter.connection != null) {
        // We had an already-allocated connection and it's good.
        result = transmitter.connection
        releasedConnection = null
      }

      if (result == null) {
        // Attempt to get a connection from the pool.
        if (connectionPool.transmitterAcquirePooledConnection(address, transmitter, null, false)) {
          foundPooledConnection = true
          result = transmitter.connection
        } else if (nextRouteToTry != null) {
          selectedRoute = nextRouteToTry
          nextRouteToTry = null
        } else if (retryCurrentRoute()) {
          selectedRoute = transmitter.connection!!.route()
        }
      }
    }
    ...
    if (result != null) {
      // If we found an already-allocated or pooled connection, we're done.
      return result!!
    }

    // If we need a route selection, make one. This is a blocking operation.
    var newRouteSelection = false
    if (selectedRoute == null && (routeSelection == null || !routeSelection!!.hasNext())) {
      newRouteSelection = true
      routeSelection = routeSelector.next()
    }

    var routes: List<Route>? = null
    synchronized(connectionPool) {
      if (transmitter.isCanceled) throw IOException("Canceled")

      if (newRouteSelection) {
        // Now that we have a set of IP addresses, make another attempt at getting a connection from
        // the pool. This could match due to connection coalescing.
        routes = routeSelection!!.routes
        if (connectionPool.transmitterAcquirePooledConnection(
                address, transmitter, routes, false)) {
          foundPooledConnection = true
          result = transmitter.connection
        }
      }

      if (!foundPooledConnection) {
        if (selectedRoute == null) {
          selectedRoute = routeSelection!!.next()
        }

        // Create a connection and assign it to this allocation immediately. This makes it possible
        // for an asynchronous cancel() to interrupt the handshake we're about to do.
        result = RealConnection(connectionPool, selectedRoute!!)
        connectingConnection = result
      }
    }

    // If we found a pooled connection on the 2nd time around, we're done.
    if (foundPooledConnection) {
      eventListener.connectionAcquired(call, result!!)
      return result!!
    }
    ...
  }
```
1. transmitter.connection
2. RealConnectionPool#transmitterAcquirePooledConnection
3. new RealConnection

查看可用的备胎遵循这一定的规则，不是什么阿猫阿狗都能当备胎。首先最好是能有当备胎的经验，从零开始培养一个备胎远比已经当过备胎更加耗费资源，创建一个连接是需要调用系统资源的。如果在Transmitter中找不到这个连接，再去连接池找到(RealConnectionPool#transmitterAcquirePooledConnection方法找)，毕竟身边有现成的在跑到备胎池到处找来得快，最后真不行只能自己动用一切资源培养一个备胎。

比较难的地方在于连接池的查找，第一次查找时仅仅通过请求的host和复用的连接host相同就能找复用的连接，如果不存在这样的连接，那么这时候就要切换路由，路由线路的数量来源于上层应用提供了多少代理。

RouteSelector
{:.filename}
```java
  private fun resetNextInetSocketAddress(proxy: Proxy) {
    // Clear the addresses. Necessary if getAllByName() below throws!
    val mutableInetSocketAddresses = mutableListOf<InetSocketAddress>()
    inetSocketAddresses = mutableInetSocketAddresses

    val socketHost: String
    val socketPort: Int
    if (proxy.type() == Proxy.Type.DIRECT || proxy.type() == Proxy.Type.SOCKS) {
      socketHost = address.url.host
      socketPort = address.url.port
    } else {
      val proxyAddress = proxy.address()
      require(proxyAddress is InetSocketAddress) {
        "Proxy.address() is not an InetSocketAddress: ${proxyAddress.javaClass}"
      }
      socketHost = proxyAddress.socketHost
      socketPort = proxyAddress.port
    }

    if (socketPort !in 1..65535) {
      throw SocketException("No route to $socketHost:$socketPort; port is out of range")
    }

    if (proxy.type() == Proxy.Type.SOCKS) {
      mutableInetSocketAddresses += InetSocketAddress.createUnresolved(socketHost, socketPort)
    } else {
      eventListener.dnsStart(call, socketHost)

      // Try each address for best behavior in mixed IPv4/IPv6 environments.
      val addresses = address.dns.lookup(socketHost)
      if (addresses.isEmpty()) {
        throw UnknownHostException("${address.dns} returned no addresses for $socketHost")
      }

      eventListener.dnsEnd(call, socketHost, addresses)

      for (inetAddress in addresses) {
        mutableInetSocketAddresses += InetSocketAddress(inetAddress, socketPort)
      }
    }
  }
```
当然了也不是所有的代理都能用，如果是http代理和http直连，RouteSelector就会用host通过dns查找可用的ip地址集合；如果是socks代理，RouteSelector就提供一条ip线路

找到了可用的路由，接下来就再次去连接池查找连接，由于向连接池提供了可用的路由，那么不在像第一次只提供host而找不到连接，连接池还会在通过路由这一筛选条件，不过可用路由必须和复用的连接一样是直连并且地址相同。这里还有一点对于需要主机验证的连接是不能被复用的

如果还是找不到怎么办？构造一个全新连接,构造新的连接，必然要和服务器进行三次握手有可能也要进行TLS连接。

ExchangeFinder
{:.filename}
```java
  @Throws(IOException::class)
  private fun findConnection(
    ...
  ): RealConnection {
    ...
    // Do TCP + TLS handshakes. This is a blocking operation.
    result!!.connect(
        connectTimeout,
        readTimeout,
        writeTimeout,
        pingIntervalMillis,
        connectionRetryEnabled,
        call,
        eventListener
    )
    connectionPool.routeDatabase.connected(result!!.route())

    var socket: Socket? = null
    synchronized(connectionPool) {
      connectingConnection = null
      // Last attempt at connection coalescing, which only occurs if we attempted multiple
      // concurrent connections to the same host.
      if (connectionPool.transmitterAcquirePooledConnection(address, transmitter, routes, true)) {
        // We lost the race! Close the connection we created and return the pooled connection.
        result!!.noNewExchanges = true
        socket = result!!.socket()
        result = transmitter.connection
      } else {
        connectionPool.put(result!!)
        transmitter.acquireConnectionNoEvents(result!!)
      }
    }
    socket?.closeQuietly()

    eventListener.connectionAcquired(call, result!!)
    return result!!
    ...
  }
```
到这里我们就看到了，连接之后就放入连接池，成为她人的备胎。那么对于tcp的握手过程，究竟做了什么？为什么成为备胎要经历这么多的艰辛。

RealConnection
{:.filename}
```java
  fun connect(
    connectTimeout: Int,
    readTimeout: Int,
    writeTimeout: Int,
    pingIntervalMillis: Int,
    connectionRetryEnabled: Boolean,
    call: Call,
    eventListener: EventListener
  ) {
    check(protocol == null) { "already connected" }

    var routeException: RouteException? = null
    val connectionSpecs = route.address.connectionSpecs
    val connectionSpecSelector = ConnectionSpecSelector(connectionSpecs)
    ...

    while (true) {
      try {
        if (route.requiresTunnel()) {
          connectTunnel(connectTimeout, readTimeout, writeTimeout, call, eventListener)
          if (rawSocket == null) {
            // We were unable to connect the tunnel but properly closed down our resources.
            break
          }
        } else {
          connectSocket(connectTimeout, readTimeout, call, eventListener)
        }
        establishProtocol(connectionSpecSelector, pingIntervalMillis, call, eventListener)
        eventListener.connectEnd(call, route.socketAddress, route.proxy, protocol)
        break
      } catch (e: IOException) {
        ...

        if (routeException == null) {
          routeException = RouteException(e)
        } else {
          routeException.addConnectException(e)
        }

        if (!connectionRetryEnabled || !connectionSpecSelector.connectionFailed(e)) {
          throw routeException
        }
      }
    }
    ...
    val http2Connection = this.http2Connection
    if (http2Connection != null) {
      synchronized(connectionPool) {
        allocationLimit = http2Connection.maxConcurrentStreams()
      }
    }
  }
```

前面我们说过路由的查找，路由的线路连接主要通过代理，而代理又分为直连、http、socks。如果只是使用这三种代理那么网络默认是明文传输的，如果开启隧道（http代理+tls）就要求必须加密，这里说一下隧道，开启前会先发CONNECT报文进行连接。当然了这三种代理我们也可以选择性的配置tls，取决于上层应用给的规格connectionSpecs。在开启隧道过程中，客户端和代理服务器会进行鉴权，客户端要在Proxy-Authenticate字段中加入鉴权的数据。

连接socket之后，就要看看接下来要不要tls连接了。

RealConnection
{:.filename}
```java
private fun connectTls(connectionSpecSelector: ConnectionSpecSelector) {
      val address = route.address
    val sslSocketFactory = address.sslSocketFactory
    var success = false
    var sslSocket: SSLSocket? = null
    try {
      // Create the wrapper over the connected socket.
      sslSocket = sslSocketFactory!!.createSocket(
          rawSocket, address.url.host, address.url.port, true /* autoClose */) as SSLSocket

      // Configure the socket's ciphers, TLS versions, and extensions.
      val connectionSpec = connectionSpecSelector.configureSecureSocket(sslSocket)
      if (connectionSpec.supportsTlsExtensions) {
        Platform.get().configureTlsExtensions(sslSocket, address.url.host, address.protocols)
      }

      // Force handshake. This can throw!
      sslSocket.startHandshake()
      // block for session establishment
      val sslSocketSession = sslSocket.session
      val unverifiedHandshake = sslSocketSession.handshake()

      // Verify that the socket's certificates are acceptable for the target host.
      if (!address.hostnameVerifier!!.verify(address.url.host, sslSocketSession)) {
        ...
      }

      val certificatePinner = address.certificatePinner!!

      handshake = Handshake(unverifiedHandshake.tlsVersion, unverifiedHandshake.cipherSuite,
          unverifiedHandshake.localCertificates) {
        certificatePinner.certificateChainCleaner!!.clean(unverifiedHandshake.peerCertificates,
            address.url.host)
      }

      // Check that the certificate pinner is satisfied by the certificates presented.
      certificatePinner.check(address.url.host) {
        handshake!!.peerCertificates.map { it as X509Certificate }
      }

      // Success! Save the handshake and the ALPN protocol.
      val maybeProtocol = if (connectionSpec.supportsTlsExtensions) {
        Platform.get().getSelectedProtocol(sslSocket)
      } else {
        null
      }
}
```
通过外部提供的sslSocketFactory我们构建了SSLSocket，并和服务器进行的握手，ssl握手的过程可以看这一博文，传送门[抓包原理]({{site.baseurl}}/2020-12-13/capture-message)。握手之后拿到证书，通过Okhttp提供的OkHostnameVerifier验证主机，当然你也可以自定义验证主机的逻辑。那么之后就完成连接。这里还要提一嘴，Okhttp项目中还提供了`okhttp-tls`，帮助我们去实现客户端服务端证书的管理。到这里我们就知道了培养备胎多么浪费资源了吧，先socket握手然后sslsocket握手，握手之后验证证书，所以能从复用就复用千万不要自己搞。

在进行连接的过程中会出现各种不能恢复的异常
- 一些致命的异常，ProtocolException  SSLHandshakeException/CertificateException SSLPeerUnverifiedException
- 客户端配置要求禁止重试
- 没有更多可用的路由
- request的body没有数据了：如果是本地路由问题，request还没有被发送body还有数据，如果是服务器问题，那么request已经被发送并且body没有了数据

与上面的不可恢复的异常相对的是可以恢复的异常SocketTimeoutException，还有本地路由出现了问题，那么对于Okhttp来说会在RetryAndFollowUpInterceptor重新尝试去连接服务。 

这里我们还需要扩展一个东西。http1.x和http2的发送请求和接受响应的不同，http1.x使用了管道化发送，一个tcp连接可以多个请求可以同时发送，但是服务器却按照顺序响应；http2由于采用了stream模式，一个tcp连接上面有多个stream，可以同时多个请求的同时发送响应。上面的连接复用对于http1.x来说我们很好理解，对于http2在代码的设计上OkHttp有一点不太一样。被复用的RealConnection对象其实是持有Http2Connection对象，当然了前提是使用http2协议，复用了RealConnection对象也就相当于复用了Http2Connection对象，Http2Connection对象存储这一堆的stream，每个stream处理一对请求响应。


你以为成为备胎就完事了？放在池子里的备胎也会只是被供挑选的对象也存在竞争，池子也遵循着末尾淘汰机制。那么这个末位淘汰机制是如何设置的？接下来看看。

```java
  private val cleanupTask = object : Task("$okHttpName ConnectionPool") {
    override fun runOnce() = cleanup(System.nanoTime())
  }
```
每次有个新连接被put到连接池中，都会触发clean任务。它会清理那些超过保活时间5min的连接或者超过6以上个处于空闲的连接，简单说就是那些到35岁的人或者团队超过6以上长时间不干活的人。你以为这样就clean up只会发生一次，太年轻了。如果clean完一个连接，紧接着马不停蹄没有delay的又开始下一次清理。如果发现这次清理的没有超过35岁或者不干活的人低于5以下，那么就会采取两种判断，如果0< 不干活人数 <=5，那么就会用保活时间减去取空闲时间最长人空闲的时间(keepAliveDurationNs - longestIdleDurationNs),其差作为下次clean任务的delay，等下次clean时，如果还不干活，就clean这个人。还有一种是既然35岁还没有到，比如34岁，就等一年在把他clean掉。那么有没有一种办法终止这种末位淘汰机制，还真有，公司倒闭了没有人了，clean循环停止。

### *3.Reference*{:.header2-font}
[Java使用SSLSocket通信](https://my.oschina.net/itblog/blog/651608)