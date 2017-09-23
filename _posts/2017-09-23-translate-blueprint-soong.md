---
layout: post
title: Android源码解析之AOSP新的编译系统
description: 翻译AOSP
author: 未知
date: 2017-09-23
share: true
comments: true
tag:
- build system
---
## *1.Summary*{:.header2-font}
&emsp;&emsp;想法简单就是想练练翻译水平。正好用看到这么一篇文章[翻译 | 使用 Soong 来进行 Android 模块的构建](http://www.10tiao.com/html/685/201704/2649516116/1.html)，所以自己也来试试。
## *2.About*{:.header2-font}

## *3.Intoduction*{:.header2-font}

使用Kati将makefile文件转换成Ninja files，然后用Ninja编译
Blueprint和Soong是用于一起把Blueprint文件转换为Ninja文件

## *4.Reference*{:.header2-font}
[翻译 | 使用 Soong 来进行 Android 模块的构建](http://www.10tiao.com/html/685/201704/2649516116/1.html)
[Android7.0 Ninja编译原理](http://blog.csdn.net/chaoy1116/article/details/53063082)
