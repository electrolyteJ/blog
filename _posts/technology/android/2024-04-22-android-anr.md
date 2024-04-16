---
layout: post
title: Android | ANR
description: Application Not Responsable
tag:
- android
- perf
---
* TOC
{:toc}

ANR类型

- input dispatch timeout
- service timeout
- brocastrecevier timeout
- contentprovider timeout

## input dispatch timeout

```
---> InputDispatch#dispatchOnce
---> InputDispatch#onAnrLocked
---> InputManagerService#notifyANR
---> ActivityManagerService#inputDispatchingTimedOut
---> ActivityManagerService#appNotResponding
```

ActivityManagerService#appNotResponding

- 采集 cpu 负荷
- 发送信号量SIGNAL_QUIT给 发生anr的进程Signal Catcher线程，让其采集所有线程堆栈

service 、 brocast recevier、contentprovider 和 input dispatch 采集anr 都是一样


## 参考资料

- [ANR机制以及问题分析](https://duanqz.github.io/2015-10-12-ANR-Analysis)
