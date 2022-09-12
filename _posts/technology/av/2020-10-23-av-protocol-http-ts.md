---
layout: post
title: AV --- HTTP-TS Protocol
description: HLS
author: 电解质
date: 2020-10-23 22:50:00
share: true
comments: true
tag: 
- elementary/av
published : true
---
## *1.Summary*{:.header2-font}
&emsp;&emsp;从编解码器生产数据到封装数据技术我们已经对音视频的流程有了一定的了解，那么接下来就是了解如何通过网络运输这些数据了。
## *2.Introduction*{:.header2-font}
HLS通过下发给客户端m3u8列表指明需要播放的ts文件列表。m3u8主要有两种直播和点播,下面我们来看几个文件格式的例子。

点播
```
        #EXTM3U
        #EXT-X-TARGETDURATION:10
        #EXT-X-VERSION:3
        #EXTINF:9.009,
        http://media.example.com/first.ts
        #EXTINF:9.009,
        http://media.example.com/second.ts
        #EXTINF:3.003,
        http://media.example.com/third.ts
        #EXT-X-ENDLIST
        

```
直播
```
        #EXTM3U
        #EXT-X-VERSION:3
        #EXT-X-TARGETDURATION:8
        #EXT-X-MEDIA-SEQUENCE:2680

        #EXTINF:7.975,
        https://priv.example.com/fileSequence2680.ts
        #EXTINF:7.941,
        https://priv.example.com/fileSequence2681.ts
        #EXTINF:7.975,
        https://priv.example.com/fileSequence2682.ts
```
直播与点播的区别在于EXT-X-ENDLIST，其表示了该m3u8文件有结尾，不会在向服务器请求下一个m3u8文件。直播server端代码已经实现，可以参考这个项目[river](https://github.com/electrolyteJ/river/blob/master/server4py/app/http_ts/server.py)
## *3.Reference*{:.header2-font}
[HTTP Live Streaming](https://developer.apple.com/streaming/)