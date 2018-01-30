---
layout: post
title: Location系统 --- 架构概述
description: 讲解Location架构
author: 电解质
date: 2018-01-30
share: true
comments: true
tag:
- LBS
---
* TOC
{:toc}
## *1.Summary*{:.header2-font}
&emsp;&emsp;在上一篇我们讲了基本的使用，现在我们来看看Location架构是如何设计的。

## *2.About*{:.header2-font}
&emsp;&emsp;现如今原生的Location API已经很少人使用了，大都是集成第三方库，就连google也推荐使用他们家的Google Location Services API，所以对于原生的Location架构，我们可以当做学习资料来研究。如果你期望能参加LBS相关的开发工作，我相信通过研究源生的Location架构来提升自身技术是一个不错的选择。如何使用Google Location Services API可以看这一篇文章[Building Apps with Location & Maps](https://developer.android.com/training/building-location.html)，但是由于国内的特殊情况，所以催生了高德地图、腾讯地图等替代品。给了链接吧[高德定位sdk](http://lbs.amap.com/api/android-location-sdk/locationsummary)

## *3.Intoduction*{:.header2-font}

![]({{site.asseturl}}/{{ page.date | date: "%Y-%m-%d" }}/2018-01-30-location-system-framework-arich.png)


## *4.Reference*{:.header2-font}
[Android 系统中 Location Service 的实现与架构](https://www.ibm.com/developerworks/cn/opensource/os-cn-android-location/)