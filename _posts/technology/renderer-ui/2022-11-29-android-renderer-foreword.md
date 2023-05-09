---
layout: post
title: Android | Android渲染器前言
description:  android renderer
tag:
- android
- renderer-ui
---
* TOC
{:toc}


在Android中存在两棵树一个View树，一个Layer树，前者用来存储xml树信息，后者用来作为硬件加速的树。Android使用图形库OpenGL ES、Vulkan、Skia绘制树所描述的ui信息，在软件绘制的时候使用Skia库，在硬件绘制的时候使用Skia、OpenGL ES、Vulkan混合使用(OpenGL ES、Vulkan作为后端)，为了优化Android平台的绘制流程度，引进了垂直信号和三级缓存。

接下来我们将要学习的内容有如下：

- [x] [Xml、View、RenderNode三棵树]({{site.baseurl}}/2022-03-22/android-renderer-three-trees)
- [x] [再谈Android View树]({{site.baseurl}}/2022-05-08/android-renderer-viewtree)
- [x] [Android绘制]({{site.baseurl}}/2022-11-29/android-renderer-draw)
- [x] [渲染优化：垂直信号 、三级缓存]({{site.baseurl}}/2022-05-08/android-renderer-vsync-triplebuffer)

# *工程结构*

- AOSP项目结构
    - frameworks/base/opengl/java : opengl java接口
    - frameworks/base/core/java/android/view : view树
    - frameworks/base/graphics ：graphics java接口
    - frameworks/base/libs/hwui : 硬件加速、渲染线程
    - frameworks/native/opengl : opengl native接口
    - frameworks/native/vulkan : vulkan接口


# *参考资料*
[从架构到源码：一文了解Flutter渲染机制](https://developer.aliyun.com/article/770384)