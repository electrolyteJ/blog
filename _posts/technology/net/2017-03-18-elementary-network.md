---
layout: post
title: 网络 | 网络协议与网络制式
description: 网络协议与网络制式
date: 2017-03-18 22:50:00
share: true
comments: true
tag: 
- network
- android
---

## *网络协议*{:.header2-font}
ietf 组织负责网络协议
![network_layer]({{ site.baseurl}}/asset/network/2017-03-18-network_layer.png)

## *网络制式*{:.header2-font}
网络制式也叫做网络类型，生活中常说的4g lte就是网络制式，其主要提供了蜂窝网络,由3gpp这个组织推广，有关3gpp可以看这个[文章](https://baike.baidu.com/item/3GPP/2373775#:~:text=3GPP%E7%AE%80%E4%BB%8B&text=3GPP%E6%88%90%E7%AB%8B%E4%BA%8E1998%E5%B9%B4,%E5%85%A5%E6%8A%80%E6%9C%AF%EF%BC%8C%E4%B8%BB%E8%A6%81%E6%98%AFUMTS%E3%80%82)

### *中国的三大运营商网络制式*{:.header3-font}

||China Telecom|China Unicom|China Mobile
|:-----:|------
|2G|CDMA|GSM|GSM
|3G|CDMA2000|WCDMA|TD-SCDMA
|4G|LTE（FDD/TDD）|LTE(FDD/TDD）|LTE(TD)
{:.inner-borders}


先来说说国内的，三大运营商都知道是中电信、中移动、中联通。

2G：
- 电信的CDMA早期是由联通那边买来的，最开始使用于军方后来运用于民间，其性能辐射小，稳定。传输的速度为9k/s。所以在表格中其他两家运营商用的都是GSM而电信用的是CMDA就可理解其中的缘由了

3G：
- 使用CDMA2000还有日本、北美、韩国
- 世界上的大部分3G网络都采用WCDMA制式
- TD-SCDMA只有中国本土专用。之前中移动带着这个号称自己自主研发的技术去参加世界通信大会，结果受到了排挤没能将其推广出去，结果只能本土使用了
过渡版本：
- 2G-3G的过渡版EDGE（图标E+），3G-4G的过渡版HSDPA（图标H+）


### *美国的四大运营商网络制式*{:.header3-font}

||Verizon Wireless|Sprint Nextel|T-Mobile USA|AT&T Wireless
|----|:-----:|------
|2G|CDMA|CDMA|GSM|GSM
|3G|CDMA2000（CDMA-EVDO）|CDMA2000（CDMA-EVDO）|CDMA2000（CDMA-EVDO）|WCDMA
|4G|LTE（FDD）|LTE（FDD）|LTE（TDD）|LTE（FDD）
{:.inner-borders}

### *拉丁美洲的运营商网络制式*{:.header3-font}
拉丁美洲最大的运营商是美洲移动通信公司，也是世界之最。旗下的下子公司Telcel（GSM/WCDMA）、Telmex、Claro、Embratel、Simple Mobile、Net、TracFone。对于其网络制式没什么好讲的,2G制式有CDMA、GSM；3G制式有CDMA2000、WCDMA。其中的Telcel是相当厉害的，市场份额70%



### 参考资料:
[互联网协议入门(一)](http://www.ruanyifeng.com/blog/2012/05/internet_protocol_suite_part_i.html)
[互联网协议入门(二)](http://www.ruanyifeng.com/blog/2012/06/internet_protocol_suite_part_ii.html)
[关于Volte](http://www.10tiao.com/html/694/201703/2652509425/1.html)