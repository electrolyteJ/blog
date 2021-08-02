---
layout: post
title: Android架构中的组件化
description: 让我们来快速搭建组件化
author: 电解质
date: 2018-02-09 22:50:00
share: false
comments: false
tag: 
- app-design/architecture
---
* TOC
{:toc}
## *1.Summary*{:.header2-font}
现如今开发Android的代码量越来越庞大，为了便于团队的开发，很多Android团队使用了组件化、插件化的方式来解耦项目。

| 解耦的方式| 构建/执行  | 打包方式|
|------------ | ------------- | -------------|       
|组件化 |      编译时 |     aar|
|插件化 |      运行时 |     apk/dex|
{:.wide}

对于插件化，主要是通过动态代理framework层提供给app层的Binder api或者hook虚拟机加载dex的流程来动态加载apk或者dex，比如动态换肤、热修复这样的案例。不过这种行为对framework有很大的破坏性。对于组件化，可以将业务进行拆分为相互解耦的组件，再通过路由将各个组件串联起来。除了业务解耦，还能让业务组件在调试时单独运行，这样可以调高开发效率。

## *2.Introduction*{:.header2-font}

先定义一下bundle和foundation,bundle是依附于app framework的native bundle(静态组件，动态插件)、flutter bundle、react native bundle、hybrid bundle，有些bundle具有动态性能被app framework动态加载；foundation是赋予上层能力的基础服务，更像是一些用来快速开发页面的toolkits，比如网络、存储、图像、音视频都是foundation。bundle之间存在通信，比如页面路由。

说了这么多，还是让我们来看看代码怎么写的。结合[bundles-assembler](https://github.com/JamesfChen/bundles-assembler)这个项目来看，这个项目是我自己的开源项目，欢迎您的star/fork/pr。

### 配置module
bundle和foundation在gradle眼里都是module,所以一开始需要在module_config.json配置模块，模块配置好，还需要手动用android studio创建模块，这一块后面可以做成自动化生成。
```
  "allModules": [
    ...
    {
      "simpleName": "hotel-bundle1", #给idea plugin显示用
      "canonicalName": ":hotel-module:bundle1", #给settings.gradle include使用
      "format": "bundle",
      "group": "hotel",
      "binary_artifact": "com.jamesfchen.b:hotel-bundle1:1.0", #给project implementation使用
      "deps": [    #依赖项
        ":hotel-module:foundation"
      ]
    },
    {
      "simpleName": "hotel-bundle2",
      "canonicalName": ":hotel-module:bundle2",
      "format": "bundle",
      "group": "hotel",
      "binary_artifact": "com.jamesfchen.b:hotel-bundle2:1.0",
      "deps": [
        ":hotel-module:foundation"
      ]
    },
    ...
   ]
```
当配置好module，第一次需要运行指令`./gradlew publishAll`将所有的模块发布到maven仓库,目前只做到发布到mavenlocal后续需要发布到远程maven。


### 选择模块

local.properties
```
excludeModules=hotel-bundle2,
sourceModules=app,hotel-bundle1,\
    hotel-main,hotel-foundation,hotel-lint,\
  framework-loader,framework-router,framework-network
apps=hotel-main,app,home-main
```

利用工具(tools/module-manager-plugin-1.0.1.jar)来选择模块，对于fwk组必须不被exclude，因为作为基础服务要集成到项目中，exclude只会对app framework以上的模块，如果有兴趣了解工具的源码，来这里[康康](https://github.com/JamesfChen/bundles-assembler/tree/main/module-manager-intellij-plugin), 来点个![img](https://github.com/JamesfChen/bundles-assembler/blob/main/android/img.png)

![picture](https://github.com/JamesfChen/bundles-assembler/blob/main/android/tools/bundles.png)

### 组件通信(ibc,inter-bundle communication)

页面路由
- 利用android framework层的intent uri路由跳转
- 在app framework实现路由跳转，需要将app层的路由器发布到app framework的路由器管理中心，当需要跳转时，app framework会到管理中心find获取路由器，然后进行跳转

cbpc,cross bundle procedure call
- 暴露api给外部bundle模块，然后内部实现接口，需要在app framework注册暴露的api，方便search，实现方式与页面路由的第二种方法相似

### 监听App生命周期
使用lifecycle-plugin，自动注册监听App，使用方式，移步这个项目[spacecraft-android-gradle-plugin](https://github.com/JamesfChen/spacecraft-android-gradle-plugin)

项目结构
```
hotel-module
--- bundle1 bundle1
--- bundle2 bundle2
--- foundation 组件们的公共库
--- main 调试组件的入口
--- hotel-lint lint规则
framework
--- loader  framework的加载器
--- network 网络库
--- ibc  inter-bundle communication。页面路由（http路由，模块路由）、bundle rpc、message
--- common  公共代码
tools 项目工具
```

## *3.Reference*{:.header2-font}
[英语流利说 Android 架构演进](https://blog.dreamtobe.cn/2016/05/29/lls_architecture/)

[微信Android客户端架构演进之路](http://www.infoq.com/cn/articles/wechat-android-app-architecture)

[从零开始的Android新项目11 - 组件化实践（1）](http://blog.zhaiyifan.cn/2016/10/20/android-new-project-from-0-p11/)
