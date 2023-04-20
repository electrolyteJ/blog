---
layout: post
title:  Android平台的线程切换 
description: AsyncTask、 IntentService
tag:
- android
- process-thread
---
* TOC
{:toc}

# IntentService

IntentService的主要是为了解决在Service开启线程后还要手动关闭Service的问题。IntentService提供了onHandleIntent生命周期接口，让开发者可以在工作线程做io等耗时操作。

```java
 @Override
    public void onCreate() {
        // TODO: It would be nice to have an option to hold a partial wakelock
        // during processing, and to have a static startService(Context, Intent)
        // method that would launch the service & hand off a wakelock.

        super.onCreate();
        HandlerThread thread = new HandlerThread("IntentService[" + mName + "]");
        thread.start();

        mServiceLooper = thread.getLooper();
        mServiceHandler = new ServiceHandler(mServiceLooper);
    }
    @Override
    public void onStart(@Nullable Intent intent, int startId) {
        Message msg = mServiceHandler.obtainMessage();
        msg.arg1 = startId;
        msg.obj = intent;
        mServiceHandler.sendMessage(msg);
    }
```
在onCreate方法中，构造了HandlerThread。该类作用会在工作线程开启一个Looper，并且可以通过工作线程的Handler类在主线程发送消息，然后切换到工作线程。


```java
 private final class ServiceHandler extends Handler {
        public ServiceHandler(Looper looper) {
            super(looper);
        }

        @Override
        public void handleMessage(Message msg) {
            onHandleIntent((Intent)msg.obj);
            stopSelf(msg.arg1);
        }
    }
```
这里我们可以看到onHandleIntent是在工作线程被调用的，所以在onHandleIntent里面的操作都是想io这种耗时操作


# AsyncTask


静态初始化一个线程池ThreadPoolExecutor，线程池最大可容纳线程CPU_COUNT * 2 + 1,采用阻塞队列.

另外一个为SerialExecutor，采用deque队列。deque中的每个任务执行完都会执行下一个任务。

AsyncTask#execute调用之后，会将Params类型转化成WorkerRunnable任务，然后将任务添加到SerialExecutor线程池，SerialExecutor线程池主要用于取任务，主要是通过轮询的策略拿取数据。然后将任务发给ThreadPoolExecutor线程池。

```java
    public static final Executor THREAD_POOL_EXECUTOR;

    static {
        ThreadPoolExecutor threadPoolExecutor = new ThreadPoolExecutor(
                CORE_POOL_SIZE, MAXIMUM_POOL_SIZE, KEEP_ALIVE_SECONDS, TimeUnit.SECONDS,
                sPoolWorkQueue, sThreadFactory);
        threadPoolExecutor.allowCoreThreadTimeOut(true);
        THREAD_POOL_EXECUTOR = threadPoolExecutor;
    }
    ...
    public static final Executor SERIAL_EXECUTOR = new SerialExecutor();

    ...

    private static volatile Executor sDefaultExecutor = SERIAL_EXECUTOR;
    ...
     private static class SerialExecutor implements Executor {
        final ArrayDeque<Runnable> mTasks = new ArrayDeque<Runnable>();
        Runnable mActive;

        public synchronized void execute(final Runnable r) {
            mTasks.offer(new Runnable() {
                public void run() {
                    try {
                        r.run();
                    } finally {
                        scheduleNext();
                    }
                }
            });
            if (mActive == null) {
                scheduleNext();
            }
        }

        protected synchronized void scheduleNext() {
            if ((mActive = mTasks.poll()) != null) {
                THREAD_POOL_EXECUTOR.execute(mActive);
            }
        }
    }
```
通过AsyncTask完成异步操作有两种。一种是传像url这样的参数，另外一种是传入Runnable（该类其实是url被包装之后的任务）
```java
    ...

   @MainThread
    public final AsyncTask<Params, Progress, Result> execute(Params... params) {
        return executeOnExecutor(sDefaultExecutor, params);
    }
    ...
       @MainThread
    public static void execute(Runnable runnable) {
        sDefaultExecutor.execute(runnable);
    }
    ...
```

