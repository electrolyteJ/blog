---
layout: post
title: AV --- 前言
description: 
author: 电解质
date: 2020-10-11 22:50:00
share: true
comments: true
tag: 
- app-design/av
published : false
---
## *1.Summary*{:.header2-font}
&emsp;&emsp;2016年，互联网掀起了一场直播浪潮，这一年被称为[直播元年](https://baike.baidu.com/item/%E4%B8%AD%E5%9B%BD%E7%BD%91%E7%BB%9C%E7%9B%B4%E6%92%AD%E5%85%83%E5%B9%B4)，元年相继涌现出了斗鱼、YY等直播服务型公司，市场爆发增长，也催促直播技术蓬勃发展。不过其业务盈利却始终是一个难点，直播该怎么套现？时隔4年，抖音淘宝等平台给出了答案，“直播带货”。催生了李佳琦、薇娅等带货明星，就连罗永浩为了替公司还债也进入了这个最能挣到快钱的行业，可见其魅力。从2016年在直播行业吃苦了4年，也培养了用户4年，钱没少花，确实挣到少，直播带货算是苦尽甘来，在加上疫情之下，实体店铺鲜有人上访，5G即将来到，会再次催促直播行业增长，技术会再次爆发。而与直播相关的技术就是音视频这一块，是时候应该引起技术人的重视了。
## *2.Introduction*{:.header2-font}
本系列文章我们要讲的主要有三个内容
- [x] 编解码器 H264/AVC
- [x] 封装容器 MPEG transport stream(short as TS) 、 FLV
- [x] 传输协议 HTTP-TS(HLS) HTTP-FLV RTMP

&emsp;&emsp;我们假象一个这样的场景，一个内容生产者如何通过网络向一个内容的消费者传输内容。首先内容生产者生产了原始数据，编解码器将其编码成有序数据，由于需要通过网络，就会存在带宽压力问题，就需要通过封装技术，进行切片分包发送，使其更易进行网络传输，而运载这些包的纽带又各有千秋，有专门为TS包运输的HLS，有专门为FLV运输的HTTP-FLV RTMP。
&emsp;&emsp;理解了上面三块的内容那么就相当于入门了,如果想了解如何实现一个从推流端到服务端再到播流端的代码实现，可以阅读这个项目的源代码[JamesfChen/river](https://github.com/JamesfChen/river)，当然也希望您能给与这个项目star

## *3.Reference*{:.header2-font}
[七牛直播云](https://developer.qiniu.com/pili/sdk/3719/PLDroidMediaStreaming-function-using)