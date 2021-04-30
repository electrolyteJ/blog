---
layout: post
title: Fiddler vs. Charles vs. Wireshark
description: 各个抓包工具使用
date: 2020-12-13 22:50:00
share: false
comments: false
tag:
- inverse-engineering
---
* TOC
{:toc}
## *1.Summary*{:.header2-font}
//todo
## *3.Introduction*{:.header2-font}
### *端口配置*{:.header3-font}
&emsp;&emsp;随便配置一个不和哪些知名端口(8080 、443)冲突的端口就行
![arch]({{site.baseurl}}/asset/crawler/fiddler1.png){: .center-image }_`fiddler`_
![arch]({{site.baseurl}}/asset/crawler/charles1.png){: .center-image }_`charles`_
### *导入CA证书*{:.header3-font}
&emsp;&emsp;在Android系统的设置应用中采用凭证管理器管理系统CA证书和用户CA证书。它们分别存放于两个地方，系统证书位置：/system/etc/security/cacerts，用户证书位置：/data/misc/keystore/user_0，所以只要将证书放到这两个位置就能被信任使用，但是考虑到安全问题，在Android7.0之前(不包括7.0)安装的用户CA证书是可以被信任使用，Android7.0之后(包括7.0)安装的用户CA证书将不能被信任使用，需要使用root机器升级为系统CA证书。Android7.0之后是否使用用户CA证书将于App开发者自己配置决定，如果不引用外部CA证书也可以引用app内部CA证书，其存放raw或者asset。所以要么修改app的配置要么升级证书为系统证书。

#### 修改app的配置
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
#### 升级为系统CA证书步骤
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
![arch]({{site.baseurl}}/asset/crawler/fiddler2.png){: .center-image }_`fiddler`_
![arch]({{site.baseurl}}/asset/crawler/charles2.png){: .center-image }_`charles`_
### *关于CA证书*{:.header3-font}
&emsp;&emsp;CA是Certificate Authorities(证书机构)的简称，CA证书就是有官方的、公认的机构提供的证书。主流的CA机构有Comodo、Symantec(DigiCert子公司)、GeoTrust(DigiCert子公司)、DigiCert、Thawte、GlobalSign、RapidSSL。CA证书的格式有很多种,可以看这个文章[主流数字证书都有哪些格式？](https://www.alibabacloud.com/help/zh/doc-detail/42214.htm)。由于Android系统的framework由java语言编写，所以其App的签名使用的是java keystore。
```
x509公钥证书规范
PKCS#7 是消息语法 （常用于数字签名与加密）
PKCS#12 个人消息交换与打包语法 （如.PFX .P12）打包成带公钥与私钥

jarsign工具签名时使用的是keystore文件
signapk工具签名时使用的是pk8,x509.pem文件

```

### *抓包原理*{:.header3-font}
&emsp;&emsp;抓包软件通过这样一种模式来实现抓包的:客户端 <-->中间人<--->服务端
![arch]({{site.baseurl}}/asset/crawler/ssl_tsl单向认证.png){: .center-image }_`ssl_tsl单向认证`_
&emsp;&emsp;单向认证中是对于服务端的认证，所以为了通过认证服务端会下发一份CA证书给客户端校验，CA证书中包含了服务端的公钥pub_key等其他信息。通过了校验之后，客户端就会将自己的密钥premaster secert用pub_key加密发给服务端。服务端用private_key解密，然后双方用密钥key(由client random+server random+premaster secret共同生成)进行通过。期间服务端使用了非对称加密pub_key、private_key，客户端提供的密钥key是对称加密，解密CA证书使用了操作系统或者浏览器提供的CA证书公钥,CA证书密钥也是非对称，服务器需要通过CA机构(CA秘钥)获取加密之后的证书

&emsp;&emsp;双向认证是对于服务端和客户端的认证，为了验证客户端，在客户端校验完服务端的证书之后，客户端也要发送一份自己的证书给服务端校验。当服务端校验通过同时告知客户端加密方案，客户端就会发送密钥premaster secert给服务端，然后通信

&emsp;&emsp;Fiddler/Charles使用了Http代理进行抓包,Wireshark/tcpdump使用了网卡抓包，所以运行Wireshark的机器要要有一张无线网卡(360无线网卡)，用来给手机当做热点，这样才能抓到手机上面的包。

### *可扩展的抓包软件*{:.header3-font}
还有更加“银杏”的抓包软件MITMProxy 、 HttpCanary 都是支持编写plugin来扩展功能
