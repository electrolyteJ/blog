---
layout: post
title: 图像 | Glide设计
description: 缓存设计、Fetch数据源设计、解码设计
author: 电解质
tag: 
- image
- android
---
* TOC
{:toc}

![image]({{site.baseurl}}/asset/image/glide.png){:.center-image}*`Glide`*

Glide的设计灵感部分借鉴了square的picasso的设计思想，并且做了扩展和增强，他们都将Bitmap、Drawable等都看成资源Resource，通过Uri、File等`Model`发送请求获取数据到`Data`，Data数据可以从从内存、磁盘、网络加载，在解码过程对资源进行了transform 、transcode等操作最后变成`Resource`


从图中我们先从缓存开始，内存与磁盘缓存都有两级，缓存获取的路径 `ActiveResources(EngineKey) -> LruResourceCache(EngineKey) -> DiskLruCache(ResourceCacheKey -> DiskLruCache(DataCacheKey)`，缓存的key表示了缓存资源的特性，EngineKey表示资源宽高、transform 、transcode、optioin等值，ResourceCacheKey表示资源的宽高、transformation、options等值，DataCacheKey基本表示了原图，未经处理的资源。

# 内存缓存

内存缓存ActiveResources、LruResourceCache，他们的key都为EngieKey。
```java
//经过transform、转码、option过处理的图片
class EngineKey implements Key {
    ...
  @Override
  public int hashCode() {
    if (hashCode == 0) {
      hashCode = model.hashCode();
      hashCode = 31 * hashCode + signature.hashCode();
      hashCode = 31 * hashCode + width;
      hashCode = 31 * hashCode + height;
      hashCode = 31 * hashCode + transformations.hashCode();
      hashCode = 31 * hashCode + resourceClass.hashCode();
      hashCode = 31 * hashCode + transcodeClass.hashCode();
      hashCode = 31 * hashCode + options.hashCode();
    }
    return hashCode;
  }
  ...
}
```

ActiveResources采用HashMap存储资源的软引用，当gc触发回收时，这块缓存会最先被回收，LruResourceCache采用LRU算法管理内存，资源占用内存size是其回收的策略，而不是根据数量。LruResourceCache的回收资源的阈值是根据app内存情况动态计算获取的。
```java
    if (targetMemoryCacheSize + targetBitmapPoolSize <= availableSize) {
      memoryCacheSize = targetMemoryCacheSize;
      bitmapPoolSize = targetBitmapPoolSize;
    } else {
      float part = availableSize / (builder.bitmapPoolScreens + builder.memoryCacheScreens);
      memoryCacheSize = Math.round(part * builder.memoryCacheScreens);
      bitmapPoolSize = Math.round(part * builder.bitmapPoolScreens);
    }

```
- targetMemoryCacheSize(两张全屏幕的大图)：targetMemoryCacheSize的值默认等于两块屏幕占用的内存
- targetBitmapPoolSize(bitmap池子大小)：在开启硬件加速的android O+的targetBitmapPoolSize大小等于一块屏幕占用的内存，在android O以下等于四块屏幕占用的内存。
- availableSize(app可用内存)：可用内存大小 = app堆内存(低内存缩小0.33倍，高内存缩小0.4倍) - 减去数组池大小(在低内存设备(包括android 4.3以下和部分4.4以上的机器)中 数组池(字节或者整型)的容量为2MB，高内存则为4MB)

