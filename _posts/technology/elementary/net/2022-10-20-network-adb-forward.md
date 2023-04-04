---
layout: post
title: 网络 | adb端口转发
description: 客户端的react native devMenu与web前端的chrome devtools背后的思考
author: 电解质
date: 2022-10-20 22:50:00
share: false
comments: false
tag: 
- network
- android
---
```
networking:
 connect HOST[:PORT]      connect to a device via TCP/IP [default port=5555]
 disconnect [HOST[:PORT]]
     disconnect from given TCP/IP device [default port=5555], or all
 forward --list           list all forward socket connections
 forward [--no-rebind] LOCAL REMOTE
     forward socket connection using:
       tcp:<port> (<local> may be "tcp:0" to pick any open port)
       localabstract:<unix domain socket name>
       localreserved:<unix domain socket name>
       localfilesystem:<unix domain socket name>
       dev:<character device name>
       jdwp:<process pid> (remote only)
 forward --remove LOCAL   remove specific forward socket connection
 forward --remove-all     remove all forward socket connections
 ppp TTY [PARAMETER...]   run PPP over USB
 reverse --list           list all reverse socket connections from device
 reverse [--no-rebind] REMOTE LOCAL
     reverse socket connection using:
       tcp:<port> (<remote> may be "tcp:0" to pick any open port)
       localabstract:<unix domain socket name>
       localreserved:<unix domain socket name>
       localfilesystem:<unix domain socket name>
 reverse --remove REMOTE  remove specific reverse socket connection
 reverse --remove-all     remove all reverse socket connections from device
```
在adb命令中，LOCAL表示电脑端，REMOTE表示手机端。adb forward LOCAL REMOTE，表示将电脑的某个端口数据转发手机端的某个端口，通常来说客户端要创建socket server(LocalServerSocket/ServerSocket等)；adb reverse REMOTE LOCAL,表示反向将手机的端口数据转发到电脑的端口，通常来说客户端要创建socket client(LocalSocket/WebSocketListener等)。为什么从电脑到手机是正向转发，而手机到电脑是反向转发？ 因为adb server在手机端，而adb client在电脑端。这里还有一些重要的信息，`tcp:<port>` 通常表示网络层socket，Socket/ServerSocket/WebSocket等基于socket定制的网络协议；localabstract:<unix domain socket name>表示Android系统内置的本地socket，LocalSocket/LocalServerSocket，不能用于网络传输，支持在usb线传输。

## adb forward
在chrome浏览器的搜索框输入`chrome://inspect`会跳转到inspector devices，页面中有两个进程。当点击inspect按钮，chrome会发送数据到与之建立连接的android app中stetho(stetho支持android app与chrome通信),其底层逻辑主要是通过`adb forward`电脑与手机端口，stetho创建的`LocalServerSocket`等待chrome发送连接请求。devtools服务的[接口文档](https://chromedevtools.github.io/devtools-protocol/v8/Console/)

![inspector discovery][1]

## adb reverse
理解了数据从电脑流向手机的场景，那么数据从手机流向电脑的场景有什么？ `推流场景`或者`信号指令`等场景。在手机实施录制数据流，然后推给电脑端的server，[river](https://github.com/electrolyteJ/river)就是这样一个场景的实践项目。

react native的devMenu功能实现原理也是基于此，手机端的WebSocket发送连接请求，react native cli创建server监听，成功连接之后。点击devMenu中某个功能，就会触发其触发指令，react native cli server负责消费处理这些指令。

![devMenu][2]



[1]:{{site.baseurl}}/asset/network/inspector-discovery.png
[2]:{{site.baseurl}}/asset/cross-platform/devMenu.png