---
layout: post
title: Android | Android并行
description: Android进程的IPC 与 Android多进程管理者AMS
tag:
- android
- process-thread
---
* TOC
{:toc}

由于jdk没有像线程池这样的东西，所以管理多进程的任务就交由Android操作系统实现了，AMS就扮演了这样一个角色，管理者进程的排序回收复用。跟线程的同步、通信、并发相比进程也存在通信与并行，由于进程是操作系统调度的最小单位而且相互隔离，所以不存在数据同步问题，那么接下来我们就讲讲进程通信与多进程。

# 进程通信(IPC)

Android的ipc有这么几种
- socket系列(Socket、LocalSocket等)
- binder系列(AIDL、Messenger、Binder、ContentProvider)
- 共享内存
- 管道
- 消息队列
- 信号量
- 信号

# 多进程

在Android中通过配置manifest实现多进程，进程的配置针对四大组件，四大组件启动时就会在所在声明的进程中运行。

```xml
//私有进程
android:process=":xxx"

android:process=".xxx"
```
