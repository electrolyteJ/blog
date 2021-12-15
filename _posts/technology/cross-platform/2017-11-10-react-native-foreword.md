---
layout: post
title: React Native ---  前言
description: 这是一篇计划文，描述了我们如何学习React Native
date: 2017-11-10 22:50:00
share: true
comments: true
tag:
# - react native
- cross-platform
---
## *1.Introduction*{:.header2-font}

&emsp;&emsp;讲React Native之前，我们应该知道这么一些故事。React是由Facebook公司开发，并且开源到了github，与Vue都是现在很火的前端开发库。之后Facebook觉得这套库在前端使用的效果很是不错，就想让移动端也支持，从而实现如他们的口号一样“Learn Once，Write Anywhere”---学习一次，任何平台都能写。这不就是大前端吗，所以React Native孕育而生。在编码方面React不同于传统的HTML+CSS+JavaScript这一套开发方式，而是采用组件化的形式，让开发者在组件里面可以混写HTML+JavaScript，即JSX代码。而原来的HTML直接解析成真实DOM树，现在也变成了组件先成为虚拟DOM，在插入文档之后才会变成真实DOM。React利用了一个叫做DOM diff的算法提高了网页的性能，所以我们在移动端上面看到很多用React Native实现的应用性能比用HTML5库实现的好很多。看看京东金融和微信。关于HTML5 VS React ，这两者孰优孰劣可以参考这一篇文章[也许，DOM 不是答案](http://www.ruanyifeng.com/blog/2015/02/future-of-dom.html)

&emsp;&emsp;不过React Native现在还没有出1.0版本，各种坑还没有被修复。比如网络请求ajax并不能适配移动端的，所以使用了web标准fetch。但是却不妨碍它能带来的效益，所以很多大厂也适配了。不过由于其License，很多大厂也不敢用了。

&emsp;&emsp;而不论使用何种实现都离不开浏览器的引擎WebKit。由于Apple想要开发自己的浏览器（Safari），所以就从KHTML分支fork出了WebKit项目，和KHTML引擎同期还有一款Gecko引擎（Firefox）。由于外界压力，最终将WebKit开源了。随着项目开源，越来越多的公司加入进来，Google就是其中一个。但是由于跟KDE一样和Apple相处不恰，Google决定自己在WebCore上面开发Blink,再结合自主研发的v8（JavaScript引擎），共同研制了开源项目Chromium，该引擎就是现如今Android平台的浏览器引擎。其实在Android4.4之前使用的是Webkit引擎去实现WebView，而现在使用的是Chromium引擎。博主也会在后续跟随老罗的脚步学习这方面知识，如果有兴趣的同学欢迎讨论。推荐一篇博文，先让大家入个门[Android Chromium WebView学习启动篇](http://blog.csdn.net/luoshengyang/article/details/46569161)。不过话说回来，Apple也不甘示弱，为了提高JavaScript引擎的性能，重写了JavaScriptCore，并且命名SquirrelFish，后来这个项目演变成了SquirrelFish  Extreme（SFX）。主要原因就是前者是一个字节码解释权，而后者却是直接将JavaScript代码编译成机器码,这样可以提高执行速度，所以导致了项目名变更的情况。

&emsp;&emsp;React Native在iOS平台使用的是WebKit，而在Android平台目前使用的也是Webkit，并不是平台提供的Chromium。Facebook对于JavaScriptCore引擎又进行了客制化。在github可以找到[facebook android-jsc](https://github.com/facebook/android-jsc)。知道了这些事之后，我们可以来做个大概的总结，其实React Native框架就是我们平时的原生开发通过libjsc.so等库去解析bundle（许多JavaScript文件的打包文件，为了提高性能所以进行了打包），而Java和JavaScript的交互就是通过这一层所谓的bridge完成的。所以由c/c++编写的库就像媒婆一样，为两者牵线搭桥。而我们想要去使用动态库libjsc,就需要知道它提供的API。Apple已经为我们提供了它的API文档[framework JavaScriptCore](https://developer.apple.com/documentation/javascriptcore)。也可以通过这一篇文章[JavaScriptCore Tutorial for iOS: Getting Started](https://www.raywenderlich.com/124075/javascriptcore-tutorial)简单了解一下JavaScriptCore引擎中的一些知识。

![arch]({{site.baseurl}}/asset/2017-11-10-react-native-foreword-arch.jpeg)


&emsp;&emsp;说完这些知识点，我们就知道了其实React Native的存在就是为了让原生开发的一套规范转换到Web开发规范，既然换了一种开发方式就意味着你要学习Web开发的相关知识，这里推荐一篇博文供大家入门前端开发，[React 入门实例教程](http://www.ruanyifeng.com/blog/2015/03/react.html)

&emsp;&emsp;之后我们将要学习的内容有如下：

- [x] React Native---启动流程
- [ ] React Native---渲染机制
- [ ] React Native---Java和JavaScript通信机制
- [ ] React Native---开发者调试工具
- [ ] React Native---cpp与java的混合对象管理
## *2.Reference*{:.header2-font}

[历史在重演：从KHTML到WebKit，再到Blink](https://36kr.com/p/202396.html)
[也许，DOM 不是答案](http://www.ruanyifeng.com/blog/2015/02/future-of-dom.html)
[React官网](https://reactjs.org/docs/hello-world.html)
[React 入门实例教程](http://www.ruanyifeng.com/blog/2015/03/react.html)
