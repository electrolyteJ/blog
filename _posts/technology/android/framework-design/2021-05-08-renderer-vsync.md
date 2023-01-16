---
layout: post
title: Android | 垂直信号vsync
description: ui测绘的利器
author: 电解质
date: 2021-05-08
share: true
tag:
- android-framework-design
- elementary/renderer
---

为了描述方便这里默认系统的刷新率为60hz。

为了提高Android的UI流畅性，Android团队采用了vsync+三buffer。其中处理vsync的Choreographer这个类，其类主要是用来监听vsync和调度vsync。那么vsync能带来什么？vsync能解决屏幕撕裂、跳帧、视觉伪影(抖动)的问题,能帮助屏幕(刷新率eg.60Hz)和应用(GPU 帧率 60fps or 60hz)实现帧同步。

Choreographer每次post一个回调，都会调用DisplayEventReceiver#scheduleVsync向底层发送需要vsync的通知。屏幕的刷新率为60hz，在接受到vsync这个信号之后会处理一下事情然后通知Choreographer，Choreographer会主线程doFrame这一帧，在下一次vsync来临之前得提前将frame写入buffer供屏幕使用，在这一帧里面会通知UI有四种类型的需要回调。这一帧必须要在16ms处理完不然就会出现掉帧。其实如果帧率一直是50fps这样稳定还看不出掉帧，比较明显的掉帧是帧率不稳定，一会50fps一会60fps再一会40fps掉帧的感觉就会比较明显。

这里要说一下一帧的消耗怎么算？MessageQueue每次接受到一条message就会触发主线程Handler#dispatchMessage(handleCallback,handleMessage),从而完成一次ui更新。其中处理一条message消费的时间即为一帧的消耗。其实还有一种计算一帧耗时的方法，每次在FrameCallback#doFrame方法快结束时就再Choreographer#postFrameCallback一个FrameCallback，然后计算两次的时间差。对帧率监控有兴趣的可以看看这些项目：matrix、ArgusAPM
```
# size 为4，其类型为如下
# 1.输入事件callback
# 2.动画callback
# 3.递归view树callback，处理layout 和draw
# 4.提交callback，处理post-draw的操作
# 执行顺序也是从数组头部到尾部。
CallbackQueue[] mCallbackQueues
```
CallbackQueue将CallbackRecord对象遵循时间递增顺序入队，队头总是被先消费，而其方法extractDueCallbacksLocked就是获取现在时间之前的CallbackRecord链表，及时处理回调链。

每个线程拿到的Choreographer对象都是互不影响(ThreadLocal),那么也就意味着，事件线程、动画线程(InvalidateOnAnimationRunnable)，ui测绘线程都有一个Choreographer，最后都会在主线程doFrame处理这一帧