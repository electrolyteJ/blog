---
layout: post
title: 再谈View树
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

#### *View Tree*{:.header3-font}
好了接下来我们来讲View的测绘吧，借张图让大家了解一下测绘流程
![]({{site.asseturl}}/ui/readering-pipline.png){: .center-image }_`图片来自“从架构到源码：一文了解Flutter渲染机制”该文章`_

```
ViewRootImpl#performTraversals
#分发一系列的Window变化的事件
- dispatchXxx
#测量，计算窗口可能的size
- ViewRootImpl#measureHierarchy ---> ViewRootImpl#performMeasure ---> View#measure
WindowSession#relayout
- ViewRootImpl#performLayout ---> View#layout
- ViewRootImp#performDraw ---> ViewRootImp#draw ---> View#draw(如果使用了硬件加速就是这样 `mAttachInfo.mThreadedRenderer.draw(mView, mAttachInfo, this);`)

View的生命周期
- onAttachedToWindow
- onWindowFocusChanged
- onWindowSystemUiVisibilityChanged
- onWindowVisibilityChanged
- onApplyWindowInsets
- onMeasure
- onLayou
- onDraw
- onDetachedFromWindow
```
在Android中View树上面主要有两种类型，一种是叶子(View),一种是子树(ViewGroup，根节点也是ViewGroup)，他们都需要执行measure、layout、draw。

`measure`

在measure阶段从根节点开始dfs measure，每一个父节点会计算子节们点给的layout params(width、height、margin等)和自身的一些情况总结出一份新的宽高测量specification，然后在递归传给子节点们，当一个每个节点measure完成都会给被打上PFLAG_MEASURED_DIMENSION_SET的flag标记并且确定宽高(measure得到的宽高只是理想状态的宽高，还需要经过layout才会确定最终宽高)。

`layout`

在layout阶段依然再次dfs View树，和measure一样，每个父节点也会计算子节点们给的layout params(除了width、height、margin还会有一些像gravity这样的属性)和自身的一些情况算出子节点的位置(left,top,right,bottom)

`draw`

在draw阶段还是dfs View树，到这里我们就产生了这样的想法有没有办法将这三个步骤的dfs进行合并或者减少dfs次数，答案还需要我们去flutter寻找。
```
        /*
         * Draw traversal performs several drawing steps which must be executed
         * in the appropriate order:
         *
         *      1. Draw the background
         *      2. If necessary, save the canvas' layers to prepare for fading
         *      3. Draw view's content
         *      4. Draw children
         *      5. If necessary, draw the fading edges and restore layers
         *      6. Draw decorations (scrollbars for instance)
         */
```
绘制的流程Android团队已经在源码中告诉了我们，从根开始自顶向下绘制，那么从用户的观察角度来说的话，远离用户观察角度的先绘制，然后逐渐到达用户，对于FrameLayout、LinearLayout、RelativeLayout ViewGroup这样的容器其实不怎么需要draw，都是交给叶子绘制，它们更多用于布局子节点们

在执行完测绘之后，我们就需要将测绘之后完成的窗口通过WindowSession发送给wms，之后如果成功wms会返回并且真个窗口就可见了。
### *b.WindowManager#updateViewLayout*{:.header3-font}
在执行完addView之后窗口就变为可见了，这一切本该完成了，但是这启动的时候出现弹窗输入法的要求，那么就会updateViewLayout，重新开始整个窗口参数的调整，由于篇幅有限就不继续看下去了。

### *c.View树事件分发*{:.header3-font}
说完了View树的测绘过程，我们还需要来了解它的事件分发。
```
input pipline
1. aq:native-pre-ime(NativePreImeInputStage)
Delivers `pre-ime` input events `to a native activity`.Does not support pointer events
2. ViewPreImeInputStage
 Delivers `pre-ime` input events `to the view hierarchy`.Does not support pointer events.
3. aq:ime(ImeInputStage)
Delivers input events `to the ime`.Does not support pointer events
4. EarlyPostImeInputStage
Performs early processing of post-ime input events.
5. aq:native-post-ime(NativePostImeInputStage) 
Delivers `post-ime` input events `to a native activity`
6. ViewPostImeInputStage--->`processPointerEvent`
Delivers `post-ime` input events `to the view hierarchy`
7. SyntheticInputStage
Performs synthesis of new input events from unhandled input events
```
在ViewRootImpl#setView的最后会注册事件管道,这里我们只看ViewPostImeInputStage

