---
layout: post
title: AV --- TS Container
description: 
author: 电解质
date: 2020-10-12 22:50:00
share: true
comments: true
tag: 
- app-design/av
published : true
---
## *1.Summary*{:.header2-font}
```

    PAT packet                       PMT  packet              PES packet
program_number=5            
program_map_PID=10   ---->  TS header pid=10
                            stream_type=0x0f audio
                            elementary_PID=20  ---->  TS header pid=20
                            stream_type=0x1b vedio
                            elementary_PID=22 ---->   TS header pid=22

program_number=6
program_map_PID=11  ---->  TS header pid=11
                            ....

program_number=7    
program_map_PID=12  ---->  ...                    
```

## *2.Introduction*{:.header2-font}
## *3.Reference*{:.header2-font}
[MPEG-TS 格式解析](https://blog.csdn.net/Kayson12345/article/details/81266587)
[MPEG2-TS基础](https://blog.csdn.net/rootusers/article/details/42772657)
[MPEG-TS基础2](https://blog.csdn.net/rootusers/article/details/42970859)
[MPEG transport stream](https://en.wikipedia.org/wiki/MPEG_transport_stream)
[Program-specific information](https://en.wikipedia.org/wiki/Program-specific_information)
[Packetized elementary stream](https://en.wikipedia.org/wiki/Packetized_elementary_stream#:~:text=PES%20packet%20header,-Name&text=Specifies%20the%20number%20of%20bytes,Optional%20PES%20header)
[HLS协议及TS封装](https://www.jianshu.com/p/d6311f03b81f)