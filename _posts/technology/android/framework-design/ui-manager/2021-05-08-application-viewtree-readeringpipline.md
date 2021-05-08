---
layout: post
title: 再谈View树渲染流水线
description: 整理出2017年的笔记View
author: 电解质
date: 2021-05-08
share: true
tag:
- framework-design/ui
---
* TOC
{:toc}
## *1.Introduction*{:.header2-font}
最近整理2017年关于View的笔记，重新修改了一下发出来，那么接下来就让我们open the door。

我们知道当ActivityThreead通过binder这条通道向framework取到apk包的Application info、ContentProvider info、Activity info等组件数据之后,按部就班的完成Application、ContentProvider生命周期，接踵而来的Activity生命周期到resume时，就开始UI的表演了。

```java
public final class ActivityThread {
...
    final void handleResumeActivity(IBinder token,
                boolean clearHide, boolean isForward, boolean reallyResume, int seq, String reason) {
         r = performResumeActivity(token, clearHide, reason);
         if (r != null) {
         ...
            if (r.window == null && !a.mFinished && willBeVisible) {
                    r.window = r.activity.getWindow();
                    View decor = r.window.getDecorView();
                    decor.setVisibility(View.INVISIBLE);
                    ViewManager wm = a.getWindowManager();
                    WindowManager.LayoutParams l = r.window.getAttributes();
                    a.mDecor = decor;
                    ...
                    if (a.mVisibleFromClient) {
                        if (!a.mWindowAdded) {
                            a.mWindowAdded = true;
                            wm.addView(decor, l);
                        
                        } else {
                           ...
                        }   
                    }
            
            } else if (!willBeVisible) {
            ...
            }
            ...
            // The window is now visible if it has been added, we are not
            // simply finishing, and we are not starting another activity.
            if (!r.activity.mFinished && willBeVisible
                        && r.activity.mDecor != null && !r.hideForNow) {
                        
                    ...
                        
                    if ((l.softInputMode
                            & WindowManager.LayoutParams.SOFT_INPUT_IS_FORWARD_NAVIGATION)
                            != forwardBit) {
                        l.softInputMode = (l.softInputMode
                                & (~WindowManager.LayoutParams.SOFT_INPUT_IS_FORWARD_NAVIGATION))
                                | forwardBit;
                        if (r.activity.mVisibleFromClient) {
                            ViewManager wm = a.getWindowManager();
                            View decor = r.window.getDecorView();
                            wm.updateViewLayout(decor, l);
                        }
                    }
                    ...
            }
         }
    }
}
```
当performResumeActivity完成之后(也就是Activity#onResume)，窗口还不是可见的，那么什么时候可见？接下来我们就来看看。

上面的代码主要有两部分需要关注
- wm.addView
- wm.updateViewLayout

### *a.WindowManager#addView*{:.header3-font}

对于Activity、Dialog、Toast、PopupWindow这些UI控制器，内部都维护着一个窗口,窗口又是View树的画板。那么如何往窗口添加View呢？App内部有个全局单例WindowManagerGlobal，它负责application层的addView、removeView。每当add一个view树根节点的时候，都会创建一个ViewRootImpl用于管理View树，然后将对于View树的控制权交给了ViewRootImpl，ViewRootImpl会绘制所有节点,事件分发等操作。对于Activity、Dialog来说View树的根节点为DecorView。

#### *WindowManager/ViewRootImpl*{:.header3-font}
WindowManager
{:.filename}
```java
    //保存View树的根节点
    private final ArrayList<View> mViews = new ArrayList<View>();
    //保存窗口的管理者ViewRootImpl
    private final ArrayList<ViewRootImpl> mRoots = new ArrayList<ViewRootImpl>();
    //窗口的参数:大小等
    private final ArrayList<WindowManager.LayoutParams> mParams = new ArrayList<WindowManager.LayoutParams>();
```
当调用WIndowManager#addView,会将View树根节点注入到ViewRootImpl对象，并且马不停蹄地开始测绘整个View树。我们知道在Activity的onResume之前还有onCreate，onCreate方法体内会将用户自定义的View树挂到DecorView，所以整个测绘过程漫长而且繁琐。

ViewRootImpl：
{:.filename}
```
mWinFrame(framework层wms给的窗口大小,mWidth/mHeight)
mAttachInfo(App层的窗口信息，其中也包括当前的窗口大小)
setView
    #requestLayout 会执行measure、layout、draw 而invaldate 只会执行layout、draw
    - requestLayout -->scheduleTraversals
    - addToDisplay
```

当进行View树遍历时，通过barrier将主线程中同步消息屏蔽(异步消息依然会被处理)只会专注处理Choreographer发来的异步消息,紧接着Choreographer等待GPU发来的vsync信号。信号一到就通过异步消息切换到主线程依次完成事件、动画、View树测绘(先去掉barrier再开始测绘)。

```
performTraversals
1. View#dispatchAttachedToWindow
2. ViewTreeObserver#dispatchOnWindowAttachedChange(true);
3. View#dispatchApplyWindowInsets
4. View#dispatchWindowVisibilityChanged
5. performMeasure(View#measure)
6. relayoutWindow
7. performLayout(View#layout)
8. ViewTreeObserver#dispatchOnGlobalLayout
8. IWindowSession#setTransparentRegion
9. IWindowSession#setInsets
10. ViewTreeObserver#dispatchOnPreDraw
11. performDraw  
12. ViewTreeObserver#dispatchOnDraw
13. 优先使用硬件加速mThreadedRenderer#draw，不行只能用软件绘制View#draw
12. pendingDrawFinished
```

只有第一次进行遍历View树，会执行setup 1 2;如果不是第一次并且DecorView的可见性发生了变化，则会执行setup 3

在讲View测绘之前，我们先来讲讲一个更为重要的角色Choreographer。

#### *Choreographer*{:.header3-font}
为了描述方便这里默认系统的刷新率为60hz。

为了提高Android的UI流畅性，Android团队采用了vsync+三buffer。其中处理vsync的Choreographer这个类，其类主要是用来监听vsync和调度vsync。那么vsync能带来什么？vsync能解决屏幕撕裂、跳帧、视觉伪影(抖动)的问题,能帮助屏幕(刷新率eg.60Hz)和应用(GPU 帧率 60fps or 60hz)实现帧同步。

Choreographer每次post一个回调，都会调用DisplayEventReceiver#scheduleVsync向底层发送需要vsync的通知。屏幕的刷新率为60hz，在接受到vsync这个信号之后会处理一下事情然后通知Choreographer，Choreographer会doFrame这一帧，在下一次vsync来临之前得提前将frame写入buffer供屏幕使用，在这一帧里面会通知UI有四种类型的需要回调。这一帧必须要在16ms处理完不然就会出现掉帧。其实如果帧率一直是50fps这样稳定还看不出掉帧，比较明显的掉帧是帧率不稳定，一会50fps一会60fps在一会40fps掉帧的感觉就会比较明显。

这里要说一下一帧的消耗怎么算？MessageQueue每次接受到一条message就会触发主线程Handler#dispatchMessage(handleCallback,handleMessage),从而完成一次ui更新。其中处理一条message消费的时间即为一帧的消耗。其实还有一种计算一帧耗时的方法往Choreographer的callback每次在方法快结束就post一条FrameCallback，然后计算两次的时间差。对帧率监控有兴趣的可以看看这些项目：matrix、ArgusAPM
```
# size 为4，其类型为如下
# 1.输入事件callback
# 2.动画callback
# 3.递归view树callback，处理layout 和draw
# 4.提交callback，处理post-draw的操作
# 执行顺序也是从数组头部到尾部。
CallbackQueue[] mCallbackQueues
```
CallbackQueue将CallbackRecord遵循时间排序以链表结构存储起来，而其方法extractDueCallbacksLocked就是获取现在时间之前的CallbackRecord链表，及时处理回调链。

每个线程拿到的Choreographer对象都是互不影响(ThreadLocal),那么也就意味着，事件线程、动画线程(InvalidateOnAnimationRunnable)，ui测绘线程都有一个Choreographer。


好了接下来我们来讲View的测绘吧。
![]({{site.asseturl}}/ui/readering-pipline.png){: .center-image }_`图片来自“从架构到源码：一文了解Flutter渲染机制”该文章`_


### *b.WindowManager#updateViewLayout*{:.header3-font}
在执行完addView之后窗口就变为可见了，这一切本该完成了，但是这启动的时候出现弹窗输入法的要求，那么就会updateViewLayout，重新开始整个窗口参数的调整。

ViewRootImpl：
```java
updateViewLayout
```
## *2.Reference*{:.header2-font}
[从架构到源码：一文了解Flutter渲染机制](https://developer.aliyun.com/article/770384)


