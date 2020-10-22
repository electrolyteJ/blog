---
layout: post
title: AV --- TS Container
description: 
author: 电解质
date: 2020-10-22 22:50:00
share: true
comments: true
tag: 
- app-design/av
published : true
---
## *1.Summary*{:.header2-font}
MPEG transport stream(short as TS)

```
                       4bytes               184bytes         
  +-+-+-+-+-+    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |  Packet | =  | Packet header |      Packet data                        |
  +-+-+-+-+-+    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```
### TS Header(size : 4bytes)

name |size(bit)|desc
---|---|---
sync_byte|	8	|同步字节，固定为0x47
transport_error_indicator|1|传输错误指示符，表明在ts头的adapt域后由一个无用字节，通常都为0，这个字节算在adapt域长度内
payload_unit_start_indicator|1|负载单元起始标示符，一个完整的数据包开始时标记为1
transport_priority|1|传输优先级，0为低优先级，1为高优先级，通常取0
pid	|13|pid值
transport_scrambling_control|2|传输加扰控制，00表示未加密
adaptation_field_control|2|是否包含自适应区，‘00’保留；‘01’为无自适应域，仅含有效负载；‘10’为仅含自适应域，无有效负载；‘11’为同时带有自适应域和有效负载。
continuity_counter|4|递增计数器，从0-f，起始值不一定取0，但必须是连续的

表 |PID 值
---|---
PAT|0x0000
CAT|0x0001
TSDT|0x0002
EIT,ST|0x0012
RST,ST|0x0013
TDT,TOT,ST|0x0014

### TS Body(size : 184bytes)
TS包固定文件为188字节,TS包主要有PSI和PES之分。PSI是什么？

