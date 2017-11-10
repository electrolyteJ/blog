---
layout: post
title: Smali语言（1）
description: 这是一篇了解什么是Smali，学会Smali能做什么的文章。
author: 未知
date: 2017-04-16
share: true
comments: true
tag:
- Smali
- Assembler/Disassember
---
## *1.Summary*{:.header2-font}
&emsp;&emsp;如果你遇到没有源码的应用，又要对其代码进行修改，那么会使用Smali这门汇编语言就很有必要了。而在没办法修改源代码，通过修改字节码（或者机器码）对应的反汇编代码，去改变应用逻辑的做法，就叫做插桩。那些工作内容会用到插桩这门技术呢? 可以看一下这篇文章[基于原厂ROM移植MIUI](http://www.miui.com/thread-409543-1-1.html)。

## *2.About*{:.header2-font}
&emsp;&emsp;想要了解更多关于Smali语言就要具有一定知识储备。

- 什么是[汇编语言](https://en.wikipedia.org/wiki/Assembly_language) : 一种相对于高级语言最接近机器语言的低级语言，所以性能毋庸置疑，开发效率低。编译成机器码的汇编器有GAS和NASM，编译成Java字节码的汇编器有Jasmin和Smali。而汇编语言风格又有Intel和AT&T之分。
- 什么是[Jasmin](http://jasmin.sourceforge.net/about.html) ：jasmin是一款针对官方Java虚拟机（JVM）的汇编器。``.j <---> .class``
- 什么是[Smali](https://github.com/JesusFreke/smali/wiki) : smali是一款针对Android平台JVM(Dalvik)的汇编器。 ``.smali <---> .dex`` 。其已经被开源到AOSP的external/smali目录下，但是由于中国的环境，没办法轻松获取到这个工具集。google已经将其开源到github上面了，并由google工程师Ben Gruver负责。

&emsp;&emsp;了解了这些内容，就可以简单的判断smali就是一款用于Dalvik虚拟机的汇编器，其反汇编器叫做baksmali，所以apktool其实是smali/baksmali的封装，兼具汇编和反汇编的功能。并且smali汇编器的语法是基于jasmin汇编器的语法。那为什么两者的语法时却有点不同 ？ 最终归结于虚拟机的不同导致的，官方虚拟机是基于内存中的堆栈实现，而Dalvik虚拟机是基于寄存器实现。但是jasmin语言的理念被保留了下来。

## *3.Introduction*{:.header2-font}
资料看完了，有空再来填坑。

- 数据类型、类的字段（field）和方法（method）定义：可以查看官方提供的[链接](https://github.com/JesusFreke/smali/wiki/TypesMethodsAndFields)
- 用来存放数据的寄存器，可以查看官方提供的[链接](https://github.com/JesusFreke/smali/wiki/Registers)
- 用于操作数据的内置方法instructions(也叫做opcode mnemonics)
[第一手资料](https://source.android.com/devices/tech/dalvik/dalvik-bytecode)
[第二手资料](http://pallergabor.uw.hu/androidblog/dalvik_opcodes.html)
[好几手资料](https://smalinuxer.github.io/2015/12/07/smali-base-1.html#post__title) 
[好几手资料](http://www.jianshu.com/p/80d22f66e042)
- 关于[注释](http://blog.csdn.net/junjunyanyan/article/details/45726775)




## *4.Reference*{:.header2-font}
[Professional Assembly Language](http://blog.hit.edu.cn/jsx/upload/AT%EF%BC%86TAssemblyLanguage.pdf)
[[Quora]What is smali in Android ? ](https://www.quora.com/What-is-smali-in-Android)
