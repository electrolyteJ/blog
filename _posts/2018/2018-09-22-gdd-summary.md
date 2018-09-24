---
layout: post
title: 初次参加Google Developer Days
description: 见见世面
date: 2018-09-22 23:50:00
tag: 
- 呓语
share: true 
# commets: true
---
![]({{site.baseurl}}/asset/2018-09-22/gdd-3.jpg)


&emsp;&emsp;今年gdd的开始时间选定在9月下旬20号~21号，相比于去年的12月份来得更早些。整个活动占据五层楼，比之前更大。大部分的演讲会场都在一楼，二楼是展台，不仅有google自己的软件推广展台，还有一些国内公司自家产品的展台，参观展台的过程还可以获得礼物，三楼是休息处，四楼也是演讲会场，五楼是餐厅，第一天的五楼在晚上有google 游乐园活动。
&emsp;&emsp;在结束完开幕主题演讲之后，我就直奔二楼展台来收割一波礼物。结果光顾着拿礼物，却忘记了其他演讲已经开始了。所以在展台的时间和听演讲的时间总是相冲突的。当我回去听演讲在回来体验展台的产品时，礼物已经没有了。结果就昏头转向，收获反而没有，所以第二天就更有针对性去体验和听演讲。

![]({{site.baseurl}}/asset/2018-09-22/gdd-4.jpeg){:.center-image}*`图中绿色机器人是参加google 游乐园的游戏获得`*

&emsp;&emsp;展台的内容和演讲内容比较一致，有AI方向的TensorFlow，IoT方向的穿戴设备、Android Things，当然还有ARCore和跨平台技术Flutter ( 这里有个猜测，在演讲的内容中PWA也是跨平台的一种，但是在展台却没有看到，可能google自己对于这个也不是很看好吧，尽管在演讲的时候总能听到高效、便捷这些词。)，等一些其他的，比如营销策略、工具，产品设计。

