---
layout: post
title: 移动端动态化
description: Qigsaw、RePlugin、React Native、微信小程序
tag: 
- algorithm-structure-arch
---
* TOC
{:toc}

随着移动端的高速发展，一个项目的人力越来越多业务越来越臃肿，业务解耦势在必行，紧随而来逐渐出现了插件化、React Native、Flutter、小程序等动态化的解决方案，这一次我们来聊聊插件化。

插件化实现需要考虑三个方面

- 代码动态加载：ClassLoader动态性、LoadedApk动态性、ArtMethod Hook
- 资源动态加载：AssetManager加载资源
- 插件框架兼容性：Android Framework Api升级以及限制级Api适配

# 代码动态加载


## ClassLoader加载机制

### 类加载

类加载，采用双亲委托机制，顶层加载器先判断能不能加载，加载不了就会让下一层加载器加载。加载的过程主要有五个阶段:加载(二进制流读取) 、验证(类文件的检验) 、准备(静态成员变量分配内存) 、 解析(常量池的符号引用变为直接引用) 、初始化

```shell
Bootstrap ClassLoader---BootClassLoader(load class from  jdk、android framework)
     |
Application ClassLoader---DexClassLoader/PathClassLoader/InMemoryDexClassLoader（load class from CLASSPATH,-classpath,-cp,Manifest）
```
Android的ClassLoader有DexClassLoader、PathClassLoader，他们都继承BaseDexClassLoader，前者可以功能较为强大可以加载apk、jar、dex、so,加载路径自己可以定义，后者限制较大，只能加载路径被指定为/data/dalvik-cache的dex文件，BaseDexClassLoader文件成员变量pathList是DexPathList的对象，DexPathList用dexElements数组存储dex文件，用nativeLibraryPathElements数组存储so文件。

Android dex文件的类查找与加载流程
```java
ClassLoader#loadClass -> PathClassLoader/BaseDexClassLoader#findClass ->
DexPathList#findClass -> Element#findClass -> DexFile#loadClassBinaryName ->
ClassLinker#DefineClass
```
BaseDexClassLoader通过类名查找类在不在elements数组里，如果不存在，则会让其父类加载器继续查找，如果顶部的类加载器也不存在，则会让顶部类加载器加载，加载不了会依次向下让子类加载器加载。BaseDexClassLoader在加载类时通过DexFile类的native方法defineClassNative，在分析defineClassNative之前我们先来看看elements的初始化。

在BaseDexClassLoader构造的时候会调用makeDexElements初始化elements数组，每个Element元素表示DexFile，而DexFile是loadDex来自于dexPath文件内的dex，所以当程序要查找一个类是否已经被加载，只要遍历一下elements数组的DexFile是否存在该类。tinker热修复正是基于这个逻辑来完成类修复的，在elements数组中，被修复的类需要在有问题的类左侧。

 java类 | jni| cpp类 | 
 --- | --- | ---|
 "Ldalvik/system/DexFile;" | runtime/native/dalvik_system_DexFile | libdexfile/dex/dex_file
 defineClassNative|DexFile_defineClassNative| FindXxx
 
ClassLinker调用DefineClass函数加载类，关于ClassLinker加载类的逻辑我们就不继续跟踪了。

### so加载

so文件加载调用链
```java
System#loadLibrary -> Runtime#loadLibrary0 -> 
ClassLoader#loadLibrary -> PathClassLoader/BaseDexClassLoader#findLibrary ->
DexPathList#findLibrary -> NativeLibraryElement#findNativeLibrary(获取到filename) ->
Runtime#nativeLoad -> JavaVMExt#LoadNativeLibrary -> native_loader.cpp OpenNativeLibrary
```
OpenNativeLibrary最后调用dlopen加载so文件，通过System#loadLibrary我们可以实现动态加载so，不过由于安全问题，无法从sdcard的路径加载，只能从/data/data/包名 加载so。

## LoadedApk加载机制

LoadedApk类内部的mClassLoader用来加载Application等类，根据双亲委托机制，我们可以自定义ClassLoader(DexClassLoader)然后将mClassLoader作为父类，自定义的ClassLoader用来加载插件包，mClassLoader依旧用来加载宿主包。

## ArtMethod Hook

在ART中ArtMethod结构体表示java类成员函数，当A调用a方法之前，我们可以修改a方法的地址，将hook函数地址copy到a方法的地址，由于ArtMethod结构体的size在每个ART都不同，那么如何兼容 ？ 计算ArtMethod结构体的大小，replace两个函数的地址。

有时候为了保留a函数，会将a函数copy到backup函数，然后将跳板地址copy到a函数的入口地址，通过跳板(汇编指令：br调用xx函数)调用hook函数。

# 资源加载
<!-- # 兼容性 -->

