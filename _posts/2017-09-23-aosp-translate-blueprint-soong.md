---
layout: post
title: 翻译AOSP/AOSP(SYS) --- 新的构建系统
description: 使用Blueprint语言描述编译过程
date: 2017-9-23
share: true
comments: true
tag:
- Build Tools
- Translation
- AOSP(SYS)
---
## *1.Summary*{:.header2-font}
&emsp;&emsp;想法简单就是想练练翻译水平。正好用看到这么一篇文章[翻译 | 使用 Soong 来进行 Android 模块的构建](http://www.10tiao.com/html/685/201704/2649516116/1.html)，所以自己也来试试。
## *2.About*{:.header2-font}
Blueprint、Soong这套编译工具将替代老的构建工具make、kati

## *3.Intoduction*{:.header2-font}

使用kati将Makefile文件转换成Ninja files，然后用Ninja编译
使用Soong是用于一起把Blueprint文件转换为Ninja文件

## *4.Reference*{:.header2-font}
[翻译 | 使用 Soong 来进行 Android 模块的构建](http://www.10tiao.com/html/685/201704/2649516116/1.html)
[Android7.0 Ninja编译原理](http://blog.csdn.net/chaoy1116/article/details/53063082)
