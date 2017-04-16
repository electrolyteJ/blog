---
layout: post
title: Android源码解析之Smali语言（1）
description: 这是一篇了解是什么Smali，学会Smali能做什么的初学者文章。
author: 未知
date: 2017-04-16
share: true
comments: true
tag:
- Smali
- Assembler/Disassember
---
## *1.Summary*{:.header2-font}
&emsp;&emsp;如果你遇到没有源码的应用，又要对其代码进行修改，那么会使用Smali这门汇编语言就很有必要了。而在没办法修改源代码，通过修改字节码（或者机器码）对应的反汇编代码，去改变应用逻辑的做法，就叫做插桩。那些工作内容会用到插桩这门技术呢? 可以看一下这篇文章[基于原厂ROM移植MIUI]](http://www.miui.com/thread-409543-1-1.html)。

## *2.About*{:.header2-font}
&emsp;&emsp;想要了解更多关于Smali语言就要具有一定知识储备。

- 什么是[汇编语言](https://en.wikipedia.org/wiki/Assembly_language) : 一种相对于高级语言最接近机器语言的低级语言，所以性能毋庸置疑，开发效率低。编译成机器码的汇编器有GAS和NASM，编译成Java字节码的汇编器有Jasmin和Smali。而汇编语言风格又有Intel和AT&T之分。
- 什么是[Jasmin](http://jasmin.sourceforge.net/about.html) ：jasmin是一款针对官方Java虚拟机（JVM）的汇编器。``.j <---> .class``
- 什么是[Smali](https://github.com/JesusFreke/smali/wiki) : smali是一款针对Android平台JVM(Dalvik)的汇编器。 ``.smali <---> .dex`` 。其已经被开源到AOSP的external/smali目录下，但是由于中国的环境，没办法轻松获取到这个工具集。google已经将其开源到github上面了，并由google工程师Ben Gruver负责。

&emsp;&emsp;了解了这些内容，就可以简单的判断smali就是一款用于Dalvik虚拟机的汇编器，其反汇编器叫做baksmali，所以apktool其实是smali/baksmali的封装，兼具汇编和反汇编的功能。并且smali汇编器的语法是基于jasmin汇编器的语法。那为什么两者的语法时却有点不同 ？ 最终归结于虚拟机的不同导致的，官方虚拟机是基于内存中的堆栈实现，而Dalvik虚拟机是基于寄存器实现。但是jasmin语言的理念被保留了下来。所以我们先从汇编理念开始学习。

## *3.Introduction*{:.header2-font}
### *定义字段*{:.header3-font}
.field \<access-spec> \<field-name> \<descriptor> [ = <value> ]

eg: ``.field public static final VERSION_NAME:Ljava/lang/String; = "1.0"``

- \<access-spec> : public, private, protected, static, final, volatile, transient 
- \<field-name>  ：字段名
- \<descriptor>  : 字段类型

<style type="text/css">
.tg  {border-collapse:collapse;border-spacing:0;border-color:#aaa;}
.tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:#aaa;color:#333;background-color:#fff;}
.tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:#aaa;color:#fff;background-color:#f38630;}
.tg .tg-yw4l{vertical-align:top}
</style>
<table class="tg">
  <tr>
    <th class="tg-yw4l">V</th>
    <th class="tg-yw4l">void - can only be used for return types</th>
  </tr>
  <tr>
    <td class="tg-yw4l">Z</td>
    <td class="tg-yw4l">boolean</td>
  </tr>
  <tr>
    <td class="tg-yw4l">B</td>
    <td class="tg-yw4l">byte</td>
  </tr>
  <tr>
    <td class="tg-yw4l">S</td>
    <td class="tg-yw4l">short</td>
  </tr>
  <tr>
    <td class="tg-yw4l">C</td>
    <td class="tg-yw4l">char</td>
  </tr>
  <tr>
    <td class="tg-yw4l">I</td>
    <td class="tg-yw4l">int</td>
  </tr>
  <tr>
    <td class="tg-yw4l">J</td>
    <td class="tg-yw4l">long (64 bits)</td>
  </tr>
  <tr>
    <td class="tg-yw4l">F</td>
    <td class="tg-yw4l">float</td>
  </tr>
  <tr>
    <td class="tg-yw4l">D</td>
    <td class="tg-yw4l">double (64 bits)</td>
  </tr>
  <tr>
    <td class="tg-yw4l">[</td>
    <td class="tg-yw4l">arrays</td>
  </tr>
  <tr>
    <td class="tg-yw4l">L</td>
    <td class="tg-yw4l">object</td>
  </tr>
</table>

### *定义方法*{:.header3-font}
.method \<access-spec> \<method-spec>
&emsp;&emsp;\<statements>
.end method

- \<access-spec> : public, private, protected, static, final, synchronized, native, abstract
- \<method-spec> :方法的签名，就是方法的返回值+方法名+参数

```smali
# direct methods
.method constructor <init>(Lcom/android/emulator/detector/MyActivity;Landroid/content/Context;Landroid/widget/TextView;)V
    .registers 4
    .param p1, "this$0"    # Lcom/android/emulator/detector/MyActivity;

    .prologue
    .line 26
    iput-object p1, p0, Lcom/android/emulator/detector/MyActivity$1;->this$0:Lcom/android/emulator/detector/MyActivity;

    iput-object p2, p0, Lcom/android/emulator/detector/MyActivity$1;->val$ctx:Landroid/content/Context;

    iput-object p3, p0, Lcom/android/emulator/detector/MyActivity$1;->val$emulatorLabel:Landroid/widget/TextView;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method
```
方法的种类很多，其中virtual methods是指类的成员方法，direct methods是指类的构造方法，其余super  methods、interface methods、static等可以根据上下文判断。

### *控制流程*{:.header3-font}
&emsp;&emsp;首先我们需要知道像goto 、 invoke-virtual、const-string 这种指令在smali中，叫做操作码助记符（Opcode mnemonics），对高级语言来说就是一些内置函数，这有一些平台提供的[操作码助记符](http://pallergabor.uw.hu/androidblog/dalvik_opcodes.html)。

&emsp;&emsp;if流程在smali中叫做branch，实现其流程的指令叫做branch instructions（也叫做opcode mnemonics）

    goto  <label>
    goto_w  <label>
    if_acmpeq  <label>
    if_acmpne  <label>
    if_icmpeq  <label>
    if_icmpge  <label>
    if_icmpgt  <label>
    if_icmple  <label>
    if_icmplt  <label>
    if_icmpne  <label>
    ifeq  <label>
    ifge  <label>
    ifgt  <label>
    ifle  <label>
    iflt  <label>
    ifne  <label>
    ifnonnull  <label>
    ifnull  <label>
    jsr  <label>
    jsr_w  <label>

&emsp;&emsp;而 ``try...catch  `` 捕获异常跟 ``.catch <classname> from <label1> to <label2> using <label3>`` ，以 ``.``开头的，在smali中叫做directives。从label1到lable2是要捕获的代码，label3是异常的处理。

&emsp;&emsp;循环流程可通过 :label实现，如 `` :cond_4  ...  if-eqz v2, :cond_4`` ，":cond_4"在smali中叫做label。

&emsp;&emsp;关于``switch..case...``可以查看[The lookupswitch instruction](http://jasmin.sourceforge.net/instructions.html) 和 [The tableswitch instruction](http://jasmin.sourceforge.net/instructions.html)这两种。
&emsp;&emsp;类和对象的操作指令

	anewarray  <class>
	checkcast  <class>
	instanceof <class>
	new        <class>



```smali
.method public static hasEth0Interface()Z
    .registers 4

    .prologue  
    .line 63
    :try_start_0
    invoke-static {}, Ljava/net/NetworkInterface;->getNetworkInterfaces()Ljava/util/Enumeration;

    move-result-object v0

    .local v0, "en":Ljava/util/Enumeration;, "Ljava/util/Enumeration<Ljava/net/NetworkInterface;>;"
    :cond_4
    invoke-interface {v0}, Ljava/util/Enumeration;->hasMoreElements()Z

    move-result v2

    if-eqz v2, :cond_1f

    .line 64
    invoke-interface {v0}, Ljava/util/Enumeration;->nextElement()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, Ljava/net/NetworkInterface;

    .line 65
    .local v1, "intf":Ljava/net/NetworkInterface;
    invoke-virtual {v1}, Ljava/net/NetworkInterface;->getName()Ljava/lang/String;

    move-result-object v2

    const-string v3, "eth0"

    invoke-virtual {v2, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    :try_end_19
    .catch Ljava/net/SocketException; {:try_start_0 .. :try_end_19} :catch_1e

    move-result v2

    if-eqz v2, :cond_4

    .line 66
    const/4 v2, 0x1

    .line 69
    .end local v1    # "intf":Ljava/net/NetworkInterface;
    :goto_1d
    return v2

    .line 68
    :catch_1e
    move-exception v2

    .line 69
    :cond_1f
    const/4 v2, 0x0

    goto :goto_1d
.end method
```



## *4.Reference*{:.header2-font}
[Professional Assembly Language](http://blog.hit.edu.cn/jsx/upload/AT%EF%BC%86TAssemblyLanguage.pdf)
[[Quora]What is smali in Android ? ](https://www.quora.com/What-is-smali-in-Android)