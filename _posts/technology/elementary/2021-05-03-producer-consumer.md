---
layout: post
title: 生产者-消费者
description: 异步的基石
author: 电解质
date: 2021-05-03 22:50:00
share: true
comments: false
tag: 
- elementary/async
published : true
---
## *1.Summary*{:.header2-font}
来谈谈OkHttp 和 Android平台提供的生产者-消费者模型


..| 消费者|生成者|产品|Android消费的场所
--|--|--|--|--|
OkHttp | TaskRunner|TaskQueue|Task|其他线程
Android| Looper| MessageQueue|Message(Handler,Runnable)|主线程、其他线程、跨进程

生产者-消费者模型是一种实现线程通信的方式，其核心是利用queue先进先出的特点，生产者负责将消息(或者事件)写入到queue，而消费者负责从queue读取。
## *2.Introduction*{:.header2-font}
Android平台的生产者消费者模型使用范围更加广泛
- 支持跨进程，支持跨线程
- 使用epoll唤醒睡眠，linux提供的系统调用
- 使用链表保存Message，插入删除有优势

OkHttp生产者消费者模型
- 支持跨线程
- 使用wait/notifyXXX唤醒睡眠，java虚拟机提供的调用
- 使用数组保存Task，查询有优势

### *OkHttp生产者消费者模型*{:.header3-font}

生产者TaskQueue
{:.filename}
```java
class TaskQueue internal constructor(
  internal val taskRunner: TaskRunner,
  internal val name: String
) {
    internal val futureTasks = mutableListOf<Task>()
}
```
<!-- 看到上面使用数组保存Task，你应该会奇怪为什么不和Android平台一样使用链表？其实这个问题不难回答，OkHttp用了数组必然是看中其查询的复杂度比链表好， -->
生产者TaskQueue使用了数组保存了产品Task。在OkHttp中生产者可以很多个，比如RealConnectionPool连接池持有一个cleanupQueue，用来存放定时清理连接的任务cleanupTask，在Http2Connection中的生产者更多了，比如writerQueue用来存放发送心态包的任务还有pushQueue保存server push的任务，但是对于消费者TaskRunner独独只会有一个。

消费者TaskRunner
{:.filename}
```java
  /** Queues with tasks that are currently executing their [TaskQueue.activeTask]. */
  private val busyQueues = mutableListOf<TaskQueue>()

  /** Queues not in [busyQueues] that have non-empty [TaskQueue.futureTasks]. */
  private val readyQueues = mutableListOf<TaskQueue>()

  fun awaitTaskToRun(): Task? {
    this.assertThreadHoldsLock()

    while (true) {
      if (readyQueues.isEmpty()) {
        return null // Nothing to do.
      }

      val now = backend.nanoTime()
      var minDelayNanos = Long.MAX_VALUE
      var readyTask: Task? = null
      var multipleReadyTasks = false

      // Decide what to run. This loop's goal wants to:
      //  * Find out what this thread should do (either run a task or sleep)
      //  * Find out if there's enough work to start another thread.
      eachQueue@ for (queue in readyQueues) {
        val candidate = queue.futureTasks[0]
        val candidateDelay = maxOf(0L, candidate.nextExecuteNanoTime - now)

        when {
          // Compute the delay of the soonest-executable task.
          candidateDelay > 0L -> {
            minDelayNanos = minOf(candidateDelay, minDelayNanos)
            continue@eachQueue
          }

          // If we already have more than one task, that's enough work for now. Stop searching.
          readyTask != null -> {
            multipleReadyTasks = true
            break@eachQueue
          }

          // We have a task to execute when we complete the loop.
          else -> {
            readyTask = candidate
          }
        }
      }

      // Implement the decision.
      when {
        // We have a task ready to go. Get ready.
        readyTask != null -> {
          beforeRun(readyTask)

          // Also start another thread if there's more work or scheduling to do.
          if (multipleReadyTasks || !coordinatorWaiting && readyQueues.isNotEmpty()) {
            backend.execute(runnable)
          }

          return readyTask
        }

        // Notify the coordinator of a task that's coming up soon.
        coordinatorWaiting -> {
          if (minDelayNanos < coordinatorWakeUpAt - now) {
            backend.coordinatorNotify(this@TaskRunner)
          }
          return null
        }

        // No other thread is coordinating. Become the coordinator!
        else -> {
          coordinatorWaiting = true
          coordinatorWakeUpAt = now + minDelayNanos
          try {
            backend.coordinatorWait(this@TaskRunner, minDelayNanos)
          } catch (_: InterruptedException) {
            // Will cause all tasks to exit unless more are scheduled!
            cancelAll()
          } finally {
            coordinatorWaiting = false
          }
        }
      }
    }
  }
```
消费者TaskRunner不停向生产者TaskQueue取task。
对于一个消费者来说可以向多家生产厂商(readyQueues = mutableListOf<TaskQueue>())消费，每个生产厂商提供的产品task按照时间排序，距离现在最近排在队伍头部。
- 如果多家生产厂商的产品符合一定条件(任务执行的时间<=当前时间)，那么就会有多个生产厂商的产品被消费者购买。
- 如果多家生产厂商有那么几家生产线超前，可以提前预定，那么就会约定一个发售时间(minDelayNanos)让消费者等待,到时消费者再抢购，当然了，如果本来没有的突然插入一款新的产品也会打破这个等待的时间，重新抢购。
- 如果多家生产厂商有多没有产品了，那么就会停止任务轮询。

