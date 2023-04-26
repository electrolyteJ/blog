---
layout: post
title: Android ART | java家族与c家族的编译器
description:  编译器前端与后端
tag:
- inverse-engineering
- vm-language
- android
---
* TOC
{:toc}

java家族有java、kotlin、groovy等，而c家族有c、cpp、objective c/c++等,java家族的编译器有javac、kotlinc等，c家族编译器有gcc、llvm等，而编译器前端与编译器后端还出现了一些著名且影响很广的项目clang、gas、smali，让我们先从编译器的前端开始这趟路程。

java家族与c家族编译器的工作流程

- javac/kotlinc: `java/kotlin(高级语言)--->语法解析---> 字节码(二进制文件.class or .dex)`
- gcc/llvm: `cpp(高级语言)--->语法解析--->汇编(低级语言)---> 机器码(二进制文件elf)`

编译器分为前端和后端，前端主要是对源代码语法的处理，转换成语法树，后端则是关注字节码或者机器码的生成。开源项目llvm的clang项目就是编译器前端，是c家族语法的解析，而llvm项目早期主要是聚集在编译器后端，处理x86、arm等指令，只不过随着项目壮大clang、lld等项目产生逐渐变成一个构建编译器的工具箱。

# *kotlin编译*

## 编译流程

kotlin源代码 --> 词法分析器 --> Token流 --> 语法分析器 --> 语法树/抽象语法树 -->语义分析器 --> 注解抽象语法树 --> 字节码生成器 ---> JVM字节码

1. 词法分析器：使用JFlex开源库，_JetLexer(KotlinLexer)代表词法分析器
2. 语法分析器(syntax parser)：使用InteliJ项目中的PsiParser(KotlinParser),并且生成AST
3. 语义分析(semantic analyzer)：检查AST 上下文相关属性，并且生成中间代码。org.jetbrains.kotlin.resolve包下为语义分析，org.jetbrains.kotlin.ir包下为中间代码生成
4. 目标代码生成：org.jetbrains.kotlin.codegen

## 编译器前端与后端

- 编译前端： build syntax tree and semantic info
- 编译后端： generates target/machine code

```kotlin
/**
 *                      frontend
 * source code --> [ parser  -- syntax tree ---> semantic analyzer ] -- syntax tree + semantic info -->
 *       backend
 * -->  [intermediate code:generator & optimizer -- intermediate representation --> machine code:generator & optimizer ] -- target/machine code-->
 *
 * kotlin在编译后端自动生成set/get代码(PropertyCodegen)，修改类为final
 */
```

# *汇编器Smali/GAS*

什么是[汇编语言](https://en.wikipedia.org/wiki/Assembly_language) : 一种相对于高级语言最接近机器语言的低级语言，所以性能毋庸置疑，开发效率低。编译成机器码的汇编器有GAS(即GNU AS汇编编译器，基于AT&T syntax指令，生成.s文件)、NASM(基于Intel syntax指令，生成.asm文件)、MASM(Windows平台下的汇编编译器，也使用Intel风格),机器码的汇编语言风格有Intel和AT&T之分，编译成Java字节码的汇编器有Jasmin和Smali。Smali是anroid虚拟机字节码的汇编器，GAS是android机器码的汇编器

## Smali

如果你遇到没有源码的应用，又要对其进行修改，那么会使用Smali的汇编指令就很有必要了，而在没办法修改源代码，通过修改字节码（或者机器码）对应的反汇编代码，去改变应用逻辑的做法，就叫做插桩，属于静态二进制插桩(gralde transform也属于静态二进制插桩，inline hook属于动态二进制插桩)。哪些工作内容会用到插桩这门技术呢? 可以看一下这篇文章[基于原厂ROM移植MIUI](http://www.miui.com/thread-409543-1-1.html)。

想要了解更多关于Smali就要具有一定知识储备。

- 什么是[Jasmin](http://jasmin.sourceforge.net/about.html) ：jasmin是一款针对官方Java虚拟机（JVM）的汇编器。``.j <---> .class``
- 什么是[Smali](https://github.com/JesusFreke/smali/wiki) : smali是一款针对Android平台JVM(Dalvik)的汇编器。 ``.smali <---> .dex`` 。其已经被开源到AOSP的external/smali目录下，但是由于中国的环境，没办法轻松获取到这个工具集，google已经将其开源到github上面了，并由google工程师Ben Gruver负责。

了解了这些内容，就可以简单的判断smali就是一款用于Dalvik虚拟机的汇编器，其反汇编器叫做baksmali，所以apktool其实是smali/baksmali的封装，兼具汇编和反汇编的功能。并且smali汇编器的语法是基于jasmin汇编器的语法。那为什么两者的语法却有点不同 ？ 最终归结于虚拟机的不同导致的，官方虚拟机是基于内存中的堆栈实现，而Dalvik虚拟机是基于cpu的寄存器实现，但是jasmin的汇编语言理念被保留了下来。

- 数据类型、类的字段（field）和方法（method）定义：可以查看官方提供的[链接](https://github.com/JesusFreke/smali/wiki/TypesMethodsAndFields)
- 用来存放数据的寄存器，可以查看官方提供的[链接](https://github.com/JesusFreke/smali/wiki/Registers)
- 用于操作数据的内置方法instructions(也叫做opcode mnemonics)
    - [第一手资料](https://source.android.com/devices/tech/dalvik/dalvik-bytecode)
    - [第二手资料](http://pallergabor.uw.hu/androidblog/dalvik_opcodes.html)
    - [好几手资料](http://www.jianshu.com/p/80d22f66e042)
- 关于[注释](http://blog.csdn.net/junjunyanyan/article/details/45726775)

## GAS

- [GAS](https://tldp.org/HOWTO/Assembly-HOWTO/gas.html)
- [Using as](http://sourceware.org/binutils/docs/as/index.html)

# *参考*

[Professional Assembly Language](http://blog.hit.edu.cn/jsx/upload/AT%EF%BC%86TAssemblyLanguage.pdf)

[[Quora]What is smali in Android ? ](https://www.quora.com/What-is-smali-in-Android)

[llvm](https://llvm.org/)

[Kotlin 源代码编译过程分析](https://developer.aliyun.com/article/662337)

[k2视频讲述](https://blog.jetbrains.com/zh-hans/kotlin/2021/10/the-road-to-the-k2-compiler/)

[GCC 汇编分析](http://blog.ccyg.studio/article/6afa7afe-3312-4bc9-99aa-af1256e5db5b/#hello-world)

[ARM Assembly By Example](https://armasm.com/docs/getting-to-hello-world/basics/)

[C语言与汇编混合编程](https://blog.csdn.net/AllenWells/article/details/47422011?spm=1001.2014.3001.5502)
