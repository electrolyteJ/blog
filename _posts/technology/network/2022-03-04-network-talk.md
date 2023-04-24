---
layout: post
title: 网络漫谈
description: 
tag: 
- network
- android
---
* TOC
{:toc}

现如今互联网模式下的即时通讯应用大多传承了旧时代手机的打电话功能、联系人信息管理功能、短信聊骚功能。由于博主曾经从事过ROM开发，隶属于通信组，主要解决的是手机通信模块相关的问题，但自认为还是一名技术小白，因为该模块里面涉及的东西太多了，知识点从Kernel到Application层。不过对于整体还有有一个比较清晰的认识，所以就来聊聊互联网模式下的IM和传统模式下的IM。

# 通信（communication） vs.  通讯（message）

为了更好的理解下面提到的内容，博主这里不客观的理解两者差异。在网络上常常将两者混淆，这个很大原因是由于英文被转译成中文，变了味道。所以追本溯源才能理解其中奥义。通信的英文为communication，涉及从物理层到应用层的通信，而通讯的英文我认为是message来的更叫贴切，为什么呢？常常提到的一个词叫做即时通讯（instant message，short for IM），它是采用应用层的报文（message）进行沟通的。所以通信的描述范围相对于通讯来得广泛，对于像设备厂商或者运营商这种生产实体物的公司来说，通信对他们来说来得比较贴切，而对于生产虚拟物的互联网公司来说，比如微信、qq等拥有即时通讯功能的软件来说，通讯对他们来说比较吻合。以上纯属于个人观点，如果有不对欢迎纠错。

# 网络协议族
首先来说说网络这一块，由于移动端IP电话、IP网络的兴起，互联网模式下的IM，主要采用的是分组交换（Packet switching，short for PS）的数据通信，而传统模式下的IM主要采用的是电路交换（Circuit Switching，short for CS）。在早年CS通信的稳定性决定了其实用性，而随着基于PS的音视频技术越来越成熟，基于PS的音视频逐渐被普及。面对这样一种冲击，4G网络中的VoLTE应运而生，其特点就是当PS通话不能使用时，自动fallback到2G通话。

- PS协议族
- CS协议族
- VoLTE协议族

然后具体细分一下，消息收发和实时音视频通讯。

## 消息收发

- 在互联网模式下的IM，消息传递可以通过WebSocket，由于Http不能自动实现服务端自动推送消息到客户端，而WebSocket正好解决了这个问题，不过除了使用WebSocket推送消息，还可以让客户端轮询发送Http请求，来实现类谁于WebSocket的推送功能，但是这样就比较浪费带宽了。

- 在传统模式下的IM，消息传递主要在短信应用里面。短信(SMS)是使用GSM的信令通道，而彩信（MMS）是基于WAP（Wireless Application Protocol）协议族，走数据通道，其传输能力大大超过短信。因为短信只能发送文字，所以彩信能够发送图片、音视频，在条件允许下还能支持流媒体。彩信采用Http的流模式，传输的数据是经过 encode的二进制文件，我们叫做PDU。[彩信的协议流程](http://yinger-fei.iteye.com/blog/1520553)。为什么要这样处理呢？因为SMS通过信令通道传输数据的，其格式采用7/8/16位 encode的二进制文件，应用层数据格式统一，便于解析分装，只是底层传输通道不同。

需要实现的基本功能：发送/接收、通知/已阅读

由于OkHttp支持配置全双工的WebSocket，所以互联网模式下的IM，就可以不用像传统模式下的IM实现PDU，然后短信让modem来推送，彩信让服务中心（MMSC）来推送。运营商具体如何实现推送我们不得而知，不过却有几种方案供大家选择,都是基于半双工的Http，[参考文章](http://www.52im.net/thread-331-1-1.html)。当然了如果你想加快传输速度节省带宽，可以让WebSocket不传输文本该传输PDU。

## 实时音视频通讯

- 在互联网模式下的IM，实时音视频通讯可以通过WebRTC或者HLS/DASH。
- 在传统模式下的IM，实时音视频通讯主要在Phone应用里面，早期没有视频通话，只有语音通话，采用的是gms/cdms;而后使用了VoLTE（VoLTE引入了IMS），集成了PS，才有可能实现视频通话。

### 采用p2p技术传输,协议有：
1. STUN（Session Traversal Utilities for NAT）：它允许位于NAT（或多重NAT）后的客户端找出自己的公网地址，查出自己位于哪种类型的NAT之后以及NAT为某一个本地端口所绑定的Internet端端口。这些信息被用来在两个同时处于NAT路由器之后的主机之间创建UDP通信。
2. TURN(Traversal Using Relay NAT):是一种数据传输协议,允许在TCP或UDP的连接上跨越NAT或防火墙。
3. ICE(Interactive Connectivity Establishment):exchange network information.

### 采用会话层协议有：

signaling可以使用 SIP和 XMPP；双工通道也要自己选择

sigaling的作用
- Session control messages: to initialize or close communication and report errors.
- Network configuration: to the outside world, what's my computer's IP address and port?
- Media capabilities: what codecs and resolutions can be handled by my browser and the browser it wants to communicate with?

网络配置通过ICE。媒体信息通过sdp。

网络存在问题
- packet loss concealment
- echo cancellation
- bandwidth adaptivity
- dynamic jitter buffering
- automatic gain control
- noise reduction and suppression
- image 'cleaning'.

与Modem相比的话，AT指令是signaling，而ppp是数据传输协议，只不过他们是在数据链路层，相对WebRTC更加底层，这一层还有很重要的东西叫做串口。格式为：8位数据位、1位停止位、无奇偶校验位、硬件流控制（CTS/RTS）。比如PC机用串口接入拨号MODEM时，PC机是DTE，拨号MODEM是DCE。AT只用于DTE来控制DCE。PPP是用于数据通讯，是DTE与远程的接入服务器(Access Server)进行通讯的协议。

### AV
A:iSAC codec
V:VP8 codec

# VoLTE协议族
![]({{site.baseurl}}/asset/network/VoLTE_protocol_stack.jpg)

# 总结
消息方面：可以使用WebSocket或者Http的流模式。为了加快传输速度和节省带宽等可以将文本传输换成PDU传输。

音视频：使用WebRTC来的方便，信令协议需要自己选择，传输协议和音视频编解码器已经提供，服务端需要配置STUN、信令等服务器。也可以用一些像HLS基于Http的解决方案。

# 参考资料

[Phone模块分析文章](https://blog.csdn.net/yihongyuelan/article/details/19930861)

[短信模块分析文章1](https://blog.csdn.net/hitlion2008/article/category/945580)

[短信模块分析文章2](https://blog.csdn.net/t12x3456/article/category/1648993)