当可用内存大于bitmap池子+targetMemoryCacheSize,那么内存缓存的大小等于targetMemoryCacheSize，反之，内存缓存不太足够时，内存缓存会对可用内存进行等分，要么在开启硬件加速的设备2/3(1+2），要么在没有开启的设备 2/6(4+2)等分。

知道了LruResourceCache最大值，那么当LruResourceCache容器存储的资源size触顶之后就会回收最近最少被使用的资源。

内存缓存策略，作用于LruResourceCache 与 BitmapPool
```java
public enum MemoryCategory {
  /**
   * Tells Glide's memory cache and bitmap pool to use at most half of their initial maximum size.
   */
  LOW(0.5f),
  /** Tells Glide's memory cache and bitmap pool to use at most their initial maximum size. */
  NORMAL(1f),
  /**
   * Tells Glide's memory cache and bitmap pool to use at most one and a half times their initial
   * maximum size.
   */
  HIGH(1.5f);

  private final float multiplier;
  ...
}
```

# 磁盘缓存

磁盘也有两级缓存分别为使用ResourceCacheKey和DataCacheKey的DiskLruCache,使用ResourceCacheKey的DiskLruCache在ResourceCacheGenerator迭代器获取，使用DataCacheKey在DataCacheGenerator迭代器获取

```java
//经过transform、option过处理的图片
final class ResourceCacheKey implements Key {
    ...
      @Override
  public int hashCode() {
    int result = sourceKey.hashCode();
    result = 31 * result + signature.hashCode();
    result = 31 * result + width;
    result = 31 * result + height;
    if (transformation != null) {
      result = 31 * result + transformation.hashCode();
    }
    result = 31 * result + decodedResourceClass.hashCode();
    result = 31 * result + options.hashCode();
    return result;
  }
    ...
}
//未经过处理的图片
final class DataCacheKey implements Key {
    ...
      @Override
    public int hashCode() {
        int result = sourceKey.hashCode();
        result = 31 * result + signature.hashCode();
        return result;
    }
    ...
}  

```
DiskLruCache缓存数据都在File中，读取File的loader有如下
```java
        .append(File.class, ByteBuffer.class, new ByteBufferFileLoader.Factory())
        .append(File.class, InputStream.class, new FileLoader.StreamFactory())
        .append(File.class, File.class, new FileDecoder())
        .append(File.class, ParcelFileDescriptor.class, new FileLoader.FileDescriptorFactory())
        // Compilation with Gradle requires the type to be specified for UnitModelLoader here.
        .append(File.class, File.class, UnitModelLoader.Factory.<File>getInstance())
```
ResourceCacheGenerator和DataCacheGenerator迭代器都会遍历上面的loader，将缓存从File中读取到数据源(Data)中，数据源在被读取到 `decode --> transform -> encode --> transcode`。如果缓存没能从ResourceCacheGenerator与DataCacheGenerator两个迭代器获取，那么会从缓存的源头读取，接下来就执行SourceGenerator迭代器，这类loader有如下
```java
//从网络读取
registry.replace(GlideUrl.class, InputStream.class, new OkHttpUrlLoader.Factory());
//从assets获取
        .append(Uri.class, InputStream.class, new AssetUriLoader.StreamFactory(context.getAssets()))
        .append(
            Uri.class,
            AssetFileDescriptor.class,
            new AssetUriLoader.FileDescriptorFactory(context.getAssets()))

```

讲到这里其实已经不是属于缓存了，而是数据的fetch读取源数据过程,接下来我们展开讲讲


磁盘缓存策略
```java
public abstract class DiskCacheStrategy {
    public static final DiskCacheStrategy ALL =...
    public static final DiskCacheStrategy NONE =...
      public static final DiskCacheStrategy DATA =...
      public static final DiskCacheStrategy RESOURCE =...
}
```
# Bitmap 与 Array 缓存
Bitmap在内存中也是一块巨大的开销，所以Bitmap需要被缓存池管理起来方便复用。LruBitmapPool的池大小在app可用内存充足的情况下且Android N以下设备为开启硬件加速相当于四张全屏幕的大图占用的内存，其默认的策略在Android 4.4+用SizeConfigStrategy，以下用AttributeStrategy。


Bitmap下采样的策略
```java
public abstract class DownsampleStrategy {
  public static final DownsampleStrategy AT_LEAST = new AtLeast();

  public static final DownsampleStrategy AT_MOST = new AtMost();

  public static final DownsampleStrategy FIT_CENTER = new FitCenter();

  public static final DownsampleStrategy CENTER_INSIDE = new CenterInside();

  public static final DownsampleStrategy CENTER_OUTSIDE = new CenterOutside();

  public static final DownsampleStrategy NONE = new None();

  public static final DownsampleStrategy DEFAULT = CENTER_OUTSIDE;
}
```
在Gilde中如果ImageView没有提供具体的宽高，那么就不会进行scale调整Bitmap，直接进行原图加载。Bitmap的下采样主要是针对外部定义了ImageView的宽高才能进行。

# 扩展性

## Fetcher设计

可定制：Loader/Fetcher Model 为 Data


源数据的获取主要是通过Model，Uri、Url、File、Asset Folder等，在`api "com.squareup.okhttp3:okhttp:${OK_HTTP_4_VERSION}"`库中使用了Okhttp Fetcher拉取数据，Glide具备Fetcher的扩展性，外部只要继承`ModelLoader<GlideUrl, InputStream> ` 与 `DataFetcher<InputStream>` 并且在注册中心映射Model与Data的关系标明数据从GideUrl服务器流到InputStream,，Glide库就能在需要使用的时候去注册中心找到对应的类。

## Decode设计

下面三个地方都是可定制的

- Data 使用ResourceDecoder 解码为 Resource
- Resource transform为 Resource
- 使用ResourceEncoder编码Resource(Bitmap重新编码为更小的Bitmap) 或者 Data(ByteBuffer编码到File)
- Resource 使用ResourceTranscoder转码为Transcode

比如，SVG资源如何转换为Android平台的Drawable类 ？通过 继承`ResourceDecoder<InputStream, SVG>`并且进行资源的转码


## Target设计

Glide通过外部继承CustomViewTarget类实现Android View绘制具体的资源，内部监听ViewTreeObserver.OnPreDrawListener#onPreDraw开始绘制才会触发资源做加载请求，真正做到按需加载。

<!-- ## 资源流的预加载 -->