---
layout: post
title: Framework层的服务 | 前言
description:
author: 电解质
date: 2018-03-06
share: true
comments: true
tag:
  - android
---

<!-- * TOC
{:toc} -->

## _1.Summary_{:.header2-font}

&emsp;&emsp;开头说一下市场上关于这种文章已经有很多了，为什么要写这个系列的文章。这要说道我刚毕业时，主要从事 Android 手机 ROM 定制的工作，是一名 Android ROM 开发者,相对于 App 开发者对于 Framework 层的了解也会多一点，但是如今成为了一个 App 开发者。而站在 App 开发者的角度去思考，App 开发者需要知道 Framework 层的哪些知识呢 ？网上的文章要么太深入（像老罗，gityuan、邓凡平这样的 ROM 开发者），要么太片面（都是从某一个 API 切入），所以我的经历加上我的思考产生了这个系列的文章，此原因之一；其二，看了许多 Framework 层源码而没有进行总结就会像流水一样，转瞬即逝。基于这两点这个系列文章主要是引导开发者思考 Framework 层的 AMS、PKMS、WMS 的设计，唯有把握了全局再去阅读具体的实现，才能体会到 Android 团队当初在 code Framework 层代码时的想法，才能提高自身的技术水平和眼界。所以啊，对于一个 Android 高级工程师来说，是需要将自己的眼界拉到全局，用一种架构的心态去思考，而不是只专注埋头 code 某块功能的代码。

## _2.Introduction_{:.header2-font}

&emsp;&emsp;我们都知道 kernel 的内核空间运行之后会启动用户空间的 init 进程，进程 id 为 1，也就是天字一号的地位。之后 init 进程会 fork 出 zygote 进程(应用程序名/system/bin/app_process,源码文件 frameworks/base/cmds/app_process/app_main.cpp)用于孵化上层应用和服务，比如 system_server 进程。而 system_server 进程，初始化过程中会附带启动 ActivityManagerService(AMS)、PackageManagerService(PKMS)、WindowManagerService(WMS)等系统服务，并且在主线程开启一个 Looper，接收其他线程的消息，从而实现线程通讯。

重要分包

```
frameworks/base/services/java/com/android/server/SystemServer.java

frameworks/base/services/core/java/com/android/server/am/ActivityManagerService.java

frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java

frameworks/base/services/core/java/com/android/server/wm/WindowManagerService.java
```

&emsp;&emsp;看完上面的分包后你应该能猜到一些规律了吧。

- am 目录：AMS 相关的目录，还包括 ActivityStackSupervisor（ASS）、ActivityStack（AS）；
- pm 目录：PKMS 相关的目录，还包括 PackageUsage；
- wm 目录：WMS 相关的目录，还包括 Session、WindowState、WindowToken。

所以我们接下来就要围绕着 AMS、PKMS、WMS 这三个类来讲故事了。这里在插句话，当你学习完这三个 service 之后，类比其他的 service(比如 InputManagerService、PowerManagerService)也就能信手拈来，因为 Framework 层的 service 设计都差不多。先来张图大致熟悉一下整个 Framework 层的消息响应。

![]({{site.asseturl}}/android-framework/android-framework-architecture.png){: .center-image }
