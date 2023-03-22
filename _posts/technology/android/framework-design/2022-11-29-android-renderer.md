---
layout: post
title: Android | Android渲染器
description: SurfaceFlinger 、 Hardware Composer 、Gralloc 、 BufferQueue 、IGraphicBufferProducer
author: 电解质
tag:
- android
- elementary/renderer
---

## 名词解释

基础概念：

- 图形库(Graphic): OpenGl ES(2d、3d，GLES) 、Skia(2d)、Vulkan(3d)
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


> ps: hybrid类 除了类名不同，角色职能差不多，分两部分内存一份在java heap ， 一部分在cpp heap。

ThreadedRenderer的hybrid类对象持有RenderThread单例对象 、 CanvasContext对象、DrawFrameTask对象、root RenderNode对象

DisplayListCanvas的的hybrid类对象持有root RenderNode对象、SkiaDisplayList对象(或者DisplayList，取决于cpp 侧的Canvas子类是哪一个)


开启了硬件加速的Android系统在绘制时会调用`mAttachInfo.mThreadedRenderer.draw(mView, mAttachInfo, this);`

```java
    void draw(View view, AttachInfo attachInfo, DrawCallbacks callbacks) {
        ...
        //1.调用每个view的draw获得全部canvas指令且转换成DisplayList对象
        // View.updateDisplayListIfDirty();
        //--> canvas.drawRenderNode
        //--> jni call --> SkiaRecordingCanvas#drawRenderNode
        //---> SkiaCanvas#drawDrawable
        // ---> skia库的绘制
        updateRootDisplayList(view, callbacks);

        ...
        
        final long[] frameInfo = choreographer.mFrameInfo.mFrameInfo;
        //2. ThreadedRenderer#nSyncAndDrawFrame
        //-->android_view_ThreadedRenderer#syncAndDrawFrame 
        //--> RenderProxy#syncAndDrawFrame 
        //--> DrawFrameTask#drawFrame
        int syncResult = nSyncAndDrawFrame(mNativeProxy, frameInfo, frameInfo.length);
        ...
    }
```
draw主要做两件事调用每个view的draw获得全部canvas指令且转换成RenderNode(包含DisplayList和影响DisplayList的属性)对象和调用DrawFrameTask#drawFrame。DrawFrameTask是运行在RenderThread线程的任务,而RenderThread又是基于Looper实现，本质上有点等同于java的HandlerThread。执行drawFrame函数会异步执行DrawFrameTask任务，且会阻塞主线程，等待任务完成，所以这里还不是异步渲染。锁只有等待unblockUiThread调用才会释放并且开始异步draw。

```cpp
void DrawFrameTask::run() {
    ATRACE_NAME("DrawFrame");

    bool canUnblockUiThread;
    bool canDrawThisFrame;
    {
        TreeInfo info(TreeInfo::MODE_FULL, *mContext);
        //1.同步从Choreographer 的FrameInfo，将一帧的开始时间传给渲染线程做备案
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
- syncFrameState -->  prepareTree --> Texture upload(16) 88x111
- dequeueBuffer --> dequeueBuffer --> addAndGetFrameTimestamps
- flush commands --> shader_compile --> ShaderCache::load
- eglSwapBuffersWithDamageKHR --> queueBuffer --> queueBuffer --> onFrameAvailable --> processNextBufferLocked





```cpp
//渲染流水线
CanvasContext* CanvasContext::create(RenderThread& thread,
        bool translucent, RenderNode* rootRenderNode, IContextFactory* contextFactory) {

    auto renderType = Properties::getRenderPipelineType();

    switch (renderType) {
        case RenderPipelineType::OpenGL:
            return new CanvasContext(thread, translucent, rootRenderNode, contextFactory,
                    std::make_unique<OpenGLPipeline>(thread));
        case RenderPipelineType::SkiaGL:
            return new CanvasContext(thread, translucent, rootRenderNode, contextFactory,
                    std::make_unique<skiapipeline::SkiaOpenGLPipeline>(thread));
        case RenderPipelineType::SkiaVulkan:
            return new CanvasContext(thread, translucent, rootRenderNode, contextFactory,
                                std::make_unique<skiapipeline::SkiaVulkanPipeline>(thread));
        default:
            LOG_ALWAYS_FATAL("canvas context type %d not supported", (int32_t) renderType);
            break;
    }
    return nullptr;
}
```






react native 实现了异步布局，而android实现了异步渲染，他们的目的都是为了减轻主线程(UI线程)的负担，降低掉帧率。


## *参考资料*
[硬件加速](https://developer.android.com/guide/topics/graphics/hardware-accel?hl=zh-cn) 
[图形](https://source.android.com/docs/core/graphics)
[EGL](https://www.khronos.org/egl)
[Android硬件加速原理与实现简介](https://tech.meituan.com/2017/01/19/hardware-accelerate.html)