上面的代码我们可以看到Okhttp中的任务生成消费有线程的切换，线程池为缓存池，没有核心线程，不限制线程数，保活60s，及其短暂。

### *Android生产者消费者模型*{:.header3-font}
Android的生产者MessageQueue保存产品的方式不同于OkHttp的生产者TaskQueue，MessageQueue的产品Message使用链表结构来保存，在插入删除方便比数组有优势，不过查询就是劣势。

生产者MessageQueue
{:.filename}
```java
Message next() {
        ...
        
        for (;;) {
            ...
            nativePollOnce(ptr, nextPollTimeoutMillis);

            synchronized (this) {
                // Try to retrieve the next message.  Return if found.
                final long now = SystemClock.uptimeMillis();
                Message prevMsg = null;
                Message msg = mMessages;
                if (msg != null && msg.target == null) {
                    // Stalled by a barrier.  Find the next asynchronous message in the queue.
                    do {
                        prevMsg = msg;
                        msg = msg.next;
                    } while (msg != null && !msg.isAsynchronous());
                }
                if (msg != null) {
                    if (now < msg.when) {
                        // Next message is not ready.  Set a timeout to wake up when it is ready.
                        nextPollTimeoutMillis = (int) Math.min(msg.when - now, Integer.MAX_VALUE);
                    } else {
                        // Got a message.
                        mBlocked = false;
                        if (prevMsg != null) {
                            prevMsg.next = msg.next;
                        } else {
                            mMessages = msg.next;
                        }
                        msg.next = null;
                        if (DEBUG) Log.v(TAG, "Returning message: " + msg);
                        msg.markInUse();
                        return msg;
                    }
                } else {
                    // No more messages.
                    nextPollTimeoutMillis = -1;
                }
                
                ...
                
                // Process the quit message now that all pending messages have been handled.
                if (mQuitting) {
                    dispose();
                    return null;
                }
                
                ...
                if (pendingIdleHandlerCount <= 0) {
                    // No idle handlers to run.  Loop and wait some more.
                    mBlocked = true;
                    continue;
                }
                ...
            }
                
        }
}
```
MessageQueue#next是获取Message的方法，如果消息是异步消息，那么就不会被barrier拦住，barrier的功能是拦住非异步消息的被消费，这样就能把所有的cpu资源都给先要处理的事情，Choreographer就利用barrier拦住非异步的消息，然后递归View数。如果没有消息那么就会调用epoll编写native接口进行wait。wait这一块OkHttp的消费者TaskRunner则是基于java wait,这个到底孰强孰弱，有机会在看看，关于epoll的使用可以移步[这里代码](https://github.com/deltajf/attack-on-titan/blob/master/guard/src/main/jni/guard/event.cpp)

消费者Looper
{:.filename}
```java
 public static void loop() {
        final Looper me = myLooper();
        ...
        final MessageQueue queue = me.mQueue;

        // Make sure the identity of this thread is that of the local process,
        // and keep track of what that identity token actually is.
        Binder.clearCallingIdentity();
        final long ident = Binder.clearCallingIdentity();

        for (;;) {
            Message msg = queue.next(); // might block
            ...
            try {
                msg.target.dispatchMessage(msg);
                end = (slowDispatchThresholdMs == 0) ? 0 :
            } finally {
            ...
            }
            ...
            msg.recycleUnchecked();
        }
    }
```
Android的消费者Looper比起OkHttp的消费者TaskRunner代码，就是循环处理消息。这里要说一下由于每个线程都会有自己的Looper(通过ThreadLocal实现)，那么对于主线程Looper来说，当其他线程enqueueMessage消息到MessageQueue(这里MessageQueue对象被synchronized，避免MessageQueue对象被操作)之后，在取消息的时候始终是在主线程(这里去消息也对MessageQueue对象synchronized)。

其实如果理解了上面的生产者消费者模型，那么对于kotlin的协程之间的切换，RxJava的主线程与其他线程之间的切换，就不难理解。