在主线程调用execute方法,executeOnExecutor方法会被调用
```java
    @MainThread
    public final AsyncTask<Params, Progress, Result> executeOnExecutor(Executor exec,
            Params... params) {
        if (mStatus != Status.PENDING) {
            switch (mStatus) {
                case RUNNING:
                    throw new IllegalStateException("Cannot execute task:"
                            + " the task is already running.");
                case FINISHED:
                    throw new IllegalStateException("Cannot execute task:"
                            + " the task has already been executed "
                            + "(a task can be executed only once)");
            }
        }

        mStatus = Status.RUNNING;

        onPreExecute();

        mWorker.mParams = params;
        exec.execute(mFuture);

        return this;
    }
```
我们都知道Android开发文档建议对AsyncTask类的四个方法进行重写，他们的调用顺序为onPreExecute，doInBackground，onProgressUpdate(Progress...)，onPostExecute(Result)。onPreExecute是一个运行在主线程的方法，用于做一些准备工作。从外面传进了的参数会被保存到WorkerRunnable<Params, Result>这个泛型类中，该类是Callable<Result>接口的实现类，Callable类似于Runnable，只是它有返回值。

使用线程池开始任务之后，接下来会发生这样的事情

```java
    mWorker = new WorkerRunnable<Params, Result>() {
            public Result call() throws Exception {
                mTaskInvoked.set(true);
                Result result = null;
                try {
                    Process.setThreadPriority(Process.THREAD_PRIORITY_BACKGROUND);
                    //noinspection unchecked
                    result = doInBackground(mParams);
                    Binder.flushPendingCommands();
                } catch (Throwable tr) {
                    mCancelled.set(true);
                    throw tr;
                } finally {
                    postResult(result);
                }
                return result;
            }
        };

        mFuture = new FutureTask<Result>(mWorker) {
            @Override
            protected void done() {
                try {
                    postResultIfNotInvoked(get());
                } catch (InterruptedException e) {
                    android.util.Log.w(LOG_TAG, e);
                } catch (ExecutionException e) {
                    throw new RuntimeException("An error occurred while executing doInBackground()",
                            e.getCause());
                } catch (CancellationException e) {
                    postResultIfNotInvoked(null);
                }
            }
        };
```

先调用WorkerRunnable#call,完成任务之后FutureTask会得到任务的结果。

在调用WorkerRunnable#call过程中，我们看到了doInBackground方法，通过重写这个方法，可以让我们在工作线程做一些跟io一样的耗时操作。在doInBackground方法里可以调用publishProgress方法，而该方法会通过Handler类从工作线程切换到主线程调用onProgressUpdate方法，实现进度条的效果。当我们执行完任务之后就会就会通过Handler切换到主线程调用onPostExecute方法实现UI刷新


# 其他

## Activity.runOnUiThread(Runnable)
```java
    @Override
    public final void runOnUiThread(Runnable action) {
        if (Thread.currentThread() != mUiThread) {
            mHandler.post(action);
        } else {
            action.run();
        }
    }
```
工作线程调用该方法是，会通过Handler的post方法切换到主线程，并且刷新ui。如果是主线程直接就执行刷新ui的工作

## View.post(Runnable)/View.postDelayed(Runnable, long)
post和postDelayed类似，所以只分析postDelayed足以

```java
    public boolean postDelayed(Runnable action, long delayMillis) {
        final AttachInfo attachInfo = mAttachInfo;
        if (attachInfo != null) {
            return attachInfo.mHandler.postDelayed(action, delayMillis);
        }

        // Postpone the runnable until we know on which thread it needs to run.
        // Assume that the runnable will be successfully placed after attach.
        getRunQueue().postDelayed(action, delayMillis);
        return true;
    }
```
- AttachInfo的Handler对象来源于ViewRootImpl$ViewRootHandler,而ViewRootHandler是用来更新UI的。所以参考前面说的，postDelayed的意义不难理解。
- 通过getRunQueue方法获取HandlerActionQueue对象，该对象按照队列的形式发送消息，然后在ViewRootImpl$ViewRootHandler处理消息。本质上与第一种相同