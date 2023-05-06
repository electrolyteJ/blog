---
layout: post
title: Android | AOSP 新的构建系统Soong
description: 使用Blueprint语言描述编译过程
tag:
- build-tools
- android
---

Blueprint+Soong这套构建工具将替代老的构建工具MakeFile+kati,想要认识MakeFile+kati的话可以参考这一篇文章[AOSP项目的构建工具GNU make(kati)]({{site.baseurl}}/2017-10-22/build-tools-gnumake)，这里简单说一下他们的关系和区别。

kati基于make构建系统为Android定制的构建系统，kati将Makefile文件转换成Ninja files，然后用Ninja编译，而Soong是把Blueprint文件转换为Ninja文件。

Soong是一种替代make构建系统的方案,它不在识别解析Android.mk文件，而是替换成Android.bp文件。

Buleprint是一个元构建系统，用于读取Buleprint文件（描述需要被编译的模块有哪些）和生成一个Ninja manifest（描述编译时的一些指令和有哪些依赖文件，绝大多数的构建系统使用內建规则或者DSL去描述模块转换成构建规则的逻辑，但是Buleprint代替了它，用Go语言编写的构建逻辑去per-oroject。Blueprint使用的是同bazel一样的语言BUILD，BUCK也是来源于bazel。


# 参考资料

[翻译 | 使用 Soong 来进行 Android 模块的构建](http://www.10tiao.com/html/685/201704/2649516116/1.html)

[Android7.0 Ninja编译原理](http://blog.csdn.net/chaoy1116/article/details/53063082)

[Soong Build System](https://source.android.com/docs/setup/build)

[LineageOS/android_build_soong](https://github.com/LineageOS/android_build_soong)

[ninja](https://github.com/ninja-build/ninja)
