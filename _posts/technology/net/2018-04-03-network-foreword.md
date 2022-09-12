---
layout: post
title: 网络|前言
description: 
author: 电解质
date: 2018-04-03 22:50:00
share: true
comments: true
tag: 
- elementary/network
published : true
---
<!-- * TOC
{:toc} -->
## *1.Summary*{:.header2-font}
&emsp;&emsp;互联网发展至今网络通讯是其最为重要的部分，网络协议层出不穷，但是影响最为深远的还得是HTTP。由HTTP1.0到HTTP2.0随着社会的需求不停地迭代更新，排队发送到管道发送，半双工到全双工。
对于Android客户端来说，目前最为常用的HTTP实现方案是OkHttp,而早起Google Android团队也退出了自己的网络库Volley，但是其存在致命缺陷，由于在网络回来之后解析过程会将response保存到内存中，虽然能快速响应cache但是容易把内存搞爆了。所以在Android N之后在framework层采用了OkHttp的核心代码来作为网络请求，这相当于肯定了OkHttp在网络库的地位。然而Google Android团队也没有就此不作为，从隔壁的Chromium团队把网络库Cronet也移植到了Java平台。有别于用Java实现的OkHttp，Cronet是用Cpp实现的，所以天生具备跨平台，支持iOS、Android、Frontend。对于熟悉Java/Kotlin开发的Android程序员，阅读Volley和OkHttp更是当务之急。因为Volley是一个相对于OKHttp比较简单的网络库，其设计比较适合入门网络库阅读，OkHttp在HTTP实现来得更加完整，代码也更加优雅，阅读体验感人。
&emsp;&emsp;先来两张图感受一下它们的设计。
Volley
![network]({{site.baseurl}}/asset/network/Volley.jpg)

OkHttp
![network]({{site.baseurl}}/asset/network/OkHttp.jpg)

&emsp;&emsp;了解了Volley和OkHttp，也得了解其api style和序列化

SOP:HTTP+XML(过去)
REST:HTTP+JSON(现在)
gRPC+protobuf(未来) ​​​​

## *2.Reference*{:.header2-font}

[HTTP - Hypertext Transfer Protocol](https://www.w3.org/Protocols/)
[HTTP 协议入门](https://www.ruanyifeng.com/blog/2016/08/http.html)
[使用 Cronet 执行网络操作](https://developer.android.com/guide/topics/connectivity/cronet)