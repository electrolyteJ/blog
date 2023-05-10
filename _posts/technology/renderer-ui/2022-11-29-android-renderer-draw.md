---
layout: post
title: Android | 深入Android UI绘制
description:  View、RenderNode 、GraphicBuffer 、 HardwareRenderer
tag:
- android
- renderer-ui
---
* TOC
{:toc}

# 名词解释

基础概念：

- 图形库(Graphic): OpenGl ES(2d、3d，GLES) 、Skia(2d)、Vulkan(3d)、Metal
- 图像(Image) ： PNG、Webp
- 绘制：图形库支持硬件加速绘制(GPU)与软件绘制(CPU)

> ps:EGL™ is an interface between Khronos rendering APIs such as OpenGL ES or OpenVG and the underlying native platform window system.EGL是接口，整合了 图形库 与 平台窗口系统。可以这么理解EGL向外部定义了一套接口规范，保证OpenGL ES这样的图形库与各个平台暴露出来的接口一致。

> Graphic与Image的关系，一言以蔽之：Graphic draw image

渲染器中的角色：

java类|jni | cpp类 | hybrid类
|---|---|---|---|
FrameInfo| NA |FrameInfo|FrameInfo
ThreadedRenderer    /HardwareRenderer| android_graphics_HardwareRenderer |RenderProxy | HardwareRenderer
RenderNode|android_graphics_RenderNode | RenderNode | RenderNode
CompatibleCanvas   /软件Canvas|android_graphics_Canvas|SkiaCanvas|CompatibleCanvas
RecordingCanvas   /硬件Canvas|android_graphics_DisplayListCanvas|SkiaRecordingCanvas(                   Canvas)、RecordingCanvas(             SkCanvasVirtualEnforcer)|RecordingCanvas
NA| NA |BufferQueueConsumer   /IGraphicBufferConsumer| NA
NA| NA |BufferQueueProducer   /IGraphicBufferProducer| NA
NA| NA |BufferQueue | NA 
NA| NA |GraphicBuffer| NA 
NA| NA |SurfaceFlinger| NA 
Surface| android_view_Surface |Surface| Surface 
NA| NA |Hardware Composer| NA 
NA| NA |Gralloc| NA 

> ps: hybrid类 除了类名不同，角色职能差不多，分两部分内存,一部分在java heap ， 一部分在cpp heap。

HardwareRenderer的hybrid类对象持有RenderThread单例对象 、 CanvasContext对象、DrawFrameTask对象、root RenderNode对象

DrawFrameTask是运行在RenderThread线程的任务,而RenderThread又是基于Looper实现，等同于java的HandlerThread。

RenderNode的hybrid类对象持有DisplayList对象、RecordingCanvas对象

RecordingCanvas的hybrid类对象持有root RenderNode对象、SkiaDisplayList对象(或者DisplayList，取决于cpp 侧的Canvas子类是哪一个)

CanvasContext的native类对象持有RenderNode对象数组

SurfaceFlinger:
- Hardware Composer:硬件合成
- Gralloc：图形内存分配器

# 硬件绘制(hwui)

在硬件绘制中引入了RenderNode、DisplayList、RecordingCanva，每个View相当于RenderNode，其持有DisplayList对象和RecordingCanva对象，而软件绘制整棵树只有一个Canvas，这样对于做不到局部更新，对于无变化的View也会被迫更新，那么就从调用`mAttachInfo.mThreadedRenderer.draw(mView, mAttachInfo, this);`开始分析。

```java
    void draw(View view, AttachInfo attachInfo, DrawCallbacks callbacks) {
        ...
        updateRootDisplayList(view, callbacks);
        ...
        
        final long[] frameInfo = choreographer.mFrameInfo.mFrameInfo;
        ...
        int syncResult = nSyncAndDrawFrame(mNativeProxy, frameInfo, frameInfo.length);
        ...
    }
```
ThreadedRenderer#draw主要做两件事：

1. 更新Root RenderNode:调用每个view的draw获得全部canvas指令且转换成RenderNode对象(包含DisplayList和影响DisplayList的属性) 
2. 异步绘制：调用DrawFrameTask#drawFrame

## 更新Root RenderNode

updateRootDisplayList函数调用链
```java
View.updateDisplayListIfDirty();
--> canvas.drawRenderNode
--> SkiaRecordingCanvas#drawRenderNode
--> SkiaCanvas#drawDrawable
--> skia库的绘制
```

## 异步绘制

react native 实现了异步布局，而android实现了异步绘制，他们的目的都是为了减轻主线程(UI线程)的负担，降低掉帧率。

nSyncAndDrawFrame函数调用链
```java
ThreadedRenderer#nSyncAndDrawFrame
--> android_view_ThreadedRenderer#syncAndDrawFrame 
--> RenderProxy#syncAndDrawFrame 
--> DrawFrameTask#drawFrame
--> DrawFrameTask#postAndWait
--> DrawFrameTask#run
```

