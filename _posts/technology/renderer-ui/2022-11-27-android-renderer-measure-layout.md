---
layout: post
title: Android | Android UI测量与布局
description: 测量与布局
tag:
- android
- renderer-ui
---
* TOC
{:toc}

我们知道当ActivityThreead通过binder这条通道向framework取到apk包的Application info、ContentProvider info、Activity info等组件数据之后,按部就班的完成Application、ContentProvider生命周期，接踵而来的Activity生命周期到resume时，就开始UI的表演了。

在ActivityThread#handleLaunchActivity完成xml树到view树的创建，在ActivityThread#handleResumeActivity完成之后窗口就可见可交互。ActivityThread#handleResumeActivity有三个重要的阶段：performResumeActivity、WindowManager#addView、WindowManager.updateViewLayout。

- performResumeActivity：performResumeActivity中的Activity#onResume完成之后，窗口还是不可见不可交互，要等到完成Activity#onWindowFocusChanged，窗口才真正可交互。
- WindowManager#addView：对于Activity、Dialog、Toast、PopupWindow这些UI控制器，内部都维护着一个窗口,窗口又是View树的画板，那么如何往窗口添加View呢？App内部有个全局单例WindowManagerGlobal，它负责application层的addView、removeView。每当add一个view树根节点的时候，都会创建一个ViewRootImpl用于管理View树，ViewRootImpl会分发事件、执行动画、测量布局绘制所有节点，对于Activity、Dialog来说View树的根节点为DecorView。
- WindowManager#updateViewLayout：updateViewLayout会重新调整整个窗口参数，主要出现在出现输入法弹窗的场景。

WindowManager管理者数组Root View和数组ViewRootImpl，也就是当前的app是存在多窗口的情况。
```java
    //保存View树的根节点
    private final ArrayList<View> mViews = new ArrayList<View>();
    //保存窗口的管理者ViewRootImpl
    private final ArrayList<ViewRootImpl> mRoots = new ArrayList<ViewRootImpl>();
    //窗口的参数:大小等
    private final ArrayList<WindowManager.LayoutParams> mParams = new ArrayList<WindowManager.LayoutParams>();
```

View添加到窗口的函数调用链`WindowManager#addView --> ViewRootImpl#setView --> ViewRootImpl#requestLayout --> ViewRootImpl#scheduleTraversals`，当调用scheduleTraversals方法时通过barrier将主线程的同步消息屏蔽(异步消息依然会被处理)只会专注处理Choreographer发来的异步消息,紧接着Choreographer等待屏幕发来的vsync信号，信号一到就通过异步消息切换到主线程依次完成事件、动画、View树测绘(先去掉barrier再开始测绘)。

# *View Tree*
好了接下来我们来讲View的测绘吧，借张图让大家了解一下测绘流程
![]({{site.asseturl}}/android-framework/readering-pipline.png){: .center-image }_`图片来自“从架构到源码：一文了解Flutter渲染机制”该文章`_

```
ViewRootImpl#performTraversals
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

ViewRootImpl#performTraversals
- dispatchXxx：分发一系列的Window变化的事件
- ViewRootImpl#measureHierarchy ---> ViewRootImpl#performMeasure ---> View#measure：测量，计算窗口可能的size
- ViewRootImpl#performLayout ---> View#layout
- ViewRootImp#performDraw ---> ViewRootImp#draw ---> View#draw(如果使用了硬件加速就是这样 `mAttachInfo.mThreadedRenderer.draw(mView, mAttachInfo, this);`)

在Android中View树上面主要有两种类型，一种是叶子(View),一种是子树(ViewGroup，根节点也是ViewGroup)，他们都需要执行measure、layout、draw。

## measure

在measure阶段从根节点开始dfs View数，每个父节点会将所有子节的layout params(width、height、margin等)和自身的宽高、padding值总结出一份新的宽高测量specification，然后传给其子节点，子节点如果是View则会自测量，如果自测量的宽高不满足会让父节点重新计算spec，所以确定宽高并不是一次measure就完成的。每个节点measure完成都会被打上PFLAG_MEASURED_DIMENSION_SET的flag标记表明measure之后的宽高(measure得到的宽高只是理想状态的宽高，还需要经过layout才会确定最终宽高)。

## layout

在layout阶段依然再次dfs View树，和measure一样，每个父节点也会计算子节点们给的layout params(除了width、height、margin还会有一些像gravity这样的属性)和自身的一些情况算出子节点的位置(left,top,right,bottom)

## draw

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



