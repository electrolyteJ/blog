---
layout: post
title: LRU Algorithm
description: least recently used,which apply to memory and disk cache
author: 电解质
date: 2020-03-08 22:50:00
share: false
comments: false
tag: 
- elementary/algorithm-structure
---
## *1.Summary*{:.header2-font}
Android系统提供了LruCache这么一个类用来管理资源，以防止出现OOM这样的问题。采用了LRU算法用来排序资源，最近最少被使用的资源在出现特定条件(管理的资源内存达到阈值或者管理的资源数量到达阈值)将面临着从集合中被remove。这就好比一个人在公司，每个绩效评审的周期最近最少做出贡献的人，就会被公司标记为团队中排名靠后的人，当出现裁员时那么排名靠后的人就会被remove。这里提到一个`最近最少被使用`要注意一下，因为从一个长周期来看，排名靠后的人在出现裁员之前由于贡献值多了，是有机会改变排名。
```java
    int cacheSize = 4 * 1024 * 1024; // 4MiB
    LruCache<String, Bitmap> bitmapCache = new LruCache<String, Bitmap>(cacheSize) {
        protected int sizeOf(String key, Bitmap value) {
            return value.getByteCount();
        }
     }
```
那么对于一个LRU cache的设计就应该设计到这么几点
- 定义重排逻辑,有些时根据时间来重排；有些是根据列表中元素的特点来排序不单单是时间
- 定义特定条件,到底是内存阈值，还是数量阈值或者其他的阈值

在Android中进程管理就是采用LRU算法+组件特点来重新排序，比如对于将要`被使用的存在Activity组件的进程(A)`就会被排到到列表尾部，或者对于`与A相互关联的进程`(通过bindService绑定的进程,B)也会被重排到紧挨着A进程的位置，而和B进程具有相同用户id的进程也会被排到紧挨B进程。有一种一人得道鸡犬升天的味道。对于何时清理进程，Android采用剩余内存阈值，而且其阈值有多个档位，当剩余内存处于332MB改清理哪些进程，73MB时又该清理哪些进程，当然有些进程是不能被清理的，比如system_server,清理它相当于整个framework都挂掉了，那谁还来提供服务；还有native进程，其不受system管控。如果只这样设计就会存在很多问题，有些内存占用小但是却不怎么重要，没被清理，而有些很重要单内存占用大确被清理。比如某个音乐的service进程和没有被使用的联系人进程。所以在Android系统中有个oom_adj的值，其和内存阈值存在映射关系，也分档位。先用oom_adj值判断，在用内存判断。
<!-- ## *3.Introduction*{:.header2-font} -->

