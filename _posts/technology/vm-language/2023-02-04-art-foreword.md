---
layout: post
title: Android ART |  前言
description:  新一代Android虚拟机ART
tag:
- vm-language
- android
---

Android 5之后全面切换到了新的虚拟机ART，这是一款既支持JIT编译也能AOT编译的java虚拟机。

之后我们将要学习的内容有如下：

- [x] [AppRuntime与Runtime 启动]({{site.baseurl}}/2023-02-05/art-runtime-startup)
- [x] [java家族与c家族的编译器]({{site.baseurl}}/2023-02-01/art-compiler1)
- [ ] [Dex to Oat 编译]({{site.baseurl}}/2023-02-01/art-compiler2)
- [ ] [ART GC]({{site.baseurl}}/2023-02-05/art)

## *ART工程结构*

- dex2oat: 字节码转机器码
- compiler：字节码编译成机器码的编译器
- runtime:执行机器码(oat文件)或者字节码(dex文件)的虚拟机，支持AOT编译与JIT编译
    - entrypoints：函数执行入口
    - native：java类jni方法的native代码，比如java类Object的所有jni方法在java_lang_Object.cc文件中
    - mirror：java类在cpp中的映射类，比如java Class类在mirror文件中对应是cpp Class
    - interpreter：解释器
    - gc:垃圾回收器
- oatdump/dexdump：oat(elf格式)与dex文件的dump
- libexfile/libelffile:操作dex文件与elf文件的库
- tools
    - dexanalyze
    - dexfuzz
    - jfuzz
    - signal_dumper
- ...