---
layout: post
title: Kotlin并发
description:  kotlin coroutines 
tag:
- vm-language
- process-thread
---
* TOC
{:toc}

# 什么是异步？什么是并发？什么是并行？

1. 并行(parallax)是对于进程来说的，多个进程在同一时间运行，期间可能会有资源的相互交换。多进程的模式常见于框架，比如Android，Framework层运行着一个叫做systemserver的进程，其拥有这AMS PMS这样的线程，在App层运行着各个App进程，这些进程通过Binder进程IPC通讯（rpc）。多进程能让各个App像沙盒一样安全，并且单独运行不受其他进程影响。
2. 并发(concurrence)是对于线程来说的，也是其Java语言的特点。但是并发只是看似在同一时间运行，其利用的是cpu的切片。线程中的资源可以共享，不同于进程是隔离的。所以对于系统来说，线程带来的开销可以比进程小。在systemserver进程中AMS PMS都是线程,它们在Binder线程池中。
3. 异步(asynchronization)是线程中的回调,由于JavaScript语言的特性，其运行在单线程中，这样过就会出现问题，在其之中不能执行过于耗时的任务这样带来的就是UI卡顿,比如发送100个不相互依赖的请求，在单线程中这100个请求会按照顺序执行，可想而知如果第50个一直在等待，那么后面的也会一直在等待，后50请求对应的UI就会展示很慢给用户一种错觉，页面卡顿，而这一点像及了Java的单进程。面对这样的问题，异步突然杀出。在Android系统中，通过Handler Looper MessageQueue这三个铁三角实现了异步调度，本质上是利用了事件驱动，通过线程池并发执行耗时的任务，当其中的任务完成就会通过Handler通知UI线程更新。kotlin在语言层面实现了异步，并命名为协程。

> 进程是系统进行资源分配和调度的基本单位。
> 并发：说的是多个线程同时运行。并发过程中可能使用同一块内存，所以并发要考虑同步，即内存io的一致性。
> 异步：说的是调用者所在线程不会被调用的函数block，实现non block的方式可以使进程或者线程池。

| platform  |  Java |   Kotlin| Android
|---|---|---|---|
异步|   java nio 、okio、Rxjava(Scheduler)  | coroutines、kotlin flow   |  AsyncTask(Loop Handler)
并发|   Executor| /| /
并行| /| /| Binder


# 为什么选择kotlin
- 提高生产力，代码的简洁性
- 空安全
- 高阶函数编程

# 协程
- 基于线程池api
- 使用阻塞的方法写出非阻塞式的代码，解决并发中的地狱回调，关键字suspend

在Android中协程主要解决两个问题，处理耗时任务和保证主线程安全(suspend函数只能在协程中调用，所以不会阻塞主线程)
协程有suspend与resume，当发送网络请求，suspend函数被挂起不阻塞主线程(函数堆栈帧被保存起来)，当网络请求结束，通过resume重新切换到主线程(函数堆栈帧被重新复制回来使用)

使用结构化并发带来的好处
- 作用域取消时，它内部所有的协程也会被取消
- suspend 函数返回时，意味着它的所有任务都已完成
- 协程报错时，它所在的作用域或调用方会收到报错通知

CoroutineScope(管理协程，持有协程CoroutineContext，可被看作是一个具有超能力的 ExecutorService 的轻量级版本)
    - MainScope
    - GlobalScope
CoroutineContext(Element,组成元素 Job ， CoroutineDispatcher , CoroutineName , CoroutineExceptionHandler)
    - Job(协程的唯一标识，负责管理协程的生命周期)
        - JobSupport
    - ContinuationInterceptor(可以拦截Continuation，比如线程切换)
        - CoroutineDispatcher

Continuation(程续体，协程通过Continuation将线程切回原来的线程)
    - BaseContinuationImpl


## 协程作用域
- runBlocking：顶层函数 与 coroutineScope不同，会阻塞当前线程等待
- GlobalScope:全局协程作用域，对应整个应用
- 自定义作用域：自定义作用域可以绑定组件的生命周期防止内存泄露

## 调度器
- Main:android中的主线程
- IO
- Default：Cpu密集型
- UnConfined:非限制调度器，指定线程可能会随着挂起的函数变化

## 协程构建器
- launch:启动一个协程会返回一个Job对象，通过Job#cancel可以取消协程
- async：启动协程之后放回Deferred对象，通过Deferred#await获取结果，类似java的Future,相比较普通的挂起函数，async是可以并发执行任务的

## 挂起函数(suspend)
suspend是一个函数的关键字，仅仅起着提醒的作用，一般挂起函数的使用场景有：1.耗时操作(io,cpu) 2. 等待操作(delay方法)


# 协程通信(channel)
Channel是一个面向协程之间数据传输的BlockQueue

- 创建Channel
    - 直接创建对象
    - 扩展函数produce
- 发送数据：send
- 接收数据：receive

# 多协程并发
为了解决原子性问题，提供了Mutex，锁可以挂起非阻塞


# 参考资料

[揭秘协程中的 suspend 修饰符](https://mp.weixin.qq.com/s?__biz=MzAwODY4OTk2Mg==&mid=2652055127&idx=2&sn=283de8250bfc8a7bd8287a7aadad1339&chksm=808c8612b7fb0f047702c2101d27f4de42363ae5dd462be977ec897c7ae6a36e57b94675750a&cur_album_id=1385760483604758529&scene=189#rd)