---
layout: post
title: AV | AAC Codec 
description: Audio Codec
tag: 
- av
---

## 重要的文件格式

### 1.AAC文件格式
aac文件格式有两种：ADIF和ADTS

ADIF(必须从头解码，用于磁盘):
header  | body
---|---
header（） | raw_data_stream()

ADTS（可以从中间解码，用于广播电视）:
| |      |  header  | | body| | |
---|---    |---      |---      |---|---|---|
previous |syncword |header（）|error_check() |raw_data_block() |next|


音频帧的播放时间=一个AAC帧对应的采样样本的个数/采样频率(单位为s)

一帧 1024个 sample。采样率 Samplerate 44100KHz，每秒44100个sample, 所以 根据公式   音频帧的播放时间=一个AAC帧对应的采样样本的个数/采样频率

当前AAC一帧的播放时间是= 1024*1000000/44100= 22.32ms(单位为ms)


### 2.脉冲编码调制（Pulse Code Modulation，short for PCM）
modulator-demodulator(modem)
猫是一个双向的过程，即可以解调也可以调制，而pcm是其中的调制。

录制时常用参数：
- 采样频率(sampling rate)：一般有11025HZ（11KHz），22050HZ（22KHz）、44100Hz（44KHz）三种。在16位声卡中有22KHz、44KHz等几级，44KHz已相当于CD音质了，目前的常用采样频率都不超过48KHz
- 采样位数：8位和16位
- 声道数：单声道、立体声道
# Codec
## 音频codec争抢

相关专业词
```
sample rate
channel count
```

- G系列

为了VoIP，ITU-T定制了G系列，从G.711开始迭代。


- MP/ACC系列

为了小型播放器MP3，MPEG定制了MP系列，从MP2开始迭代。随着tv、数字无线、互联网流兴起，定制了AAC系列，逐渐取代MP3，期间版本经历了，最初的ACC到HE-ACC(high efficiency,高效率)。


profile
```
MPEG-2 AAC LC 低复杂度规格（Low Complexity）
MPEG-2 AAC Main 主规格
MPEG-2 AAC SSR 可变采样率规格（Scaleable Sample Rate）
MPEG-4 AAC LC 低复杂度规格（Low Complexity），现在的手机比较常见的 MP4 文件中的音频部份就包括了该规格音频文件
MPEG-4 AAC Main 主规格
MPEG-4 AAC SSR 可变采样率规格（Scaleable Sample Rate）
MPEG-4 AAC LTP 长时期预测规格（Long Term Predicition）
MPEG-4 AAC LD 低延迟规格（Low Delay）
MPEG-4 AAC HE 高效率规格（High Efficiency）
```

- AMR系列

对于ITU-T的一霸，3GPP表示也要搞个AMR系列，所以就有了开始的AMR到AMR-WB,再到AMR-WB+。


- ALAC

既然公认机构都在搞，由于自身业务需求，apple也要插一脚，所以出了ALAC


## 直播
采集数据->提前处理->编码->网络传输->解码->渲染
