---
layout: post
title: Java并发
description:  锁、队列、信号量、线程、线程池
tag:
- vm-language
- android
---

在java并发中我们常常遇到这样一些关键词：锁、队列、信号、线程、线程池，它们都是围绕线程衍生出来的周边，涉及到线程同步、线程通信、线程复用。

- 线程同步：锁是为了解决并发竞争资源问题，是一种线程同步方式，除了锁还有CAS、volatile
- 线程通信：队列、列表、信号是线程通信的方式，比如ArrayBlockingQueue、wait/notify、CountDownLatch、Semaphore
- 线程复用：线程复用依赖于线程池，jdk提供的线程池有四种FixedThreadPool、SingleThreadExecutor、ScheduledThreadPool、CachedThreadPool

# 线程同步

线程同步有三个特点

- 原子性:一个线程在进行写操作时，其他线程不能写
- 可见性: 一个变量被改变，立马同步到主内存，其他线程能同时知道
- 有序性：程序的执行顺序就是代码的先后顺序

synchronized(自动锁)和Lock(手动锁:AQS)、CAS同时具备上面三个特点，volatile只具备2,3不能保证原子性，但是volatile不用上锁且能保证线程安全，主要使用场景有：运算结果并不依赖变量的当前值、能够确保只有单一的线程修改变量的值(一写多读)

锁的种类也很多：乐观锁(不加锁，通过自旋实现)、悲观锁(每次都会加锁)、可重入锁、公平锁、非公平锁、轻量级锁、重量级锁

# 线程通信

CopyOnWriteArrayList

# 线程复用

线程的创建对于应用来说是一种昂贵的资源，因为涉及虚拟机到kernel整条链路，所以复用线程的方案是线程池。

为我们提供了四种线程池：单线城池、固定数量线程池、缓存线程池、工作
这四种线程池最后都会调用ThreadPoolExecutor方法，从而创建特定的线程池。

```java
public class ThreadPoolExecutor extends AbstractExecutorService {
...
  public ThreadPoolExecutor(int corePoolSize,
                              int maximumPoolSize,
                              long keepAliveTime,
                              TimeUnit unit,
                              BlockingQueue<Runnable> workQueue,
                              ThreadFactory threadFactory,
                              RejectedExecutionHandler handler) {
        if (corePoolSize < 0 ||
            maximumPoolSize <= 0 ||
            maximumPoolSize < corePoolSize ||
            keepAliveTime < 0)
            throw new IllegalArgumentException();
        if (workQueue == null || threadFactory == null || handler == null)
            throw new NullPointerException();
        this.corePoolSize = corePoolSize;
        this.maximumPoolSize = maximumPoolSize;
        this.workQueue = workQueue;
        this.keepAliveTime = unit.toNanos(keepAliveTime);
        this.threadFactory = threadFactory;
        this.handler = handler;
    }
...
}
```

- corePoolSize：核心线程数
- maximumPoolSize：最大线程数
- keepAliveTime：存活时间
- unit：存活时间的单位
- workQueue：任务的排列方式
- threadFactory：线程的工厂模式，如何创建线程
- handler：线程被reject后的处理器


## 固定线程池
```java
public class Executors {
    public static ExecutorService newFixedThreadPool(int nThreads) {
        return new ThreadPoolExecutor(nThreads, nThreads,
                                      0L, TimeUnit.MILLISECONDS,
                                      new LinkedBlockingQueue<Runnable>());
    }
}
```
可以容纳的最大线程数就是核心线程数，采用链表形式的队列，存活时间为永久。

## 单线程池

```java
public class Executors {
    public static ExecutorService newSingleThreadExecutor() {
        return new FinalizableDelegatedExecutorService
            (new ThreadPoolExecutor(1, 1,
                                    0L, TimeUnit.MILLISECONDS,
                                    new LinkedBlockingQueue<Runnable>()));
    }
}
```
只有一个线程的线程池，存活为永久，采用链表形式的队列

## 缓存线程池
```java
public class Executors {
    public static ExecutorService newCachedThreadPool() {
        return new ThreadPoolExecutor(0, Integer.MAX_VALUE,
                                      60L, TimeUnit.SECONDS,
                                      new SynchronousQueue<Runnable>());
    }
}
```
核心线程数为0，最大线程数为整数最大值，几乎可以认为无穷。存活时间为60s，采用的是同步队列

## 周期性线程池
```java
public class Executors {
    public static ScheduledExecutorService newScheduledThreadPool(int corePoolSize) {
        return new ScheduledThreadPoolExecutor(corePoolSize);
    }
}
```
ScheduledThreadPoolExecutor是ThreadPoolExecutor的子类，构造过程直接调用父类的构造器。通过采用DelayedWorkQueue队列从而实现定时执行任务的功能。

```java
public class ScheduledThreadPoolExecutor
        extends ThreadPoolExecutor
        implements ScheduledExecutorService {
        ...
    public ScheduledThreadPoolExecutor(int corePoolSize) {
        super(corePoolSize, Integer.MAX_VALUE,
              DEFAULT_KEEPALIVE_MILLIS, MILLISECONDS,
              new DelayedWorkQueue());
    }
}
```
最大线程数也是接近无穷。存活时间为10ms

# 参考资料

[Java中的21种锁，图文并茂的详细解释](https://cloud.tencent.com/developer/news/688367)

[不可不说的Java“锁”事](https://tech.meituan.com/2018/11/15/java-lock.html)

[Java线程池分析](http://gityuan.com/2016/01/16/thread-pool/)

[Java™ 7 util.concurrent API](https://www.uml-diagrams.org/java-7-concurrent-uml-class-diagram-example.html)