> Program-specific information (PSI) is metadata about a program (channel) and part of an MPEG transport stream.
> The PSI data as defined by ISO/IEC 13818-1 (MPEG-2 Part 1: Systems) includes four tables: 
> - PAT (Program Association Table)
> - CAT (Conditional Access Table)
> - PMT (Program Mapping Table)
> - [NIT (Network Information Table)](https://baike.baidu.com/item/NIT%E8%A1%A8)

其中需要关注的是PAT和PMT这两个包,下面通过一个流程图讲解从而理解PAT、PMT
```

    PAT packet               PMT  packet              PES packet
program_number=0x0001            
program_map_PID=10   ---->  TS header pid=10
                            stream_type=0x0f audio
                            elementary_PID=20  ---->  TS header pid=20(PES被切成多个固定size的ts包)
                            stream_type=0x1b vedio
                            elementary_PID=22 ---->   TS header pid=22

program_number=0x0001 
program_map_PID=11  ---->  TS header pid=11
                            ....
                            NIT  packet 
program_number=0x0000   
program_map_PID=12  ---->  ...                    
```
从H264编解码器输出的数据，我们叫做Elemental Stream,数据可能是I帧，P帧或者B帧，ES数据头部会加入pts、dts等信息打包为Packet Elemental Stream(PES)。由于PES可能是音频数据也可能是视频数据或者其他种类的数据，这些PES数据可能是同一个节目产生的也可能是其他节目产生的，通过PMT就可以将这些庞杂紊乱的数据进行重新规划，将同一个节目的视频数据流、音频数据流等规划到一起。PAT注册了所有不同PMT，也可以说PAT表示了所有的节目。

理解了这些那么接一下我们就可以来看看PAT 、 PMT 、 PES

## *2.Introduction*{:.header2-font}

###  PAT((Program Associate Table) Packet
ts头字段pid固定为0x0000
```
                         4bytes                 184bytes         
  +-+-+-+-+-+    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |  Packet | =  | TS header |    Packet data                              |
  +-+-+-+-+-+    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                      
                     4bytes     1byte,0x00表示负载的开始                      
  +-+-+-+-+-+    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |  Packet | =  | TS header |      0x00      |PAT header |   filled 0xff  |
  +-+-+-+-+-+    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

name |size(bit)|desc
---|---|---
table_id|8|	PAT表固定为0x00
section_syntax_indicator|1|固定为二进制1
zero|1|固定为二进制0
reserved|2|固定为二进制11(3)
section_length|12|后面数据的长度
transport_stream_id|16|传输流ID，固定为0x0001
reserved|2|固定为二进制11(3)
version_number|5|版本号，固定为二进制00000，如果PAT有变化则版本号加1
current_next_indicator|1|固定为二进制1，表示这个PAT表可以用，如果为0则要等待下一个PAT表
section_number|8|固定为0x00 
last_section_number|8|固定为0x00  

开始循环	

name |size(bit)|desc
---|---|---
program_number|16|节目号为0x0000时表示这是NIT，节目号为0x0001时,表示这是PMT
reserved|3|固定为二进制111(7)
network_id(节目号为0时) program_map_PID(节目号为其他时)|13|节目号为0x0000时,表示这是NIT，PID=0x001f，即31节目号为0x0001时,表示这是PMT，PID=0x100，即256

结束循环

name |size(bit)|desc
---|---|---
CRC32|32|前面数据的CRC32校验码


### PMT(Program Map Table) Packet
```
                         4bytes                 184bytes         
  +-+-+-+-+-+    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |  Packet | =  | TS header |    Packet data                              |
  +-+-+-+-+-+    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                                1byte,0x00表示负载的开始
  +-+-+-+-+-+    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |  Packet | =  | TS header |   0x00         |PMT header | filled 0xff    |
  +-+-+-+-+-+    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

name |size(bit)|desc
---|---|---
table_id|8|PMT表取值随意，0x02
section_syntax_indicator|1|固定为二进制1
zero|1|固定为二进制0
reserved|2|固定为二进制11(3)
section_length|12|后面数据的长度
program_number|16|频道号码，表示当前的PMT关联到的频道，取值0x0001
reserved|2|固定为二进制11(3)
version_number|5|版本号，固定为00000，如果PAT有变化则版本号加1
current_next_indicator|1|固定为二进制1
section_number|8|固定为0x00
last_section_number|8|固定为0x00
reserved|3|固定为二进制111(7)
PCR_PID|13|PCR(节目参考时钟)所在TS分组的PID，指定为视频PID
reserved|4|固定为二进制1111(15)
program_info_length|12|节目描述信息，指定为0x000表示没有 

开始循环

name |size(bit)|desc
---|---|---
stream_type|8|流类型，标志是Video还是Audio还是其他数据，h.264编码对应0x1b，aac编码对应0x0f，mp3编码对应0x03
reserved|3|固定为二进制111(7)
elementary_PID|13|与stream_type对应的PID
reserved|4|固定为二进制1111(15)
ES_info_length|12|描述信息，指定为0x000表示没有 

结束循环

name |size(bits)|desc
---|---|---
CRC32|32|前面数据的CRC32校验码

### PES(Packet Elemental Stream) Packet

```
                     4bytes               184bytes         
  +-+-+-+-+-+    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |  TS     | =  | TS header|  adaptation field| 0x00 |  Packet data(PES)  |
  +-+-+-+-+-+    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                    6Byte          3~259Byte           max 65526Byte
  +-+-+-+-+-+    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |  PES    | =  |PES header |  optional PES header  |  Packet data(ES)    |
  +-+-+-+-+-+    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  | pes header| nalu(0x09)| 1byte |  nalu |     | nalu(0x67)|     | nalu(0x68)|     | nalu(0x65)|     |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                             随意     其他   内容       SPS     内容     PPS       内容      I帧      内容
                             
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  | pes header| nalu(0x09)| 1byte |  nalu |     | nalu(0x41)|     |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                             随意     其他   内容       P帧     内容
```
#### adaptation field

name |size(bytes)|desc
---|---|---
adaptation_field_length|1|自适应域长度，后面的字节数
flag|1|取0x50表示包含PCR或0x40表示不包含PCR
pcr|5|Program Clock Reference，节目时钟参考，用于恢复出与编码端一致的系统时序时钟STC（System Time Clock）。
stuffing_bytes|xByte|填充字节，取值0xff

什么是PCR？ 
```python
      pcr = decode_timescale  # 节目时钟参考
      ts_packet[6] = byte(pcr >> 25)
      ts_packet[7] = byte((pcr >> 17) & 0xff)
      ts_packet[8] = byte((pcr >> 9) & 0xff)
      ts_packet[9] = byte((pcr >> 1) & 0xff)
      ts_packet[10] = byte(((pcr & 0x1) << 7) | 0x7e)
```
很多文章中说pts、dts是显示时间戳，解码时间戳，但是确切地说应该叫做显示时间刻度和解码时间刻度。
```python
#decode_timestamp、presentation_timestamp : unit millisecond
#decode_timescale、presentation_timescale : unit timescale
decode_timescale = decode_timestamp * 90
presentation_timescale = presentation_timestamp * 90
```
dts与pts的区别
```
 ------------------------------>
    I     P     B     B     B     P
    1     2     3     4     5     6   读取顺序
    1     2     3     4     5     6   dts顺序
    1     5     3     2     4     6   pts顺序
点播视频dts算法:
dts = 初始值 + 90000 / video_frame_rate，初始值可以随便指定，但是最好不要取0，video_frame_rate就是帧率，比如23、30。
pts和dts是以timescale为单位的，1s = 90000 time scale , 一帧就应该是90000/video_frame_rate 个timescale。
用一帧的timescale除以采样频率就可以转换为一帧的播放时长

点播音频dts算法：
dts = 初始值 + (90000 * audio_samples_per_frame) / audio_sample_rate，audio_samples_per_frame这个值与编解码相关，aac取值1024，mp3取值1158，audio_sample_rate是采样率，比如24000、41000。AAC一帧解码出来是每声道1024个sample，也就是说一帧的时长为1024/sample_rate秒。所以每一帧时间戳依次0，1024/sample_rate，...，1024*n/sample_rate秒。

直播视频的dts和pts应该直接用直播数据流中的时间，不应该按公式计算。
```
#### PES packet header

name |size(bytes)|desc
---|---|---
Packet start code prefix|3|0x000001
Stream id|1|Examples: Audio streams (0xC0-0xDF), Video streams (0xE0-0xEF) [4][5]
PES Packet length|2|Specifies the number of bytes remaining in the packet after this field. Can be zero. If the PES packet length is set to zero, the PES packet can be of any length. A value of zero for the PES packet length can be used only when the PES packet payload is a video elementary stream.[6]
Optional PES header|variable length (length >= 3)|not present in case of Padding stream & Private stream 2 (navigation data)
Data||See elementary stream. In the case of private streams the first byte of the payload is the sub-stream number.

Optional PES header
name |size(bits)|desc
---|---|---
Marker bits|2|10 binary or 0x8 hex
Scrambling control|2|00 implies not scrambled
Priority|1|
Data alignment indicator|1|1 indicates that the PES packet header is immediately followed by the video start code or audio syncword
Copyright|1|1 implies copyrighted
Original or Copy|1|1 implies original
PTS DTS indicator|2|11 = both present, 01 is forbidden, 10 = only PTS, 00 = no PTS or DTS
ESCR flag|1	|
ES rate flag|1|
DSM trick mode flag|1|	
Additional copy info flag|1|	
CRC flag|1|	
extension flag|1|	
PES header length|8|gives the length of the remainder of the PES header in bytes
Optional fields|variable|length	presence is determined by flag bits above
Stuffing Bytes|variable|length	0xff

由于ts要求包大小固定为188bytes，所以这一帧会被切割成为多个188bytes的ts包，当然这些被切片化的碎片在打包为ts包之前，会进行加工处理，在头部加入pts dts 、pcr(如果是视频关键帧)等信息，已让解码器知道如何解析播放
```
            视频/音频类型包(Packet),一帧视频/音频数据被拆分成N个Packet
          +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
          | ts header |   adaptation field    |      payload(pes 1)     |-->第1个Packet
          +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
          | ts header |              payload(pes 2)                     |-->第2个Packet
          +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
          | ts header |                   ...                           |
          +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
          | ts header |             payload(pes n-1)                    |-->第n-1个Packet
          +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
          | ts header |   adaptation field    |      payload(pes n)     |-->第n个Packet
          +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```
### 打包
代码来源项目[JamesfChen/river](https://github.com/JamesfChen/river/blob/master/server4py/app/container/ts.py),欢迎star
```python
    def muxe(self, frame, max_duration=3000) -> PacketList:
        if frame.header.is_keyframe():
            self.__cur_keyframe = frame
        dts = frame.header.dts
        pts = frame.header.pts
        dts_timescale = dts * 90  # unit:timescale
        pts_timescale = pts * 90
        is_video = True if frame.header.is_video_packet() else False
        # print('%d dts:%d , pts:%d,is_keyframe:%s,is_video:%s,es packet size:%d' % (
        #     self.__i, dts, pts, frame.header.is_keyframe(), is_video, len(frame.payload)))
        self.__i += 1
        h = Header()
        h.packet_type = Packet_Type_VIDEO
        payload = bytearray()
        delta = pts - self.__base_time
        if delta >= max_duration and frame.header.is_keyframe():
            print('>>>生成ts文件','ts file:\u001B[31m%s\u001B[0m duration:\u001B[31m%s\u001B[0m' % (self.__ts_file.name, (delta/1000)))
            # self.__writer = open(self.path % time.time(), 'ab') if self.path else self.sw
            self.__ts_file.duration = delta
            self.cache.set(self.__ts_file)
            self.__seqnum_count += 1
            self.allocate_ts_file(self.path_template % self.__seqnum_count, self.__seqnum_count)
            self.__base_time = pts
            self.__is_first = True
        # PAT表和PMT表需要定期插入ts流，因为用户随时可能加入ts流,这个间隔比较小，通常每隔几个视频帧就要加入PAT和PMT
        if self.__is_first:
            payload.extend(self.ts_pat_packet())
            payload.extend(self.ts_pmt_packet(is_video))
            self.__is_first = False

        ts_pes_packets_size, ps = self.ts_pes_packets(
            frame.payload,
            is_video,
            frame.header.is_keyframe(),
            pts_timescale, dts_timescale
        )

        for p in ps:
            payload.extend(p)

        return PacketList(h, payload)
```



## *3.Reference*{:.header2-font}
[MPEG-TS 格式解析](https://blog.csdn.net/Kayson12345/article/details/81266587)
[MPEG2-TS基础](https://blog.csdn.net/rootusers/article/details/42772657)
[MPEG-TS基础2](https://blog.csdn.net/rootusers/article/details/42970859)
[MPEG transport stream](https://en.wikipedia.org/wiki/MPEG_transport_stream)
[Program-specific information](https://en.wikipedia.org/wiki/Program-specific_information)
[Packetized elementary stream](https://en.wikipedia.org/wiki/Packetized_elementary_stream#:~:text=PES%20packet%20header,-Name&text=Specifies%20the%20number%20of%20bytes,Optional%20PES%20header)
[HLS协议及TS封装](https://www.jianshu.com/p/d6311f03b81f)
[MD5、SHA1、CRC32值是干什么的？](https://zhuanlan.zhihu.com/p/38411551)
[h264封装ts](https://blog.csdn.net/wanglf1986/article/details/52944884)
[视频流基础知识 1-PSI/SI](https://winddoing.github.io/post/10069.html)
[I帧、P帧、B帧、GOP、IDR 和PTS, DTS之间的关系](https://www.cnblogs.com/yongdaimi/p/10676309.html#:~:text=GOP%20(%20Group%20of%20Pictures)%20%E6%98%AF,%E5%B8%A7%EF%BC%88%E5%8F%8C%E5%90%91%E5%8F%82%E8%80%83%E5%B8%A7%EF%BC%89%E3%80%82)