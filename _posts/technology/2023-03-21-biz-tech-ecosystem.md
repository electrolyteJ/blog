---
layout: post
title: 技术生态 与 商业生态
description: 技术生态与商业生态
share: false
comments: false
tag:
# - react native
- cross-platform
- android
---

# 技术生态(Technology Ecosystem)

指标|微信小程序|react native/expo|flutter|对比结果
|---|---|---|---|---
招聘需求|很多|很多|一般|微信小程序最多这点毋庸置疑
渲染方式|webview渲染|平台渲染|自渲染|自渲染> 平台渲染 > webview渲染
性能|较差|一般|很多| 各家平台最大的差异在于渲染，而其也影响着性能
开发者体验|很好|一般|很好|微信小程序与flutter都将生态做得很好，答疑开发工具等
原生集成|较差|一般|很好|flutter原生集成工具更好
共享代码、知识与开发者|很好|很好|很好|react native胜于flutter，在于reactjs除了在react natvie的使用还覆盖了服务端、前端
社区|微信小程序社区|reactjs社区+react native社区|flutter社区|都不错
代码推送|支持|支持|不支持|react native在做得更好，即能支持热更新也可以实现热修复
ui一致性|很好|一般| 很好|由于react native是依赖平台渲染所以ui存在差异，也是其特色，保持平台风格
跨平台|移动/PC|移动/PC/Web|移动/PC/Web|大家都在跨端

微信小程序日活：4.5亿
ColorOS日活:5亿

[我不认为Flutter比React Native好](https://mp.weixin.qq.com/s/YzGHdBBKh4UZPvKvy6IQ6w)

[如何理解 Flutter 路由源码设计？\| 开发者说·DTalk](https://mp.weixin.qq.com/s/DZB3OPYiYvhJMZssWK67Sw)

[基于Web内核的微信小程序框架实践](https://mp.weixin.qq.com/s/vEu2Ft4c6LHPeUBHChjfFA)

# 商业生态(Business Ecosystem)

目前面向第三方开发者的跨端框架是小程序、快应用，而flutter/react native主要是给公司内部开发使用，所以接下来需要对比各家头部公司的小程序商业生态。

头部公司的小程序生态

- 社交类：微信/QQ
- 电商类：淘宝/京东/美团
- 办公：飞书/钉钉
- 短视频：抖音
- 支付：支付宝
- ...

我们对一些有超级流量的小程序平台做了分类，其中对于`工具类/资讯类/小说类/生活服务类`的小程序主要在微信小程序平台和抖音小程序平台、快应用平台投放，因为这些平台想象空间更大，市场需求更大，下面我们主要对这个几个小程序平台进行对比分析。

指标|微信小程序平台|抖音小程序平台|快应用平台
--|--|--|--
服务市场/服务商|[微信服务市场](https://fuwu.weixin.qq.com/)|[抖音服务市场](https://developer.open-douyin.com/service-market/home/recommend)/[抖音服务商](https://partner.open-douyin.com/)|[快应用服务商](https://www.quickapp.cn/contactUs/supplier)
后端接口OpenAPI|有|有|无
云开发|有|无|无
数据分析|有|无|无
性能监控|有|无|无

小程序服务商

- [微盟](https://www.weimob.com/website/topic/xcx1)
- [有赞](https://www.youzan.com/intro/landing/weapp/?from_source=google_sem_xcx_11009&gclid=CjwKCAiA_6yfBhBNEiwAkmXy5yIADVPDjRwMf0ribfi6KXLaUOsv35ywX4ipIXNo2-gu2_223hwJWBoCIeAQAvD_BwE)




