---
layout: post
title: 图像 | 前言
description: 图像处理
author: 电解质
tag: 
- image
- android
---
* TOC
{:toc}

# Color(色彩的世界)
## Color Space(色域)
pc中三种色域
sRGB < NTSC < Adobe RGB
- sRGB：
- NTSC
- Adobe RGB

## Color Depth(色彩深度)

色深：单位像素带颜色的bit数量，只计算rgb的总和。

transparency透明度，translucency半透明,opacity不透明度

color depth(bit depth)|Bitmap | 内存占用大小|能存储颜色的数量
---|---|---|---
.|ALPHA_8 |每个像素使用1byte存储translucency(alpha)|256色|
12 bit|ARGB_4444|每个像素使用2个字节存储ARGB  | 16 * 16 * 16 = 4096色
16 bit|RGB_565(This configuration can produce slight visual artifacts depending on the configuration of the source) | 每个像素使用2个字节存储RGB   |32,64,32
24 bit(true color)|ARGB_8888|每个像素使用4个字节存储ARGB  | 256 * 256 * 256 = 16,777,216色
30 bit(deep color)|RGBA_1010102(This configuration is suited for wide-gamut and HDR content which does not require alpha blending, such that the memory cost is the same as ARGB_8888 while enabling higher color precision.)|...|每个像素使用4个字节(32bits)存储|...
.|RGBA_F16(suited for wide-gamut and HDR content.) |每个像素使用8个字节存储ARGB  |...

手机显示器常见的色深就是上面表格罗列的，电脑显示器的色深有rgb_888 / rgb_101010

> 抖8：本身不是8bit通过软件算法达到8bit

# Format(封装色彩)
图片的格式存在raster和vector，在Android中可以通过Drawable加载raster格式，用VectorDrawable加载vector格式
## Raster formats
- JPEG/JFIF
- JPEG 2000
- Exif
- TIFF
- GIF
- BMP
- PNG
- PPM, PGM, PBM, and PNM
- WebP
- ....
- psd

## Vector formats
- SVG
- .dwg(3d)

## Transform
主要通过矩阵Matrix(3x3),分为三种操作队列的方式，pre、post、set。pre是插入到队列头，post是插入到队列尾部，set会清空队列，然后放入当前新的transform。

transform方式有
- rotate
- skew
- translate
- scale
- concat


# 应用-图片适配屏幕：

矢量图相比于栅格图是一种scalability之后不会loss显示质量的图，这意味着对于不同分辨率的屏幕，同一个文件resize之后不会loss图片的显示质量，在屏幕适配这一块来说是一种优势

Android提供三种源可转化成vector drawable
- material icon
- svg
- psd



format|compression/palettes|
---|---
BMP |Lossless / Indexed and Direct
GIF | Lossless / Indexed only
JPEG | Lossy / Direct
PNG-8(Alpha) | Lossless / Indexed
PNG-24(RGB_888) | Lossless / Direct
PNG-32(ARGB_8888)|
SVG | Lossless / Vector

> Palettes(different colour depths) : indexed color(size=256)和direct color(size=thousands of colors)



# 图库：Picasso vs. Glide vs. Fresco
![image]({{site.baseurl}}/asset/image/picasso.png){:.center-image}*`Picasso`*

![image]({{site.baseurl}}/asset/image/glide.png){:.center-image}*`Glide`*

# *参考资料*

[关于显示器的颜色深度、色域、HDR，以及它们的关系和区别](https://kejiweixun.com/blog/explain-display-color-depth-color-space-hdr/)