# *TensorFlow*{:.header2-font}
&emsp;&emsp;展台里面除了有TensorFlow的礼物之外，google还提供了很多机器学习的资源，有汉化的[机器学习](https://developers.google.com/machine-learning/crash-course/ml-intro?hl=zh-cn)网站；面向在校学生的机器学习冬令营；还有一些机器学习的具体应用场景，比如猜画小歌、在Android Things上面的应用、其他大厂的应用。在演讲方面，机器学习也是受到了高度重视，包括了从入门到深入的分享。这里说一个题外话，当时有个叫做“编写机器学习的7个步骤”的分享，我晚到了5分钟，结果门口挤满了人在听演讲。可见对于这样一个实操性强的、能有大神带你入门的机器学习分享是多么受到欢迎。以及午餐的时候也听到旁人都讨论关于机器学习的方方面面。所以相对于Android，google对于TensorFlow的推广更加重视，Android这位宠儿正在渐渐地被TensorFlow这位新宠取代。

![]({{site.baseurl}}/asset/2018-09-22/gdd-10.jpg){:.center-image}*`机器学习应用`*

![]({{site.baseurl}}/asset/2018-09-22/gdd-57.jpg)

# *ARCore*{:.header2-font}
&emsp;&emsp;我在体验ARCore时，最为尴尬的莫过于软件突然卡住了，在场的人都面面相觑，然后仔细一看手机型号vivo nex，升降摄像头。当时差点没有憋住笑出来，这款手机也没能驾驭得了google的软件。工作人员还一顿解释道，之前是不会这样的可能是由于使用时间太长了。对于AR的推广不光有google自己在shopping方面的软件，还有其他公司，比如网易云推出的AR游戏。除了这些，这次还有ARCore Codelab,偏向于实操性的。需要提前报名现场签到才能进入，我对于这个并不是很感兴趣所以就没有报名。不过有朋友进去之后据她说可以拿到礼物，才感觉自己错过什么。
![]({{site.baseurl}}/asset/2018-09-22/gdd-11.jpg)


# *IoT*{:.header2-font}
&emsp;&emsp;google在穿戴方面主要是推广一些设备制造公司和一些手表公司的穿戴设备。在演讲内容也有这部分的分享，比如wear OS应用的设计、表盘的设计。正好自己对于这方面准备多多了解一下。现如今的Android手机市场并不如前些年那么好挣钱，市场更多趋于正常，当时在风口飞翔的猪，有的掉下来，有的长了翅膀。大部分手机厂商都在求变，做智能穿戴设备、做智能硬件等，都希望在落地之前长出翅膀或者拥抱另外一个风口。
&emsp;&emsp;在体验`Wear OS 家居管理`时，可以通过手表的按钮控制房间里的灯，突然想到有没有一种可能通过一些定义好的手势或者定义好的约定来唤醒房间里的灯。比如，拍个掌、或者轻轻敲击手表两下等。当然了，手表应该不会发展到《名侦探柯南》动漫里面那种能够发射麻醉针的地步吧，然后给医务人员使用。

![]({{site.baseurl}}/asset/2018-09-22/gdd-56.jpg)

![]({{site.baseurl}}/asset/2018-09-22/gdd-36.jpg)

![]({{site.baseurl}}/asset/2018-09-22/gdd-1.jpeg)

# *Flutter*{:.header2-font}
&emsp;&emsp;终于说到这里了，Flutter想必才是现如今Android开发者最为关心的。有的人说赶紧学，有的人说先不要学，那么到底学不学？先保持关注，感受感受风口有没有风吧。不过说到学，google在这次大会中也从入门到深入的为我们讲解了Flutter，就是不知道Flutter是`扶不起的阿斗`还是`生子当如孙仲谋`。而在国内闲鱼使用Flutter是首当其冲，还是挺配这种愿意踩坑的勇气。 现如今的大前端趋势越来越明显了，只会一门java语言会越来越限制自身的发展，还需要学习HTML、CSS、JavaScript这些前端知识。这真的是学无止境了。

![]({{site.baseurl}}/asset/2018-09-22/gdd-23.jpg)

![]({{site.baseurl}}/asset/2018-09-22/gdd-35.jpg)

# *google 游乐园*{:.header2-font}
&emsp;&emsp;第一天晚上的google游乐园，有打碟的小姐姐，有精美的礼物，有各种游戏，还有各种吃的。
![]({{site.baseurl}}/asset/2018-09-22/gdd-38.jpg)

![]({{site.baseurl}}/asset/2018-09-22/gdd-39.jpg)

![]({{site.baseurl}}/asset/2018-09-22/gdd-40.jpg)

![]({{site.baseurl}}/asset/2018-09-22/gdd-41.jpg)

![]({{site.baseurl}}/asset/2018-09-22/gdd-43.jpg)

# *饮食*{:.header2-font}
![]({{site.baseurl}}/asset/2018-09-22/gdd-52.jpg){:.header2-font}*午餐*

![]({{site.baseurl}}/asset/2018-09-22/gdd-53.jpg){:.header2-font}*午餐场地*

![]({{site.baseurl}}/asset/2018-09-22/gdd-59.jpg){:.header2-font}*茶歇*

# *其他*{:.header2-font}
&emsp;&emsp;放一些妹子和有趣的照片，让大家感受一下，我眼里看到的程序员和媒体看到的程序员是两种群体，工程师也可以生活得有趣。
![]({{site.baseurl}}/asset/2018-09-22/gdd-54.jpg)

![]({{site.baseurl}}/asset/2018-09-22/gdd-55.jpg)


![]({{site.baseurl}}/asset/2018-09-22/gdd-60.jpg)

![]({{site.baseurl}}/asset/2018-09-22/gdd-62.jpg){:.center-image}*朋友偷偷拍的小姐姐*

![]({{site.baseurl}}/asset/2018-09-22/gdd-64.jpg)


![]({{site.baseurl}}/asset/2018-09-22/gdd-68.jpg){:.center-image}*如果说我对google是一种什么感情，应该是这张图的这种感情*

&emsp;&emsp;最后说点题外话，很感谢朋友提醒我参加这一次`Google Developer Days`，这些年太过于关注技术，闭门造车，不是在学习技术就是在学习技术的路上，除了加班就是加班，而忽视了生活忽视了周边，因此也碰到了很多的槛。如朋友说地出来见见世面。技术归根到底还是要服务于生活，从生活出发，学习生活。用一句鞭策一下自己，`驽马十驾功在不舍 --- 《劝学》`

------------------

