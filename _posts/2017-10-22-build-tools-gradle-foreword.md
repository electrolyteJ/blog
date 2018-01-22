---
layout: post
title:  构建工具Gradle
description: 
date: 2017-10-22
share: true
comments: true
tag:
- Build Tools
# - AOSP(APP)
---
## *1.Summary*{:.header2-font}
&emsp;&emsp;从Android团队开始宣布放弃Eclipse，使用Android Studio时，构建工具Gradle进入了Android开发者的视野。而随着热修复、插件化、编译时注解的流行，深入了解Gradle就变得很有必要了。那么什么是Gradle ？
## *2.About*{:.header2-font}
&emsp;&emsp;Gradle是一个基于Ant构建工具，用Groovy DSL描述依赖关系的jar包。我们都知道早期的Android开发使用的是Eclipse,而Eclipse的构建工具使用的是Ant，用XML描述依赖关系，而XML存在太多的弊端，不如动态语言。所以动态语言Groovy代替了XML，最后集成为Gradle。而Groovy诞生就是由于在后端Java是一门静态语言，对于配置信息处理比较差，所以Apache开发了这门语言。说道后端Java，必然要说道Android端Java，与之搭配的就是最近很火的Kotlin，Kotlin也是一门动态语言，而且Kotlin和Groovy一样也可以写build.gradle文件，它们都是基于JVM的动态语言，都可以使用DSL去描述项目依赖关系。

## *3.Intoduction*{:.header2-font}
&emsp;&emsp;我们会从Groovy DSL和Gradle框架来分析。
### *Groovy DSL*{:.header3-font}
&emsp;&emsp;首先Groovy语言的基本知识我们不进行探讨，网上与之相关的资料有很多。我们来讲讲它的DSL，因为Gradle提供的build.gradle配置文件就是用DSL来写的。那么什么是DSL？[维基百科](https://en.wikipedia.org/wiki/Domain-specific_language)里面描述的很清楚，但是具体到代码有哪些呢?就像Android里面的AIDL，前端的JQUERY。由于DSL是一种为解决某种问题的领域指定语言，所以Android团队写了解析AIDL代码，Gradle团队写了解析Groovy DSL的代码。

### *Gradle框架*{:.header3-font}
&emsp;&emsp;我们都知道Gradle的生命流程要经历三个部分：初始化、配置、执行。

初始化：settings.gradle
配置：build.gradle
执行：task

## *4.Reference*{:.header2-font}
[Groovy官网](http://www.groovy-lang.org/learn.html)
[深入理解Android之Gradle](http://blog.csdn.net/innost/article/details/48228651)

[Gradle的官网](https://gradle.org/)
[Build Overview](http://tools.android.com/build)