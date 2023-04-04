---
layout: post
title: 网络 | 网络代理
description: http代理、tcp代理、ip代理
author: 电解质
date: 2022-10-15 22:50:00
share: false
comments: false
tag: 
- network
- inverse-engineering
- android
---
* TOC
{:toc}

网络代理按照层级划分有
- http代理(tunnel代理)
- tcp代理(socks代理)
- ip代理(vpn代理)

http代理是利用tunnel来完成代理，代理开始时会发送一条请求报文，起首行为`CONNECT example.com:443 HTTP/1.1`来告知代理服务器目标服务器地址，紧接着代理服务器会连接目标服务器，成功之后会给客户端返回`HTTP/1.1 200 Connection Established`，这样握手成功之后就可以进行数据传输了。我们常见的抓包工具Charles、Fiddler、MITMProxy 都是利用隧道代理来完成抓包，还有服务器用于负载均衡的Nginx。

tcp代理有socks v4 v5，socks4支持tcp而socks5不仅支持tcp还支持udp,使用也能简单`Socket s = new Socket(new Proxy(Proxy.Type.SOCKS, new InetSocketAddress("socks.mydom.com", 1080)))`。socks可以实现防火墙穿透从内网环境直达外网环境，对于网络穿透的有frp。socks代理是比tunnel代理更低的一种网络代理方式，在osi模型中处于会话层。

那么是否有比起更低的网络代理？答案是有的，ip代理。通过在本地创建一块虚拟网卡tun，然后监听这张虚拟网卡。vpn是ip代理的具体实现，通过抓取tun网卡的包发送给vpns，vpns接收到并且解析包之后找出目标服务器地址并且连接和交换数据。