```cpp
void DrawFrameTask::run() {
    ATRACE_NAME("DrawFrame");

    bool canUnblockUiThread;
    bool canDrawThisFrame;
    {
        TreeInfo info(TreeInfo::MODE_FULL, *mContext);
        //1.同步Choreographer 的FrameInfo，将一帧的开始时间传给渲染线程做备案
        canUnblockUiThread = syncFrameState(info);
        canDrawThisFrame = info.out.canDrawThisFrame;
    }

    // Grab a copy of everything we need
    CanvasContext* context = mContext;

    // From this point on anything in "this" is *UNSAFE TO ACCESS*
    if (canUnblockUiThread) {
        unblockUiThread();
    }

    if (CC_LIKELY(canDrawThisFrame)) {
        context->draw();
    } else {
        // wait on fences so tasks don't overlap next frame
        context->waitOnFences();
    }

    if (!canUnblockUiThread) {
        unblockUiThread();
    }
}
```

当调用postAndWait函数时，会异步执行DrawFrameTask#run，且会阻塞主线程。当syncFrameState同步成功且返回true时，调用unblockUiThread函数继续进行主线程, 反之同步失败返回false则会等到draw结束才释放对主线程的阻塞。在CanvasContext#draw流程中，渲染类型有两种SkiaGL和SkiaVulkan，IRenderPipeline的实现类有SkiaOpenGLPipeline、SkiaVulkanPipeline，接下来主要看SkiaOpenGLPipeline#draw的绘制流程

<!-- - mRenderPipeline->swapBuffers -->

异步绘制的systrace埋点显示

- syncFrameState -->  prepareTree --> Texture upload(16) 88x111
- dequeueBuffer --> dequeueBuffer --> addAndGetFrameTimestamps
- flush commands --> shader_compile --> ShaderCache::load
- eglSwapBuffersWithDamageKHR --> queueBuffer --> queueBuffer --> onFrameAvailable --> processNextBufferLocked

当GPU栅格化完成且swap buffer到SurfaceFlinger进程等待被合成，那么app进程的事情就告一段落，后面的控制权就到了SurfaceFlinger进程。

# 软件绘制

使用了软件绘制的Android系统会调用ViewRootImpl#drawSoftware方法

```java
private boolean drawSoftware(Surface surface, AttachInfo attachInfo, int xoff, int yoff,
            boolean scalingRequired, Rect dirty, Rect surfaceInsets) {
        ...
        // Draw with software renderer.
        final Canvas canvas;
        ...
        try {
            ...
            canvas = mSurface.lockCanvas(dirty);

            // TODO: Do this in native
            canvas.setDensity(mDensity);
        } catch (Surface.OutOfResourcesException e) {
            ...
        } catch (IllegalArgumentException e) {
            ...
        } finally {
            dirty.offset(dirtyXOffset, dirtyYOffset);  // Reset to the original value.
        }

        try {
            ...
            mView.draw(canvas);
        } finally {
              try {
                surface.unlockCanvasAndPost(canvas);
            } catch (IllegalArgumentException e) {
                ...
            }
            ...
        }
        ...
}

```
1. mSurface.lockCanvas: 获取Canvas对象,软件绘制的Canvas实现类为CompatibleCanvas(java部分:CompatibleCanvas，cpp部分：SkiaCanvas)
2. mView.draw(canvas): 收集Canvas绘制指令
3. surface.unlockCanvasAndPost: canvas指令写到GraphicBuffer，并且发送到SurfaceFlinger

混合类Surface的lock与unlock分别会从SurfaceFlinger获取GraphicBuffer和返回GraphicBuffer给SurfaceFlinger，由于Binder传输限制在8k-1m，对于GraphicBuffer这种存储大数据来说并不适用所以采用匿名共享内存实现数据传输。

在lock阶段调用IGraphicBufferProducer(BufferQueueProducer实现类)#dequeueBuffer函数获取空闲的GraphicBuffer，获取到的GraphicBuffer被当做backBuffer。

在unlock阶段调用IGraphicBufferProducer(BufferQueueProducer实现类)#queueBuffer将被栅格化的GraphicBuffer传给SurfaceFlinger合成。

# *参考资料*
[硬件加速](https://developer.android.com/guide/topics/graphics/hardware-accel?hl=zh-cn) 
[图形](https://source.android.com/docs/core/graphics)
[EGL](https://www.khronos.org/egl)
[Android硬件加速原理与实现简介](https://tech.meituan.com/2017/01/19/hardware-accelerate.html)
[Android 系统架构 —— View 的硬件渲染](https://sharrychoo.github.io/blog/android-source/graphic-draw-hardware)
[Android中的GraphicBuffer同步机制-Fence](https://www.cnblogs.com/brucemengbm/p/6881925.html)
[Android应用程序UI硬件加速渲染技术简要介绍和学习计划](https://blog.csdn.net/luoshengyang/article/details/45601143)
[Skia Api Docs](https://api.skia.org/classSkCanvasVirtualEnforcer.html)
[Skia Docs](https://skia.org/docs/)
[LearnOpenGL-CN](https://learnopengl-cn.readthedocs.io/zh/latest/01%20Getting%20started/01%20OpenGL/)
