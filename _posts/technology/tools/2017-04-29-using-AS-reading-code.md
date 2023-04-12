---
layout: post
title:  使用Android Studio阅读AOSP源码
description: 为什么推荐使用Android Studio阅读AOSP ？ 这一篇文章将会解答
date: 2017-04-29 22:50:00
share: true
comments: true
tag:
- tools
# - AOSP(SYS)
---

## *1.Summary*
&emsp;&emsp;还是老样子，我们先来谈谈为什么要写这篇文章的原由。我们知道在阅读Android Open Source Project(简称AOSP)源码可以使用的工具有很多，轻量级的有Sublime Text、Notepad++、Atom、Vim等编辑器，重量级有Eclipse（简称ES）、Android Studio（简称AS）、Source Insight（简称SI）等IDE。而选择一款好工具，将会给你带来成倍的收益。需要工具给你提供的信息无非是，类继承结构图、被调用方法的定义或者声明的位置，文件的目录结构图，强大的搜索功能，类成员变量和成员方法的结构图，强大的编辑能力（如果需要修改AOSP的源码），集成这些功能的只有IDE这种类型的工具了。想AS、ES、SI这些都是支持导入整个工程的源码，所以使用起来非常方便。AS和ES由于设计语言的问题，对AOSP中C/C++文件支持不是很好，比如不能显示C/C++整个文件的方法、函数、类、变量，不支持函数、方法的跳转。而这一缺点SI却弥补了。所以对于Framework层以上的Java代码我使用AS/ES来阅读，其他的用SI阅读。不明白Android整个架构的可以看一下这个图。

![architecture]({{site.baseurl}}/asset/2017-04-29/2017-04-29-android_architecture.png){:.white-bg-image}

&emsp;&emsp;但是SI就只有这一点吸引了我，其他的功能相对AS/ES还是差太多。由于这不是一篇争论谁优谁劣，所以不做细究。只要知道，想看C/C++文件用SI是最好的。而对于ES和AS我选择了AS，google已经明确声明今后不在ES上更新ADT插件了，而且AS不断更新的新功能也吸引了我。

