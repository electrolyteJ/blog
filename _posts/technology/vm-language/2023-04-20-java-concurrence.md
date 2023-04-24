---
layout: post
title: Java并发
description:  锁、队列、信号量、线程、线程池
tag:
- vm-language
- process-thread
---
* TOC
{:toc}

在java并发中我们常常遇到这样一些关键词：锁、队列、信号、线程、线程池，它们都是围绕线程衍生出来的周边，涉及到线程同步、线程通信、线程复用。

- 线程同步：锁是为了解决并发竞争资源问题，是一种线程同步方式，比如synchronized、Lock(基于AQS，ReentrantLock、CountDownLatch、Semaphor等)、AtomicXxx(基于CAS实现)、volatile、await/notify
- 线程通信：队列、列表等数据结构是线程通信的方式，比如ArrayBlockingQueue、ConcurrentHashMap、CopyOnWriteArrayList
- 线程复用：线程复用依赖于线程池，jdk提供的线程池有四种FixedThreadPool、SingleThreadExecutor、ScheduledThreadPool、CachedThreadPool

# 线程同步

线程同步有三个特点

- 原子性:一个线程在进行写操作时，其他线程不能写
- 可见性: 一个变量被改变，立马同步到主内存，其他线程能同时知道
- 有序性：程序的执行顺序就是代码的先后顺序

synchronized(自动锁)和Lock(手动锁:AQS)、AtomicXxx(基于CAS实现)同时具备上面三个特点，volatile只具备2,3不能保证原子性，但是volatile不用上锁且能保证线程安全，主要使用场景有：运算结果并不依赖变量的当前值、能够确保只有单一的线程修改变量的值(一写多读)

锁的种类也很多：乐观锁(不加锁，通过自旋实现)、悲观锁(每次都会加锁)、可重入锁、公平锁、非公平锁、轻量级锁、重量级锁

## ReentrantLock

ReentrantLock是一种可重入、支持公平与非公平的锁，其内部类NonfairSync、FairSync继承Sync/AbstractQueuedSynchronizer(AQS)重写lock 与 tryAcquire接口。当外部调用lock进行上锁之后，会调用AQS#acquire尝试获取锁，如果初次获取失败那么接下来会在链表中等待直到获取到锁。

NonfairSync重写尝试获取的逻辑tryAcquire

```java
   protected final boolean tryAcquire(int acquires) {
            return nonfairTryAcquire(acquires);
    }
    final boolean nonfairTryAcquire(int acquires) {
            final Thread current = Thread.currentThread();
            int c = getState();
            if (c == 0) {
                if (compareAndSetState(0, acquires)) {
                    setExclusiveOwnerThread(current);
                    return true;
                }
            }
            else if (current == getExclusiveOwnerThread()) {
                int nextc = c + acquires;
                if (nextc < 0) // overflow
                    throw new Error("Maximum lock count exceeded");
                setState(nextc);
                return true;
            }
            return false;
    }
```
一把锁支持可重入需要有个state记录获取了几次，后面才能释放对应的次数，state为可重入的计数器，初始值为0，当某个线程优先获取到锁时，也就是compareAndSetState(0, acquires) 为ture,那么其他线程将等待锁的释放，非公平的方式效率高但是会导致线程饥饿

FairSync获取锁时会优先判断当前线程在tail的最右侧(tail链表：越右边越新)
```java
        protected final boolean tryAcquire(int acquires) {
            final Thread current = Thread.currentThread();
            int c = getState();
            if (c == 0) {
                if (!hasQueuedPredecessors() &&
                    compareAndSetState(0, acquires)) {
                    setExclusiveOwnerThread(current);
                    return true;
                }
            }
            else if (current == getExclusiveOwnerThread()) {
                int nextc = c + acquires;
                if (nextc < 0)
                    throw new Error("Maximum lock count exceeded");
                setState(nextc);
                return true;
            }
            return false;
        }
```

ReentrantLock使用独占方式(Exclusive Node)，只有一个线程能执行；而CountDownLatch、Semaphore的内部AQS采用了共享方式(Shared Node)，多个线程可同时执行；在实现读写分离锁ReentrantReadWriteLock读取时采用共享方式，写是采用独占方式


## AtomicXxx/AtomicReferenceXxx

AtomicXxx基于CAS实现的非阻塞、乐观的自旋锁，CAS是JVM基于汇编指令cmpxchgl实现，但是AtomicXxx也存在ABA问题、自旋时间过长等问题，而AtomicReferenceXxx可以解决ABA问题，除了改变变量也要添加版本号。

> ABA问题：线程1和线程2都从内存获取了A, 线程2将A改为B,然后再改为A,这个时候线程1发现内存依然是A，就进行修改且成功，从这里来说线程1并没有感知到数据有变化，可能发生数据不一致问题

# 线程通信

- ConcurrentHashMap
- CopyOnWriteArrayList
- ConcurrentLinkedQueue
- BlockingQueue
    - ArrayBlockingQueue
    - LinkedBlockingQueue
    - SynchronousQueue
    - DelayQueue
- BlockingDeque 
    - LinkedBlockingDeque

# 线程复用

线程的创建对于应用来说是一种昂贵的资源，因为涉及虚拟机到kernel整条链路，所以复用线程的方案是线程池。

为我们提供了四种线程池：单线程池、固定数量线程池、缓存线程池、周期性线程池。这四种线程池最后都会调用ThreadPoolExecutor方法，从而创建特定的线程池

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

[Java全栈知识体系](https://pdai.tech/md/java/thread/java-thread-x-juc-AtomicInteger.html#juc%e5%8e%9f%e5%ad%90%e7%b1%bb-cas-unsafe%e5%92%8c%e5%8e%9f%e5%ad%90%e7%b1%bb%e8%af%a6%e8%a7%a3)

[CAS、ABA问题以及AQS精讲](https://www.modb.pro/db/100023)

[线程池](https://github.com/Blankj/AndroidOfferKiller/blob/master/java/%E7%BA%BF%E7%A8%8B%E6%B1%A0.md)

[Java并发面试题](https://github.com/JsonChao/Awesome-Android-Interview/blob/master/Java%E7%9B%B8%E5%85%B3/Java%E5%B9%B6%E5%8F%91%E9%9D%A2%E8%AF%95%E9%A2%98.md)

