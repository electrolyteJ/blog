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
published : true
---
## *1.Summary*{:.header2-font}
&emsp;&emsp;2016年，中国互联网掀起了一场直播浪潮，这一年被称为[中国直播元年](https://baike.baidu.com/item/%E4%B8%AD%E5%9B%BD%E7%BD%91%E7%BB%9C%E7%9B%B4%E6%92%AD%E5%85%83%E5%B9%B4)，元年相继涌现出了斗鱼、YY等直播服务型公司，直播市场爆发性增长，快速推动直播技术蓬勃发展。不过其业务盈利却始终是一个难点，直播业务应该如何从用户群里获取更多更肥沃的利益？时隔4年，抖音淘宝等平台给出了答案，“直播带货”。平台催生了李佳琦、薇娅等带货明星，就连罗永浩为了替公司还债也加入了这个最能挣到快钱的行业，可见其魅力。从2016年直播行业相较于其他行业盈利能力有待提高等待了4年，直播带货算是苦尽甘来，在加上疫情之后，实体行业惨淡恢复缓慢，5G即将来到，将再次催促直播行业增长，技术会再次爆发。而与直播相关的技术就是音视频这一块，能为业务带来盈利的技术最后才能引领技术，是时候引起技术人的重视了。
## *2.Introduction*{:.header2-font}
本系列文章我们要讲的主要有三个内容
- [x] 编解码器 H264/AVC AAC
- [x] 封装容器 MPEG transport stream(short as TS) 、 FLV
- [x] 传输协议 HTTP-TS(HLS)  HTTP-FLV  RTMP

&emsp;&emsp;我们提出这样一个问题并且尝试回答它，一个内容生产者如何通过网络向一个内容的消费者传输内容。
&emsp;&emsp;首先内容生产者生产了原始数据，编解码器将其编码成有序数据，由于需要通过网络，就会存在带宽压力问题，就需要通过封装技术，进行切片分包发送，使其更易进行网络传输，而运载这些包的纽带又各有千秋，有专门为TS包运输的HLS，有专门为FLV运输的HTTP-FLV RTMP。
&emsp;&emsp;简单的了解了这样一个知识链路，那么如果能在其中某个节点扮演某个角色，那么整条链路能带来的利益就会平摊到角色上。由于利益驱动那么社会上的各个机构组织多会相互竞争这个角色。
比如说视频编解码器除了有H系列的H264还有google收购On2的VP系列
```
V系列：
"video/x-vnd.on2.vp8" - VP8 video (i.e. video in .webm)
"video/x-vnd.on2.vp9" - VP9 video (i.e. video in .webm)

H系列：
"video/3gpp" - H.263 video
"video/avc" - H.264/AVC video
"video/hevc" - H.265/HEVC video

"video/mp4v-es" - MPEG4 video

```
音频编解码器
```
"audio/mpeg" - MPEG1/2 audio layer III

AAC:
"audio/mp4a-latm" - AAC audio (note, this is raw AAC packets, not packaged in LATM!)

"audio/vorbis" - vorbis audio

AMR(3GGP)：
"audio/3gpp" - AMR narrowband audio
"audio/amr-wb" - AMR wideband audio

G系列(ITU-T):
"audio/g711-alaw" - G.711 alaw audio
"audio/g711-mlaw" - G.711 ulaw audio
```
&emsp;&emsp;对于后面的文章我们主要关注视频编解码器H264和音频编解码器MP/AAC，其中H264和MP3(后面逐渐被AAC取代)编码器广受好评的实现之一是VideoLAN 开发的x264和LAME

codec | encode|decode
---|---|---
H264 | x264 |libavcodec
MP3 | LAME|


&emsp;&emsp;而对于封装技术更是种类繁多，用于存在于文件的封装技术，用于网络传输的封装技术。这里就不做过多介绍，有兴趣维基百科自己看看[wiki](https://en.wikipedia.org/wiki/Comparison_of_video_container_formats)。网络传输协议主要使用到的HTTP-TS(HLS)  HTTP-FLV  RTMP

&emsp;&emsp;理解了这些内容就相当于半只脚入了门。如果想了解如何实现一个从推流端到服务端再到播流端的代码实现，可以阅读这个项目的源代码[JamesfChen/river](https://github.com/JamesfChen/river)，当然也希望您能给予这个项目star，因为这个项目目前的维护者和开发者都是博主我，让博主感受感受来着读者的反馈。

## *3.Reference*{:.header2-font}
[七牛直播云](https://developer.qiniu.com/pili/sdk/3719/PLDroidMediaStreaming-function-using)
[[总结]视音频编解码技术零基础学习方法](https://blog.csdn.net/leixiaohua1020/article/details/18893769)
[如何搭建一个完整的视频直播系统？](https://www.zhihu.com/question/42162310)