tunnel代理、socks代理、vpn代理这三种代理方式在连接目标服务器的时候都要进行安全认证，以防止被恶意攻击。在破解app并且获取其中的网络密钥之后，通过vpn代理抓取到网络包然后使用密钥对包进行加解密就能篡改报文里面的某些重要字段，从而欺骗服务端和客户端达到某种目的。
对于vpn代理中，一个包的结构包含多种协议，ip/udp/tcp/http等，所以在编解码时我们需要对包有清楚的认知。有兴趣的小伙伴可以看看我提供的这个开源库，里面提供了udp包、tcp包、ip包的结构[oknem](https://github.com/electrolyteJ/oknem/tree/main/androidvpn/app/src/main/java/com/jamesfchen/vpn/protocol)，只需轻轻点击即可获得成倍的抄作业快乐。

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
## *端口配置*{:.header2-font}
&emsp;&emsp;随便配置一个不和哪些知名端口(8080 、443)冲突的端口就行
![arch][1]{: .center-image }_`fiddler`_
![arch][2]{: .center-image }_`charles`_
## *导入CA证书*{:.header2-font}
&emsp;&emsp;在Android系统的设置应用中采用凭证管理器管理系统CA证书和用户CA证书。它们分别存放于两个地方，系统证书位置：/system/etc/security/cacerts，用户证书位置：/data/misc/keystore/user_0，所以只要将证书放到这两个位置就能被信任使用，但是考虑到安全问题，在Android7.0之前(不包括7.0)安装的用户CA证书是可以被信任使用，Android7.0之后(包括7.0)安装的用户CA证书将不能被信任使用，需要使用root机器升级为系统CA证书。Android7.0之后是否使用用户CA证书将于App开发者自己配置决定，如果不引用外部CA证书也可以引用app内部CA证书，其存放raw或者asset。所以要么修改app的配置要么升级证书为系统证书。

### 修改app的配置
Add a file res/xml/network_security_config.xml to your app:
```xml
<network-security-config> 
  <debug-overrides> 
    <trust-anchors> 
      <!-- Trust user added CAs while debuggable only -->
      <certificates src="user" /> 
    </trust-anchors> 
  </debug-overrides> 
</network-security-config>
```
Then add a reference to this file in your app's manifest, as follows:
```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest ... >
    <application android:networkSecurityConfig="@xml/network_security_config" ... >
        ...
    </application>
</manifest>
```
### 升级为系统CA证书步骤
`openssl x509 -inform PEM -subject_hash_old -in cacert.pem`
通过openssl会在第一行生成一串hash值,87bc3517，然后将cacert.pem文件重新命名为87bc3517.0
`adb push 87bc3517.0 /data/local/tmp/`
记住千万不要push到sdcard，不然用户组就会是sdcard_rw,push到/data/local/tmp/，用户组为shell，使用shell组CA证书才能在/system/etc/security/cacerts目录有效
```
adb shell
su
mount -o rw,remount /system
cp -f /data/local/tmp/87bc3517.0 /system/etc/security/cacerts
```
![arch][3]{: .center-image }_`fiddler`_
![arch][4]{: .center-image }_`charles`_
## *关于CA证书*{:.header2-font}
&emsp;&emsp;CA是Certificate Authorities(证书机构)的简称，CA证书就是有官方的、公认的机构提供的证书。主流的CA机构有Comodo、Symantec(DigiCert子公司)、GeoTrust(DigiCert子公司)、DigiCert、Thawte、GlobalSign、RapidSSL。CA证书的格式有很多种,可以看这个文章[主流数字证书都有哪些格式？](https://www.alibabacloud.com/help/zh/doc-detail/42214.htm)。由于Android系统的framework由java语言编写，所以其App的签名使用的是java keystore。
```
x509公钥证书规范
PKCS#7 是消息语法 （常用于数字签名与加密）
PKCS#12 个人消息交换与打包语法 （如.PFX .P12）打包成带公钥与私钥

jarsign工具签名时使用的是keystore文件
signapk工具签名时使用的是pk8,x509.pem文件

```

## *抓包原理*{:.header2-font}
&emsp;&emsp;抓包软件通过这样一种模式来实现抓包的:客户端 <-->中间人<--->服务端
![arch][5]{: .center-image }_`ssl_tsl单向认证`_
&emsp;&emsp;单向认证中是对于服务端的认证，所以为了通过认证服务端会下发一份CA证书给客户端校验，CA证书中包含了服务端的公钥pub_key等其他信息。通过了校验之后，客户端就会将自己的密钥premaster secert用pub_key加密发给服务端。服务端用private_key解密，然后双方用密钥key(由client random+server random+premaster secret共同生成)进行通过。期间服务端使用了非对称加密pub_key、private_key，客户端提供的密钥key是对称加密，解密CA证书使用了操作系统或者浏览器提供的CA证书公钥,CA证书密钥也是非对称，服务器需要通过CA机构(CA秘钥)获取加密之后的证书

&emsp;&emsp;双向认证是对于服务端和客户端的认证，为了验证客户端，在客户端校验完服务端的证书之后，客户端也要发送一份自己的证书给服务端校验。当服务端校验通过同时告知客户端加密方案，客户端就会发送密钥premaster secert给服务端，然后通信

&emsp;&emsp;Fiddler/Charles使用了Http代理进行抓包,Wireshark/tcpdump使用了网卡抓包，所以运行Wireshark的机器要要有一张无线网卡(360无线网卡)，用来给手机当做热点，这样才能抓到手机上面的包。

## *可扩展的抓包软件*{:.header2-font}
还有更加“银杏”的抓包软件MITMProxy 、 HttpCanary 都是支持编写plugin来扩展功能

## *参考资料*{:.header2-font}
[nondanee/UnblockNeteaseMusic](https://github.com/nondanee/UnblockNeteaseMusic)

[ndroi/easy163](https://github.com/ndroi/easy163)

[trojan-gfw/igniter](https://github.com/trojan-gfw/igniter)

[fatedier/frp](https://github.com/fatedier/frp)

[1]:{{site.baseurl}}/asset/crawler/fiddler1.png
[2]:{{site.baseurl}}/asset/crawler/charles1.png
[3]:{{site.baseurl}}/asset/crawler/fiddler2.png
[4]:{{site.baseurl}}/asset/crawler/charles2.png
[5]:{{site.baseurl}}/asset/crawler/ssl_tsl单向认证.png