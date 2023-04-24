---
layout: post
title: 网络 | 文件下载器DownloadProvider
description: DownloadProvider是Android团队开发的文件下载系统，让我们来看看它是如何设计的
date: 2018-01-23 22:50:00
share: true
comments: true
tag:
- network
- android
---
* TOC
{:toc}
&emsp;&emsp;为什么网上的文件下载系统那么多，我要从DownloadProvider开始呢 ? 主要有这几点：

- DownloadProvider是Android团队开发的，其软件设计和代码健硕性值得我们学习。
- DownloadProvider在Android2.3的时候就有了，经历这么多的版本，我们也能从中看到被重构的痕迹，并学习代码的可维护性。

&emsp;&emsp;DownloadProvider是Android团队开发的一款文件下载系统，提供给任何的应用使用。如果你的应用没有集成自己的文件下载系统的话，那么这一款刚好值得一用。如果没有使用过或者不熟练，可以参考这一篇文章[DownloadManager的使用](http://www.trinea.cn/android/android-downloadmanager/)。DownloadManager是一个提供给开发者的操作DownloadProvider的接口。这款文件下载系统，主要用到了关系型数据库来做数据存储（packages/providers/DownloadProvider），利用sharedUserId让DownloadProvider应用运行在media进程，可以让开发者跨进程调用，还有实现断点续传等特性
知道了这些知识之后，来啃点源码看看如何设计文件下载系统。

&emsp;&emsp;接下来，我准备先从数据层来分析，然后在自上而下，从用户角度分析

# *DataBase ORM*
&emsp;&emsp;先来看看数据的表形式和Java Bean关联。

![]({{site.baseurl}}/asset/2018-01-23/2018-01-23-DownloadProvider-orm.png)

&emsp;&emsp;数据库一共创建两张表：request_headers、download。通过DownloadManager$Request，向数据库插入开发者提供的数据，比如下载地址、下载到sd卡后的文件名等等。而通过将两张表的数据都保存到DownloadInfo类之后，就可以开始从服务端下载资源了，为了处理网络环境的不稳定的问题，DownloadThread$DownloadInfoDelta提供了某个时刻下载的进度，并且会将数据更新到数据库中。这样可以提供断点续传的功能。当下载完成会通过广播发送通知，提醒用户。

# *DownloadProvider uri设计*
&emsp;&emsp;知道了数据的关系之后，由于使用了ContentProvider来暴露数据，所以还需要设计uri，从而让外部能过安全的访问数据。

![]({{site.baseurl}}/asset/2018-01-23/2018-01-23-DownloadProvider-uri.png)

&emsp;&emsp;我们只要关注前四个就行，其余不做讨论。对于这个DownloadProvider uri 的设计，有些代码看起来有点丑而且没有按照官网说的来做。比如authority，官网说要采用`com.example.app.provider`这种命名规则才确保唯一性，而DownloadProvider却使用了downloads；还有定义契约类并没有像官网定义的那样，以xxxContract的命名，而是叫做Downloads。

&emsp;&emsp;对于uri我们来做个简单的划分

- my_downloads:表示所有行
- my_downloads/# ： 表示一行
- all_downloads:表示所有行
- all_downloads/# ： 表示一行

我们就my_downloads和all_downloads来做个讨论，先来看看路径权限。

![]({{site.baseurl}}/asset/2018-01-23/2018-01-23-DownloadProvider-path-permission.png)

从这里我们可以看出my_downloads是给外部插入数据用的，而在数据库更新和删除的代码中all_downloads是用来更新数据、删除数据，all_downloads更多是提供给内部使用，不过DownloadManager#setAccessAllDownloads可以设置外部访问是的uri为all_downloads。

# *DownloadProvider的下载流程*


![]({{site.baseurl}}/asset/2018-01-23/2018-01-23-DownloadProvider-flowchart.png)

&emsp;&emsp;通过DownloadManager$Request类将外部数据插入到数据库中，当数据插入完成时，会调用service，并且开启相应的线程。通过`new Thread().start()`调用线程利用SparseArray管理线程，说句实话看到这里我才知道，这个代码已经年代久远，现在科学管理线程的方式已经采用线程池了。这里可以说个东西，通过JobInfo内部类Builder方法setRequiredNetworkType选择在wifi下载，3g网络不下载，而开发者就是可以通过DownloadManager的内部类Request#setAllowedNetworkTypes向obInfo$Builder#setRequiredNetworkType方法提供不同的参数从而实现下载。

&emsp;&emsp;再来说说DownloadInfoDetal这个类，主要用于实现断点续传。当数据开始传输之后，客户端已收到的数据字节大小会被写入到数据库，数据会通过ParcelFileDescriptor类进行保存操作，一旦网络断开，再次恢复网络时，通过从数据库获取到的已接收的数据字节大小，并结合http header`Range：bytes=当前已接收的数据字节大小`，发送给服务端，服务端就会在之前断开的地方继续补传剩余的数据。

&emsp;&emsp;有一点值得一说，当客户端在接受服务端数据时，通过DownloadProvider#openFile，打开一个指定路径的文件，这个路径可以通过Request#setDestinationInExternalFilesDir，指定下载到sd卡。




# *参考资料*
[Creating a Content Provider](https://developer.android.com/guide/topics/providers/content-provider-creating.html)
[在Android 5.0中使用JobScheduler](http://www.jcodecraeer.com/a/anzhuokaifa/androidkaifa/2015/0403/2685.html)