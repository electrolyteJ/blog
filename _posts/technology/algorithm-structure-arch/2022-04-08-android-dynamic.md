---
layout: post
title: 移动端动态化
description: Qigsaw、RePlugin、React Native、微信小程序
tag: 
- algorithm-structure-arch
---

# 代码hook

## 类加载机制
由于Android平台JVM是读取dex文件，所以原来Java提供的ClassLoader需要重新定制, Android的ClassLoader有DexClassLoader、PathClassLoader，前者可以功能较为强大可以加载apk、jar、dex、so,加载路径自己可以定义，后者限制较大，只能加载dex，路径也被指定/data/dalvik-cache

```
Bootstrap ClassLoader---BootClassLoader(load class from  jdk、android framework)
     |
Application ClassLoader---DexClassLoader/PathClassLoader（load class from CLASSPATH,-classpath,-cp,Manifest）
```

类加载，采用双亲委托机制，顶层加载器先判断能不能加载，加载不了就会让下一层加载器加载。加载的过程主要有五个阶段 加载(二进制流读取) 验证(类文件的检验) 准备(静态成员变量分配内存) 解析(常量池的符号引用变为直接引用) 初始化

# 资源加载
<!-- # 兼容性 -->

