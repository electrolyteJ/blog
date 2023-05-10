---
layout: post
title: Android | 渲染优化：垂直信号 、三级缓存、硬件加速、渲染线程
description: ui测绘的利器
tag:
- android
- renderer-ui
---

# 垂直信号vsync

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


# 三级缓存

- GraphicBuffer:由SurfaceFlinger从BUfferQueue分配，app进程的Producter生产数据，SurfaceFlinger进程的Comsumor消费数据，CPU测量数据，GPU栅格化数据。
- FrameBuffer：Display显示到屏幕的缓存

二级缓存中，Display 使用 Front Buffer ，CPU/GPU使用 Back Buffer, 这样存在的问题是CPU与gpu串行处理buffer，为了解决一个使用buffer另一个就得等待的问题，就让CPU 与 GPU 各自有一个buffer，也就是三级缓存。为了进一步减少主线程的压力，引入了RenderThead，将GPU栅格化数据的操作放在RenderThead，主线程只处理CPU测量数据与生成RenderNode、DisplayList


# 硬件加速

android4.0+默认开启了硬件加速，在android5.0+引入了渲染线程进行光栅化减少主线程负担，不同于软件绘制使用的skia，硬件绘制使用了opengl库