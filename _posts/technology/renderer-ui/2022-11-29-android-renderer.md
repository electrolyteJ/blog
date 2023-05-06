---
layout: post
title: Android | Android渲染器
description: SurfaceFlinger 、 Hardware Composer 、Gralloc 、 BufferQueue 、IGraphicBufferProducer
author: 电解质
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

>Graphic与Image的关系，一言以蔽之：Graphic draw image

渲染器中的角色：

java类|jni | cpp类 | hybrid类
|---|---|---|---|
ThreadedRenderer| android_view_ThreadedRenderer|RenderProxy | ThreadedRenderer
RenderNode|android_view_RenderNode | RenderNode | RenderNode
DisplayListCanvas|android_view_DisplayListCanvas|Canvas(、SkiaRecordingCanvas、RecordingCanvas)|DisplayListCanvas
FrameInfo| 没有jni类|FrameInfo|FrameInfo

> ps: hybrid类 除了类名不同，角色职能差不多，分两部分内存,一部分在java heap ， 一部分在cpp heap。

ThreadedRenderer的hybrid类对象持有RenderThread单例对象 、 CanvasContext对象、DrawFrameTask对象、root RenderNode对象

DisplayListCanvas的hybrid类对象持有root RenderNode对象、SkiaDisplayList对象(或者DisplayList，取决于cpp 侧的Canvas子类是哪一个)


三级缓存：
- GraphicBuffer:由SurfaceFlinger从BUfferQueue分配，app进程的Producter生产数据，SurfaceFlinger进程的Comsumor消费数据，CPU测量数据，GPU栅格化数据。
- FrameBuffer：Display显示到屏幕的缓存

二级缓存中，Display 使用 Front Buffer ，CPU/GPU使用 Back Buffer, 这样存在的问题是CPU与gpu串行处理buffer，为了解决一个使用buffer另一个就得等待的问题，就让CPU 与 GPU 各自有一个buffer，也就是三级缓存。为了进一步减少主线程的压力，引入了RenderThead，将GPU栅格化数据的操作放在RenderThead，主线程只处理CPU测量数据与生成RenderNode、DisplayList

# 硬件绘制

开启了硬件加速的Android系统在绘制时会调用`mAttachInfo.mThreadedRenderer.draw(mView, mAttachInfo, this);`

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
draw主要做两件事：

1. 更新DisplayList:调用每个view的draw获得全部canvas指令且转换成RenderNode对象(包含DisplayList和影响DisplayList的属性) 
2. 异步渲染：调用DrawFrameTask#drawFrame

## 更新DisplayList

updateRootDisplayList函数调用链
```java
View.updateDisplayListIfDirty();
--> canvas.drawRenderNode
--> jni call --> SkiaRecordingCanvas#drawRenderNode
--> SkiaCanvas#drawDrawable
--> skia库的绘制
```
## 异步渲染

react native 实现了异步布局，而android实现了异步渲染，他们的目的都是为了减轻主线程(UI线程)的负担，降低掉帧率。

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

DrawFrameTask是运行在RenderThread线程的任务,而RenderThread又是基于Looper实现，等同于java的HandlerThread，所以当调用postAndWait函数时，会异步执行DrawFrameTask#run，且会阻塞主线程，当syncFrameState同步成功且返回true时，调用unblockUiThread函数继续进行主线程, 反之同步失败返回false则会等到draw结束才释放对主线程的阻塞。

```cpp
CanvasContext* CanvasContext::create(RenderThread& thread, bool translucent,
                                     RenderNode* rootRenderNode, IContextFactory* contextFactory) {
    auto renderType = Properties::getRenderPipelineType();

    switch (renderType) {
        case RenderPipelineType::SkiaGL:
            return new CanvasContext(thread, translucent, rootRenderNode, contextFactory,
                                     std::make_unique<skiapipeline::SkiaOpenGLPipeline>(thread));
        case RenderPipelineType::SkiaVulkan:
            return new CanvasContext(thread, translucent, rootRenderNode, contextFactory,
                                     std::make_unique<skiapipeline::SkiaVulkanPipeline>(thread));
        default:
            LOG_ALWAYS_FATAL("canvas context type %d not supported", (int32_t)renderType);
            break;
    }
    return nullptr;
}
```
在CanvasContext#draw流程中，IRenderPipeline的实现类有SkiaOpenGLPipeline、SkiaVulkanPipeline、这里主要看SkiaOpenGLPipeline

<!-- - mRenderPipeline->swapBuffers -->

异步绘制的systrace埋点显示

- syncFrameState -->  prepareTree --> Texture upload(16) 88x111
- dequeueBuffer --> dequeueBuffer --> addAndGetFrameTimestamps
- flush commands --> shader_compile --> ShaderCache::load
- eglSwapBuffersWithDamageKHR --> queueBuffer --> queueBuffer --> onFrameAvailable --> processNextBufferLocked

当GPU栅格化完成且swap buffer到SurfaceFlinger进程，那么app进程的事情就告一段落，接下来控制权就到了SurfaceFlinger进程


<!-- # 软件绘制 -->

# *参考资料*
[硬件加速](https://developer.android.com/guide/topics/graphics/hardware-accel?hl=zh-cn) 
[图形](https://source.android.com/docs/core/graphics)
[EGL](https://www.khronos.org/egl)
[Android硬件加速原理与实现简介](https://tech.meituan.com/2017/01/19/hardware-accelerate.html)
[Android 系统架构 —— View 的硬件渲染](https://sharrychoo.github.io/blog/android-source/graphic-draw-hardware)