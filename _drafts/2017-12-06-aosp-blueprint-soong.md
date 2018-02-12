---
layout: post
title: 【翻译】 新的构建系统
description: 使用Blueprint语言描述编译过程
date: 2017-12-06
share: true
comments: true
tag:
- Build Tools
- Translation
---
## *1.Summary*{:.header2-font}
&emsp;&emsp;想法简单就是想练练翻译水平。正好用看到这么一篇文章[翻译 | 使用 Soong 来进行 Android 模块的构建](http://www.10tiao.com/html/685/201704/2649516116/1.html)，所以自己也来试试。
## *2.About*{:.header2-font}
Blueprint+Soong这套构建工具将替代老的构建工具make+kati,想要认识make+kati的话可以参考这一篇文章[AOSP(SYS) --- 构建工具GNU make]({{site.baseurl}}/blog/2017-10-22/2017-10-22-aosp-build-tools-gnumake)。这里简单说一下他们的关系和区别。使用kati将Makefile文件转换成Ninja files，然后用Ninja编译，而Soong是把Blueprint文件转换为Ninja文件。而make和Buleprint都用用于解析它们自己的格式文件。make对应Makefile语言，Blueprint使用的是同bazel一样的语言BUILD，就连BUCK也是来源于bazel
## *3.Intoduction*{:.header2-font}
### *3.1 Blueprint*{：.header3-font}
build/blueprint/README.md

Buleprint是一个元构建系统，用于读取Buleprint文件（描述需要被编译的模块有哪些）和生成一个Ninja manifest（描述编译时的一些指令和有哪些依赖文件）。绝大多数的构建系统使用內建规则或者DSL去描述模块转换成构建规则的逻辑，但是Buleprint代理它，用Go语言编写的构建逻辑去per-oroject.当项目允许个别的容易修改的模块的简单变化去理解Buleprint文件时，项目是允许构建逻辑的层次复杂性去保留高级语言

### *3.2 Soong*{:.header3-font}
build/soong/README.md

Soong是一种替代基于make构建系统的方案。它将Android.mk文件替换成Android.bp文件，Android.bp文件是一种



## *4.Reference*{:.header2-font}
[翻译 | 使用 Soong 来进行 Android 模块的构建](http://www.10tiao.com/html/685/201704/2649516116/1.html)
[Android7.0 Ninja编译原理](http://blog.csdn.net/chaoy1116/article/details/53063082)
