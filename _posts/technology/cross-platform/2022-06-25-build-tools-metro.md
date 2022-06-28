---
layout: post
title:  Metro
description: 专为react native定制的打包器
date: 2022-06-25 22:50:00
tag:
- build-tools
published : false 
---
## *1.Introduction*{:.header2-font}
对于前端的打包工具有webpack(大而全，图片代码打包)，rollup(专攻代码打包,框架场景常见)等，既然有这些打包工具为什么还要在移动端搞一个metro，其中一个原因为ram bundle的区别，由于iOS读取一个文件效率更高故采用indexed ram bundle,android采用file ram bundle。

那么接下来了解一下metro

metro的bundling有三个阶段：
1. 解析(Resolution):
2. 转换(Transformation)：
3. 序列化(Serialization)：

## *2.Reference*{:.header2-font}
[干货 | 减少50%空间，携程机票React Native Bundle 分析与优化](https://mp.weixin.qq.com/s/aajdqmpCLKvGaokL4Qp1tg)
[2020-06-02 React Native 打包工具Metro原理探究](https://www.jianshu.com/p/b02f719d6107)
[ctripcorp/moles-packer](https://github.com/ctripcorp/moles-packer)
[google/diff-match-patch](https://github.com/google/diff-match-patch)
[react-native-multibundler](https://github.com/smallnew/react-native-multibundler)
[React Native 拆包及实践「iOS&Android」](https://juejin.cn/post/6844903855805693965#heading-4)