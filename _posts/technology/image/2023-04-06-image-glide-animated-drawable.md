---
layout: post
title: 图像 | Glide 动图
description: Webp、Gif、AVIF动图介绍与优化
tag: 
- image
- android
---
* TOC
{:toc}
Glide在Gif动图采用了第三方提供的编解码库，再次基础上适配了Glide框架的加载流程，其在Glide项目的代码结构主要在这几个地方

- third_party/gif_encoder库
- third_party/gif_decoder库
- com.bumptech.glide.load.resource.gif包
- com.bumptech.glide.load.resource.transcode.GifDrawableBytesTranscoder类

# Gif加载流程
当Gif从网络或者本地文件读取到数据之后，接下里就开始进行`decode -> transform -> encode -> transcode -> target`流程.

- decode: StreamGifDecoder/ByteBufferGifDecoder：数据流转GifDrawable
- transform: GifDrawableTransformation：GifDrawabl transform操作
- encode: GifDrawableEncoder：数据写入disk cache文件
- transcode: GifDrawableBytesTranscoder/UnitTranscoder：GifDrawable转码器
- target: DrawableImageViewTarget

整个流程还是比较清晰的都是围绕GifDrawable进行编码、解码、转码等操作，那么Gif又是如何一帧一帧的绘制让图片动起来的？ 当图片经过编码、transform、解码、转码之后,ImageViewTarget调用maybeUpdateAnimatable执行GifDrawable的start方法。
```
  private void maybeUpdateAnimatable(@Nullable Z resource) {
    if (resource instanceof Animatable) {
      animatable = (Animatable) resource;
      animatable.start();
    } else {
      animatable = null;
    }
  }
```
GifFrameLoader类会从GifDecoder加载一帧，然后调用invalidateSelf绘制这一帧到屏幕。

```java
        .append(
            GifDecoder.class, GifDecoder.class, UnitModelLoader.Factory.<GifDecoder>getInstance())
        .append(
            Registry.BUCKET_BITMAP,
            GifDecoder.class,
            Bitmap.class,
            new GifFrameResourceDecoder(bitmapPool))
```
GifDecoder解码这一帧给DelayTarget需要GifFrameResourceDecoder解码出一帧Bitmap(GifDecoder#getNextFrame)，然后调用onFrameReady回调告诉GifDrawable调用invalidateSelf绘制新的一帧，从这里我们看出渲染一帧与解码一帧是在串行的，那么是否存在渲染与解码分开并行的优化方案，framesequence应运而生。

# Gif加载优化
[animated-drawable-integration](https://github.com/electrolyteJ/animated-drawable-integration)实现了采用framesequence方案加载Gif的代码。FrameSequenceDrawable调用start之后会在内部创建一个名为FrameSequence decoding thread的HandlerThread线程，用来解码Gif到一个mBackBitmap，当触发了Drawable的draw方法，mBackBitmap会于用于渲染的mFrontBitmap进行swap，并且解码线程会继续解码到mBackBitmap，等待下一次的swap，这样就实现了渲染与解码流程分开，提高了Gif渲染的流畅性。

# Webp/AVIF动图
Gile 在Android P+使用了基于ImageDecoder的解码器，目前该解码器主要用来解码Android P+平台的Webp与Android S+平台的AVIF
```java
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
      registry.append(
          Registry.BUCKET_ANIMATION,
          InputStream.class,
          Drawable.class,
          AnimatedImageDecoder.streamDecoder(imageHeaderParsers, arrayPool));
      registry.append(
          Registry.BUCKET_ANIMATION,
          ByteBuffer.class,
          Drawable.class,
          AnimatedImageDecoder.byteBufferDecoder(imageHeaderParsers, arrayPool));
    }
```
ImageDecoder也是采用渲染与解码分开的方案，当数据解码时会通过OnHeaderDecodedListener#onHeaderDecoded回调一帧的信息ImageInfo，继而能让我们根据设备条件、app内存情况等信息将真实的Bitmap decode 为另外一个Bitmap

# 图片网络请求优化

1. 图片的下载占用时间较多的往往是io，而cpu常常处于等待阶段，基于此我们可以优化网络请求库的请求池，采用2*cpu + 1
```java
@GlideModule(glideName = "HomeGlide")
class HomeModule : LibraryGlideModule() {

    val okhttpClient = OkHttpClient.Builder()
        .dispatcher(Dispatcher(ThreadUtil.getIOPool()))//默认任务分发池，最多并发请求为64个，每个host最多5个，线程池最大为无线个，对于低端手机能不能根据cpu来控制线程核心数，优化图片加载任务分发池最大线程数为2*cpu+1
        .connectTimeout(15_000, TimeUnit.MILLISECONDS)//15s
        .readTimeout(15_000, TimeUnit.MILLISECONDS)//
        .writeTimeout(15_000, TimeUnit.MILLISECONDS)//
        .connectionPool(ConnectionPool(5, 10_000, TimeUnit.MILLISECONDS))//空闲5个，保活10s
        .addInterceptor { chain ->//应用层的拦截器
            return@addInterceptor chain.proceed(chain.request())
        }.build()

    override fun registerComponents(context: Context, glide: Glide, registry: Registry) {
        registry.apply {
            //替换默认的HttpGlideUrlLoader，使用Okhttp网络库并且优化任务分发池与连接池
            replace(
                GlideUrl::class.java, InputStream::class.java, OkHttpUrlLoader.Factory(okhttpClient)
            )
            //处理Glide.load(Photo对象)
            append(
                Photo::class.java, InputStream::class.java, HomeGlideUrlModuleLoader.Factory()
            )
        }
    }
}
```
2. 图床的服务器一般都是配置了url带参数进行图片裁剪，比如`"${model.uri}?w=${width}&h=${height}&q=${model.quality}"`根据各个设备上面需要的宽高下发图片，对于磁盘缓存、内存缓存都可以减压