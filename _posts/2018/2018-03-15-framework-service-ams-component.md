---
layout: post
title: Framework层的服务 --- AMS管理四大组件
description: 来一起聊聊AMS管理四大组件
author: 电解质
date: 2018-03-15
tag:
- Android Senior Engineer
---
* TOC
{:toc}
## *1.Summary*{:.header2-font}
&emsp;&emsp;在了解了AMS的启动流程之后，我们就需要开始了解运行中的AMS是如何管理四大组件的。所以这一篇会通过图形的方式带领大家了解怎么管理的。
## *2.About*{:.header2-font}
&emsp;&emsp;在此之前我们需要知道一些背景知识

1.Handler

&emsp;&emsp;Handler在Android线程通讯中起着重要的作用，所以下面我罗列了一堆的Handler。

framework层Handler	|	运行线程
--|--
AMS.mUiHandler(UiHandler)|	android.ui
AMS.mBgHandler(Handler)|	android.bg
AMS.sKillHandler(KillHandler)|ActivityManagerService：kill
AMS.mHandler(MainHandler)|	ActivityManagerService
ASS.mHandler(ActivityStackSupervisorHandler)|	ActivityManagerService
AS.mHandler(ActivityStackHandler) |	ActivityManagerService
BroadcastQueue.mHandler(BroadcastHandler)	|ActivityManagerService
ActiveServices.mServiceMap(ServiceMap)|	ActivityManagerService
{:.inner-borders}

- AMS：ActivityManagerService
- ASS：ActivityStackSupervisor
- AS：ActivityStack

Application层Handler	|	运行线程
--|--
AT.mH(H)|main (UI线程)
{:.inner-borders}


2.ApplicationThread
&emsp;&emsp;ApplicationThread(IApplicationThread.Stub)为ActivityThread接收来自于服务端的响应，四大组件就是通过ApplicationThread接收了服务端的消息，从而实现了其调度。
## *3.Intoduction*{:.header2-font}

### *Activity*{:.header3-font}

![]({{site.asseturl}}/{{ page.date | date: "%Y-%m-%d" }}/2018-03-15-launch-activity.png)

这是一张整体的启动流程图片，能让我们大致理解了整个流程中几个重要的角色的职能。接下来我们细致讲解一下Application层和Framework层各个角色。

在应用层，Activity的生命周期如下：

![]({{site.asseturl}}/{{ page.date | date: "%Y-%m-%d" }}/2018-03-15-launch-activity-3.png)

我们可以看到，在performResume方法也就是Activity的resume阶段之后才会将View通过addView呈现在屏幕上。所以唯有handleResumeActivity执行完，View才是可见的。也就是Activity#onResum的方法中，View并不是可见的，而应该是Resumed，才可见。

在Framework层，ActivityStackSupervisor起着管理Stack的责任，而ActivityStack起着担当着管理Activity的责任。

来一张图看看

![]({{site.asseturl}}/{{ page.date | date: "%Y-%m-%d" }}/2018-03-15-launch-activity-2.png){:.white-bg-image}


### *Service*{:.header3-font}

Service的启动流程

![]({{site.asseturl}}/{{ page.date | date: "%Y-%m-%d" }}/2018-03-15-launch-service-start1.png)

![]({{site.asseturl}}/{{ page.date | date: "%Y-%m-%d" }}/2018-03-15-launch-service-start2.png){:.white-bg-image}


Service的绑定流程

![]({{site.asseturl}}/{{ page.date | date: "%Y-%m-%d" }}/2018-03-15-launch-service-bind1.png)

![]({{site.asseturl}}/{{ page.date | date: "%Y-%m-%d" }}/2018-03-15-launch-service-bind2.png){:.white-bg-image}

### *BroadcastReceiver*{:.header3-font}

![]({{site.asseturl}}/{{ page.date | date: "%Y-%m-%d" }}/2018-03-15-launch-broadcastreceiver-1.png)

广播的动态注册是在AMS中使用Map数据结构将InnerReceiver作为key，ReceiverList（DeathRecipient子类）作为value保存起来


发送有序广播
![]({{site.asseturl}}/{{ page.date | date: "%Y-%m-%d" }}/2018-03-15-launch-broadcastreceiver-2.png){:.white-bg-image}


### *ContentProvider*{:.header3-font}
![]({{site.asseturl}}/{{ page.date | date: "%Y-%m-%d" }}/2018-03-15-launch-contentprovider.png)

<!-- ## *4.Reference*{:.header2-font} -->