ViewRootImpl$ViewPostImeInputStage.java
{:.filename}
```java
final class ViewPostImeInputStage extends InputStage {

        @Override
        protected int onProcess(QueuedInputEvent q) {
            if (q.mEvent instanceof KeyEvent) {
                return processKeyEvent(q);
            } else {
                final int source = q.mEvent.getSource();
                if ((source & InputDevice.SOURCE_CLASS_POINTER) != 0) {
                    return processPointerEvent(q);
                } else if ((source & InputDevice.SOURCE_CLASS_TRACKBALL) != 0) {
                    return processTrackballEvent(q);
                } else {
                    return processGenericMotionEvent(q);
                }
            }
        }
        ...
        private int processPointerEvent(QueuedInputEvent q) {
            final MotionEvent event = (MotionEvent)q.mEvent;

            mAttachInfo.mUnbufferedDispatchRequested = false;
            mAttachInfo.mHandlingPointerEvent = true;
            boolean handled = mView.dispatchPointerEvent(event);
            maybeUpdatePointerIcon(event);
            maybeUpdateTooltip(event);
            mAttachInfo.mHandlingPointerEvent = false;
            if (mAttachInfo.mUnbufferedDispatchRequested && !mUnbufferedInputDispatch) {
                mUnbufferedInputDispatch = true;
                if (mConsumeBatchedInputScheduled) {
                    scheduleConsumeBatchedInputImmediately();
                }
            }
            return handled ? FINISH_HANDLED : FORWARD;
        }
        ...
}
```
事件分发从View树的根节点开始(dispatchPointerEvent)，但是为了让事件也能经过Activity，根节点会先发Activity，Activity再发给Window，Window再给根节点，后面就是自顶向下发送，所以通过这样一种逻辑我们可以给根节点发送一个我们模拟的事件就能做到自动化控制页面的效果了。由于事件分发代码较多，我们这里用伪代码来简化一下。

ViewGroup.java/View.java
{:.filename}
```java
ViewGroup.java
@Override
public boolean dispatchTouchEvent(MotionEvent ev) {
     intercepted = onInterceptTouchEvent(ev)
     if(intercepted){ 
        handled = super.dispatchTouchEvent(event);
     }
    }
    ...
    return handled;
}
View.java
public boolean dispatchTouchEvent(MotionEvent event) {
    //OnTouchListener
     if (li != null && li.mOnTouchListener != null
                    && (mViewFlags & ENABLED_MASK) == ENABLED
                    && li.mOnTouchListener.onTouch(this, event)) {
                result = true;
    }
    
    if (!result && onTouchEvent(event)) {
                result = true;
    }
    
    //在onTouchEvent方法里面执行
     performClick();
}
ViewGroup
- onInterceptTouchEvent //定义View重写该方法
- OnTouchListener#onTouch //暴露给外部使用的监听接口
- onTouchEvent //自定义View重写该方法
- OnClickListener#onClick //暴露给外部使用的监听接口

View
- OnTouchListener#onTouch //暴露给外部使用的监听接口
- onTouchEvent //自定义View重写该方法 
- OnClickListener#onClick //暴露给外部使用的监听接口
```
与叶子节点不同的是，其父节点具备拦截功能，在事件分发的过程如果子节点不希望父节点拦截事件,可以通过`requestDisallowInterceptTouchEvent`

## *2.Reference*{:.header2-font}
[从架构到源码：一文了解Flutter渲染机制](https://developer.aliyun.com/article/770384)


