---
layout: post
title: 移动端动态化
description: Qigsaw、RePlugin、React Native、微信小程序
tag: 
- algorithm-structure-arch
---
随着移动端的高速发展，一个项目的人力越来越多业务越来越臃肿，业务解耦势在必行，紧随而来逐渐出现了插件化、React Native、Flutter、小程序等动态化的解决方案，这一次我们来聊聊插件化。

插件化实现需要考虑三个方面

- 代码动态加载：ClassLoader动态性、LoadedApk动态性、ArtMethod Hook
- 资源动态加载：AssetManager加载资源
- 插件框架兼容性：Android Framework Api升级以及限制级Api适配

# 代码动态加载


## 类加载机制

类加载，采用双亲委托机制，顶层加载器先判断能不能加载，加载不了就会让下一层加载器加载。加载的过程主要有五个阶段:加载(二进制流读取) 、验证(类文件的检验) 、准备(静态成员变量分配内存) 、 解析(常量池的符号引用变为直接引用) 、初始化

```shell
Bootstrap ClassLoader---BootClassLoader(load class from  jdk、android framework)
     |
Application ClassLoader---DexClassLoader/PathClassLoader/InMemoryDexClassLoader（load class from CLASSPATH,-classpath,-cp,Manifest）
```
Android的ClassLoader有DexClassLoader、PathClassLoader，他们都继承BaseDexClassLoader，前者可以功能较为强大可以加载apk、jar、dex、so,加载路径自己可以定义，后者限制较大，只能加载路径被指定为/data/dalvik-cache的dex文件，BaseDexClassLoader文件成员变量pathList是DexPathList的对象，DexPathList用dexElements数组存储dex文件，用nativeLibraryPathElements数组存储so文件。

Android dex文件的类查找与加载流程
```java
PathClassLoader/BaseDexClassLoader#findClass ->
DexPathList#findClass ->
Element#findClass ->
DexFile#loadClassBinaryName
```
BaseDexClassLoader通过类名查找类在不在elements数组里，如果不存在，则会让其父类加载器继续查找，如果顶部的类加载器也不存在，则会让顶部类加载器加载，加载不了会依次向下让子类加载器加载。BaseDexClassLoader在加载类时通过DexFile类的native方法defineClassNative，在分析defineClassNative之前我们先来看看elements的初始化。

```java
 private static Element[] makeDexElements(List<File> files, File optimizedDirectory,
            List<IOException> suppressedExceptions, ClassLoader loader, boolean isTrusted) {
      ...
      for (File file : files) {
          if (file.isDirectory()) {
              ...
          } else if (file.isFile()) {
              String name = file.getName();

              DexFile dex = null;
              if (name.endsWith(DEX_SUFFIX)) {
                  // Raw dex file (not inside a zip/jar).
                  try {
                      dex = loadDexFile(file, optimizedDirectory, loader, elements);
                      if (dex != null) {
                          elements[elementsPos++] = new Element(dex, null);
                      }
                  } catch (IOException suppressed) {
                      ...
                  }
              } else {
                  ...
              }
              if (dex != null && isTrusted) {
                dex.setTrusted();
              }
          } else {
              System.logW("ClassLoader referenced unknown path: " + file);
          }
      }
      if (elementsPos != elements.length) {
          elements = Arrays.copyOf(elements, elementsPos);
      }
      return elements;
    }
```
在BaseDexClassLoader构造的时候会调用makeDexElements初始化elements数组，每个Element元素表示DexFile，而DexFile是loadDex来自于dexPath文件内的dex，所以当程序要查找一个类是否已经被加载，只要遍历一下elements数组的DexFile是否存在该类。tinker热修复正是基于这个逻辑来完成类修复的，在elements数组中，被修复的类需要在有问题的类左侧。

 java类 | jni| cpp类 | 
 --- | --- | ---|
 "Ldalvik/system/DexFile;" | runtime/native/dalvik_system_DexFile | libdexfile/dex/dex_file
 defineClassNative|DexFile_defineClassNative| FindXxx
 
ClassLinker调用DefineClass函数加载类，关于ClassLinker加载类的逻辑我们就不继续跟踪了。

除此之外Android resource、so查找流程如下
```java
//资源路径查找
PathClassLoader/BaseDexClassLoader#findResource ->
DexPathList#findResource ->
Element#findResource ->
File#toURL

//so文件路径查找
PathClassLoader/BaseDexClassLoader#findLibrary ->
DexPathList#findLibrary ->
NativeLibraryElement#findNativeLibrary ->
```

## LoadedApk加载机制

## ArtMethod Hook

# 资源加载
<!-- # 兼容性 -->