## *2.About*
&emsp;&emsp;关于AS和google的关系网上资料很多，不做讨论。我给大家提供一个[AS的官网博客](http://tools.android.com/recent)。AS源于Jetbrains的产品IntelliJ IDEA，可以看看IntelliJ IDEA对Android平台的支持--->[IDEA官网博客](https://www.jetbrains.com/help/idea/2017.1/android.html)

## *3.Introduction*
&emsp;&emsp;那么接下来就讲讲，我使用AS阅读AOSP源码的一些习惯吧。

### _导入整个AOSP源码工程_
&emsp;&emsp;Android团队已经为我们提供了idegen工具去[制作AOSP源码的索引](https://android.googlesource.com/platform/development/+/master/tools/idegen/README)，有了索引才能让AS加载AOSP源码。这里说个题外话，著名的[AndroidXref](http://androidxref.com/)源码查询网址使用的是[OpenGrok](http://opengrok.github.io/OpenGrok/)搜索引擎，如果想要搭建自己项目的AndroidXref，也需要创建项目的索引，可见索引的重要性。那么接下来我们就按照Android团队提供的文档生成项目对应的索引。

- 1）全编之后，生产out目录，再单编development/tools/idegen/这个模块，可以使用make命令也可以使用mmm命令,将会在out目录下生成idegen.jar
- 2）执行development/tools/idegen/idegen.sh这个脚本调用idegen.jar，生成android.ipr和android.iml两个AS的配置文件。
- 3）将配置文件放在AOSP工程根目录下，用AS打开就可会开始导入整个工程了。

上面的操作执行下来确实挺浪费时间的，如果不进行编译想要直接导入AOSP源码的话，只要有android.ipr和android.iml就可以。这里我上传一份自己的配置文件，下载路径：[配置文件]({{site.baseurl}}/asset/2017-04-29/configuration)，或者使用idegen.jar生成android.ipr和android.iml
获得两个配置文件之后就是加载整个项目到AS，但是由于没有缓存，初次加载将会导致内存紧张，电脑卡顿。所以我们需要优化一下加载。

### _性能优化_
可以从下面几个方面优化。

- 优化加载项
- 优化AS
- 换电脑

1.优化加载项

由于include整个工程会导致电脑内存紧张，所以我们可以exclude一些不常用的目录。可以在配置文件android.iml将sourceFolder标签换成excludeFolder标签，也可以在AS的设置中exclude。如果初次加载使用前者是最好的方式。

![]({{site.baseurl}}/asset/2017-04-29/2017-04-29-android_include_projects.png){:.white-bg-image}

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;`android.iml`

![]({{site.baseurl}}/asset/2017-04-29/2017-04-29-android_projects_structure.png)

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;`Projects Structure`

从图二可以看到，处理可以将一个目录设置成exclude，让AS不去加载，在使用`查找功能`时我们也服务查找exclude的文件。如果一个目录设置成sources，使用`查找类`功能时该目录会被检索。

2.优化AS

官方推荐一篇文档可供查看:[修改虚拟机配置](https://developer.android.com/studio/intro/studio-config.html)
通过修改文件 studio.exe.vmoptions

        -server
        -Xms256m
        -Xmx750m
        -XX:MaxPermSize=350m
        -XX:ReservedCodeCacheSize=240m
        -XX:+UseConcMarkSweepGC
        -XX:SoftRefLRUPolicyMSPerMB=50
        -da
        -Djna.nosys=true
        -Djna.boot.library.path=

        -Djna.debug_load=true
        -Djna.debug_load.jna=true
        -Dsun.io.useCanonCaches=false
        -Djava.net.preferIPv4Stack=true
        -Didea.paths.selector=AndroidStudio2.2
        -Didea.platform.prefix=AndroidStudio
        -Didea.jre.check=true

可以通过[这个博客](http://blog.csdn.net/xyxjn/article/details/46906909)了解以上各个参数，优化AS其实并没有抱很大期望，因为这个是Android团队的事情。所以，我毅然决然的选择了第三种方式换电脑。

### _使用中的一些细节_
1.依赖库的选择

依赖库只导入framework、jdk，也可以选择性的添加external（主要是一些开源库wpa_supplicant、libhevc）。这样在进行代码跳转时就可以调到源码framework，而不是sdk的framework。

![]({{site.baseurl}}/asset/2017-04-29/2017-04-29-android_projects_dependencies.png)

2.类视图的过滤器

类结构图

从左到右开启选项：

    显示ImageCrop类实现的接口
    显示ImageCrop类set/get方法
    显示ImageCrop类成员变量
    显示ImageCrop类非公有变量/方法

其中的`显示ImageCrop类实现的接口`选项是我最喜欢的，开启之后可以在类结构图中查看该类override的方法。`显示ImageCrop类非公有变量/方法`选项也是非常有用。一般一个AOSP文件的方法非常多，绝大部分是非公有，如果我们只关心一个类的公有接口，不想了解内部实现，关闭该选项即可。

![]({{site.baseurl}}/asset/2017-04-29/2017-04-29-android_classes_view.png)

类继承关系图

![]({{site.baseurl}}/asset/2017-04-29/2017-04-29-android_classes_hierarchy.png)

快捷键：ctrl+h


3.多窗口任务处理

在打开的文件右击鼠标，就会有一个分屏的选项，选中即可开启多窗口功能。文件可以直接拖拽到其他窗口，可以置顶文件等功能交互非常方便。在分析流程图时，配合bookmarks功能使用非常好用。

![]({{site.baseurl}}/asset/2017-04-29/2017-04-29-android_mutil_windows.png)

4.对比工具

在文件右击鼠标，就会有对比功能，可以对比文件夹、文件、apk内容。对比工具一般配合查找功能使用。

![]({{site.baseurl}}/asset/2017-04-29/2017-04-29-android_compare_tool.png)

5.书签

	开关书签 f11
	用助记符开关书签 ctrl+f11
	使用下面的快捷键返回到对应书签 ctrl+number
	显示书签 shift+f11

![]({{site.baseurl}}/asset/2017-04-29/2017-04-29-android_bookmarks.png)

6.资源定位

    ctrl+n 查找类
    ctrl+shift+n 查找文件
    Ctrl + E 打开最近使用的文件  
    输入的查询命令`文件夹/文件 : 行数`，三个参数可以搭配使用
    
    alt+f1 定位文件所属位置
    ctrl+shift+i 快速查找定义
    ctrl+f  在某个文件内查找内容
    ctrl+shift+f 查找被工程include进来的文件内容

![]({{site.baseurl}}/asset/2017-04-29/2017-04-29-android_find_all.png)

搜索结果
![]({{site.baseurl}}/asset/2017-04-29/2017-04-29-android_find_result.png)






## *4.Reference*
[制作AOSP源码索引](https://android.googlesource.com/platform/development/+/master/tools/idegen/README)