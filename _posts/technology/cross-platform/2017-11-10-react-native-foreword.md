---
layout: post
title: React Native |  前言
description: 这是一篇计划文，描述了我们如何学习React Native
date: 2017-11-10 22:50:00
share: false
comments: false
tag:
# - react native
- cross-platform
---
![react native][7]
讲React Native之前，我们应该知道这么一些故事。React是由Facebook公司开发，并且开源到了github，与Vue都是现在很火的前端开发库。之后Facebook觉得这套库在前端使用的效果很是不错，就想让移动端也支持，从而实现如他们的口号一样“Learn Once，Write Anywhere”---学习一次，任何平台都能写。这不就是大前端吗，所以React Native孕育而生。在编码方面React不同于传统的HTML+CSS+JavaScript这一套开发方式，而是采用组件化的形式，让开发者在组件里面可以混写HTML+JavaScript，即JSX代码。而原来的HTML直接解析成真实DOM树，现在也变成了组件先成为虚拟DOM，在插入文档之后才会变成真实DOM。React利用了一个叫做DOM diff的算法提高了网页的性能，所以我们在移动端上面看到很多用React Native实现的应用性能比用HTML5库实现的好很多。看看京东金融和微信。关于HTML5 VS React ，这两者孰优孰劣可以参考这一篇文章[也许，DOM 不是答案][1]

不过React Native现在还没有出1.0版本，各种坑还没有被修复。比如网络请求ajax并不能适配移动端的，所以使用了web标准fetch。但是却不妨碍它能带来的效益，所以很多大厂也适配了。不过由于其License，很多大厂也不敢用了。

而不论使用何种实现都离不开浏览器的引擎WebKit。由于Apple想要开发自己的浏览器（Safari），所以就从KHTML分支fork出了WebKit项目，和KHTML引擎同期还有一款Gecko引擎（Firefox）。由于外界压力，最终将WebKit开源了。随着项目开源，越来越多的公司加入进来，Google就是其中一个。但是由于跟KDE一样和Apple相处不恰，Google决定自己在WebCore上面开发Blink,再结合自主研发的v8（JavaScript引擎），共同研制了开源项目Chromium，该引擎就是现如今Android平台的浏览器引擎。其实在Android4.4之前使用的是Webkit引擎去实现WebView，而现在使用的是Chromium引擎。博主也会在后续跟随老罗的脚步学习这方面知识，如果有兴趣的同学欢迎讨论。推荐一篇博文，先让大家入个门[ndroid Chromium WebView][2]学习启动篇。不过话说回来，Apple也不甘示弱，为了提高JavaScript引擎的性能，重写了JavaScriptCore，并且命名SquirrelFish，后来这个项目演变成了SquirrelFish Extreme（SFX）。主要原因就是前者是一个字节码解释权，而后者却是直接将JavaScript代码编译成机器码,这样可以提高执行速度，所以导致了项目名变更的情况。

React Native在iOS平台使用的是WebKit，而在Android平台目前使用的也是Webkit，并不是平台提供的Chromium。Facebook对于JavaScriptCore引擎又进行了客制化。在github可以找到[facebook android-jsc][3]。知道了这些事之后，我们可以来做个大概的总结，其实React Native框架就是我们平时的原生开发通过libjsc.so等库去解析bundle（许多JavaScript文件的打包文件，为了提高性能所以进行了打包），而Java和JavaScript的交互就是通过这一层所谓的bridge完成的。所以由c/c++编写的库就像媒婆一样，为两者牵线搭桥。而我们想要去使用动态库libjsc,就需要知道它提供的API。Apple已经为我们提供了它的API文档[framework JavaScriptCore][4]。也可以通过这一篇文章[JavaScriptCore Tutorial for iOS: Getting Started][5]简单了解一下JavaScriptCore引擎中的一些知识。

说完这些知识点，我们就知道了其实React Native的存在就是为了让原生开发的一套规范转换到Web开发规范，既然换了一种开发方式就意味着你要学习Web开发的相关知识，这里推荐一篇博文供大家入门前端开发，[React 入门实例教程][6]

之后我们将要学习的内容有如下：

- [x] [Java和JavaScript互操作]({{site.baseurl}}/2022-03-10/react-native-java-js-interoperability)
- [x] [启动流程]({{site.baseurl}}/2021-12-05/react-native-launch)
- [x] [初代渲染器]({{site.baseurl}}/2022-03-20/react-native-render)
- [x] [Fabric渲染器]({{site.baseurl}}/2022-09-22/react-native-fabric-render)
- [ ] [js引擎]({{site.baseurl}}/2023-02-12/hermes-foreword)
- [x] [Metro打包利器]({{site.baseurl}}/2022-11-25/react-native-metro)
- [x] [DevMenu开发者工具]({{site.baseurl}}/2022-10-21/react-native-devmenu)
<!-- - [ ] [DevMenu开发者工具 reload]({{site.baseurl}}/2022-10-21/react-native-devmenu-reload) -->
<!-- - [ ] [DevMenu开发者工具 debug]({{site.baseurl}}/2022-10-21/react-native-devmenu-debug) -->
<!-- - [ ] [DevMenu开发者工具 profiler]({{site.baseurl}}/2022-10-21/react-native-devmenu-profiler) -->

# *工程结构*
- react native项目结构
    - Libraries：react应用js框架
    - packages
        - react-native-codegen
        - react-native-gradle-plugin
    - React:iOS系统
    - ReactAndroid:Android系统
    - ReactCommon:jsc与hermes抽象出来的通用js接口

- metro : 打包器
    - metro:server
    - metro-inspector-proxy：chrome inspector代理
    - 其他
- react native cli(简称cli)：命令集
    - debugger-ui: 与react native手机侧建立双向通信，且代理手机侧的js引擎执行js代码，提供debug、reload等能力
    - cli-plugin-metro:start与bundle命令
    - cli-server-api:start命令启动的server api
    - 其他命令..

# *参考资料*

[1]:http://www.ruanyifeng.com/blog/2015/02/future-of-dom.html
[2]:http://blog.csdn.net/luoshengyang/article/details/46569161
[3]:https://github.com/facebook/android-jsc
[4]:https://developer.apple.com/documentation/javascriptcore
[5]:https://www.raywenderlich.com/124075/javascriptcore-tutorial
[6]:http://www.ruanyifeng.com/blog/2015/03/react.html
[7]:{{site.baseurl}}/asset/cross-platform/WX20221031-014810.png

[历史在重演：从KHTML到WebKit，再到Blink](https://36kr.com/p/202396.html)

[React官网](https://reactjs.org/docs/hello-world.html)


