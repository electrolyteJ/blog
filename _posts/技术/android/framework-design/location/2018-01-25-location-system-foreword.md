---
layout: post
title: Location系统 --- 前言
description: 这是一篇计划文，描述了我们如何学习LBS
date: 2018-01-25 22:50:00
tag: 
- framework-design/location
share: true
commets: true
---
## *1.Summary*{:.header2-font}

由于现在的共享单车、滴滴打车、外卖等LBS应用的持续火热和烧钱，导致定位技术在这些行业中担当着举足轻重的角色，定位技术之于LBS应用，就像音视频编解码技术之于视频应用。所以研究定位能让我们更加适应这个社会的变化，而我相信采集有效的定位数据是这些行业实现智能化（人工智能）的基石。

首先我们需要普及一下定位系统的相关知识。

### *GPS*{:.header3-font}

国际性组织GNSS，有四大成员：美国GPS、俄罗斯格洛纳斯GLONASS、中国北斗COMPASS、欧洲伽利略GALILEO。
现如今的共享单车都在使用中国北斗，比如摩拜、小黄车，也不能说它的技术已经远超GPS，而是政府对于北斗的推广确实上心了，在加上北斗在中国大陆上空确实布局的不错，所以卫星数据准确性高。有兴趣可以看看这篇文章
[GPS 对比 北斗](https://mp.weixin.qq.com/s/UJCN71SfGIKBlMVH0IFmtw)，补充一下知识。

但是尽管如此，手机设备毕竟是属于全球化的产品，而且GPS比起北斗确实比较成熟，所以GSP成了首选。为了优化GPS，芯片厂商提供标准的在线辅助工具AGPS，MTK还提供了离线辅助手段（Hot still和EPO）。

下面表格表明它们的差异性

|辅助手段 |	机理|	数据来源（流量）|	有效时间|	好处	|改善措施|
|----|---|---|---|---|----|
|Hot still|利用解调出来的卫星星历预测其7天内的星历|已解调卫星的星历（0 KB）|7天|极大缩小定位时间、有助于弱信号环境的定位、无需连网|打上最新的补丁、默认开启辅助手段。|
|EPO	|从MTK 服务器下载EPO file，预测未来30天所有GPS卫星的星历|网络（270KB/次，可利用有wifi链接时进行更新）|30天|极大缩小定位时间、有助于弱信号环境的定位、离线辅助（辅助数据有效时间内）|	
|AGPS|从AGPS 服务器获取辅助数据（包括参考时间，参考位置，星历和历书|网络（4KB）|2小时|	极大缩小定位时间、有助于弱信号环境的定位|
{:.inner-borders}

这些辅助工具能够提供什么呢？答案是：时间、位置、星历（ephemeris）、年历（almanac）。
有了这几个参数中的几个，就可以极大的增加Location系统的启动速度。

下面来看看启动方式。

启动方式|介绍
---|---
FULL start|没有任何的辅助资讯。相当于end user第一次买到手机后使用定位应用的场景。
COLD start|有时间辅助资讯，end user不会遇到该场景。
WARM start|有时间、位置辅助资讯，end user此次定位距离上次定位超过2～4个小时。
HOT start|有所有的辅助资讯，end user此次定位距离上次定位小于2～4小时。
{:.inner-borders}

以上几种我们并不总会遇到，最为常见的就是warm start和hot start。那么如何衡量各种启动类型的响应时间。答案是TTFF（Time to first fix）,可以看看维基百科上面的解释[Time to first fix](https://en.wikipedia.org/wiki/Time_to_first_fix)。最需要理解的就是fix这个单词，维基百科上面的解释是，计算出地球上点的解决方案。

MTK给出了它们在open sky,有6颗卫星SNR》40db的条件下的测量数据

    FULL start TTFF：小于50s。

    COLD start TTFF：小于40s。

    WARM start TTFF：小于35s。

    HOT start TTFF：小于5s。

### *CellID*{:.header3-font}
这个就是我们常见的基站定位。
### *WiFi MACID*{:.header3-font}

主要采用无线AP的MAC地址定位。手机会保存用户一周之内的数据，通过网络将数据传给服务器，服务器会检索每一个AP地址并结合RSSI（接收信号强度），计算出一个合理的位置。

### *其他*{:.header3-font}
除了以上几种还有蓝牙、传感器定位。但在手机端较为少用。

对于这些定位方式如果有兴趣的话可以参考这一篇文章[室内定位（总结：种类，方法，特点）](http://www.cnblogs.com/lesliexong/p/7050360.html), 由于本文的重点是讲解Location系统，上面的内容只是作为一个背景知识，所以不进行深入挖掘。


在Android的Location API里，为开发者提供了三种位置提供者：gps(GPS, AGPS)、network(CellID, WiFi MACID)、passive(从其他的软件获取)

下面我们就来罗列一下学习计划

- [x] [Location系统---入门]({{site.baseurl}}/2018-01-25/location-system-elementary)
- [x] [Location系统---架构概述]({{site.baseurl}}/2018-01-30/location-system-arich)
- [x] [Location系统---启动流程]({{site.baseurl}}/2018-01-29/location-system-launch)
- [ ] [Location系统---Map]({{site.baseurl}}/2018-01-25/location-system-map)
- [ ] [Location系统---项目实战]({{site.baseurl}}/2018-01-25/location-system-practice)

## *2.Reference*{:.header2-font}

[Android Location Providers – gps, network, passive – Tutorial](https://developerlife.com/2010/10/20/gps/)


