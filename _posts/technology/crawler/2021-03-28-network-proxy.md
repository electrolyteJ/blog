---
layout: post
title: 网络代理
description: 
author: 电解质
date: 2021-03-27 22:50:00
share: true
comments: false
tag: 
- inverse-engineering
published : true
---
## *Introduction*{:.header2-font}
网络代理按照层级划分有
- http代理(tunnel代理)
- tcp代理(socks代理)
- ip代理(vpn代理)

http代理是利用tunnel来完成代理，代理开始时会发送一条请求报文，起首行为`CONNECT example.com:443 HTTP/1.1`来告知代理服务器目标服务器地址，紧接着代理服务器会连接目标服务器，成功之后会给客户端返回`HTTP/1.1 200 Connection Established`，这样握手成功之后就可以进行数据传输了。我们常见的抓包工具Charles、Fiddler、MITMProxy 都是利用隧道代理来完成抓包，还有服务器用于负载均衡的Nginx，对于手机中的wifi网络代理也是采用这种代理方式。

tcp代理有socks v4 v5，socks4支持tcp而socks5不仅支持tcp还支持udp,使用也能简单`Socket s = new Socket(new Proxy(Proxy.Type.SOCKS, new InetSocketAddress("socks.mydom.com", 1080)))`。socks可以实现防火墙穿透从内网环境直达外网环境，对于网络穿透的有frp。socks代理是比tunnel代理更低的一种网络代理方式，在osi模型中处于会话层。

那么是否有比起更低的网络代理？答案是有的，ip代理。通过在本地创建一块虚拟网卡tun，然后监听这张虚拟网卡。vpn就是起具体的实现方式，通过抓取tun网卡的包发送给vpns，vpns接收到并且解析包之后找出目标服务器地址并且连接和交换数据。

tunnel代理、socks代理、vpn代理这三种代理方式在连接目标服务器的时候都要进行安全认证，以防止被恶意攻击。在破解app并且获取其中的网络密钥之后，通过vpn代理抓取到网络包然后使用密钥对包进行加解密就能篡改报文里面的某些重要字段，从而欺骗服务端和客户端达到某种目的。
对于vpn代理中，一个包的结构包含多种协议，ip/udp/tcp/http等，所以在编解码时我们需要对包有清楚的认知。有兴趣的小伙伴可以看看我提供的这个开源库，里面提供了udp包、tcp包、ip包的结构[JamesfChen/oknem](https://github.com/JamesfChen/oknem/tree/main/androidvpn/app/src/main/java/com/jamesfchen/vpn/protocol)，只需轻轻点击即可获得成倍的抄作业快乐。

还有提供了packet_builder用来构建tcp握手与挥手时的包
{:.filename}
```kotlin
......
//fun createSynPacketOnHandshake():Packet{
//}
fun createSynAndAckPacketOnHandshake(
    sour: InetSocketAddress, dest: InetSocketAddress, seq: Long, ack: Long, ipId: Int
): Packet {
    return createTCPPacket(
        sour, dest, seq, ack, ControlBit(ControlBit.SYN or ControlBit.ACK), ipId
    )
}

fun createAckPacketOnHandshake(
    sour: InetSocketAddress, dest: InetSocketAddress, seq: Long, ack: Long, ipId: Int
): Packet {
    return createTCPPacket(
        sour, dest,
        seq, ack,
        ControlBit(ControlBit.ACK),
        ipId
    )
}
.......
```
### *Reference*{:.header2-font}
[nondanee/UnblockNeteaseMusic](https://github.com/nondanee/UnblockNeteaseMusic)

[ndroi/easy163](https://github.com/ndroi/easy163)

[trojan-gfw/igniter](https://github.com/trojan-gfw/igniter)

[fatedier/frp](https://github.com/fatedier/frp)