---
layout: post
title: Framework层的服务 --- AMS管理进程
description: AMS如何管理进程
author: 电解质
date: 2018-03-16
tag:
- Android Senior Engineer
---
* TOC
{:toc}
## *1.Summary*{:.header2-font}
&emsp;&emsp;对于kernel来说，进程线程是不分家的，多线程或者多进程都会共享资源，但是由于需要确保每个应用在user space中都相对独立、相对安全，彼此不能轻易地操作彼此的数据，就急需做分离。所以进程和线程在user space其实是不同的。进程拥有独立的内存。多个进程中某个进程发生crash并不会影响其他的进程运行，借由进程的这个特性，对于需要放于后天的任务来说，进程是个非常好的选择。
&emsp;&emsp;为了更好的了解user space层面的进程，所以就写了这篇文章。
## *2.About*{:.header2-font}
&emsp;&emsp;我们都知道Android操作系统是基于Linux操作系统的。所以很多东西会沿用了Linux，但又在其基础之上做了定制。想要了解Android中的进程，需要简单了解一下Linux中的进程。

### *Process state*{:.header3-font}
#### linux process state
```
-   R  running or runnable (on run queue)
-   D  uninterruptible sleep (usually IO)
-   S  interruptible sleep (waiting for an event to complete)
-   Z  defunct/zombie, terminated but not reaped by its parent
-   T  stopped, either by a job control signal or because it is being traced
```
#### android process state
```java
    // Map from process states to the states we track.
    private static final int[] PROCESS_STATE_TO_STATE = new int[] {
        STATE_PERSISTENT,               // ActivityManager.PROCESS_STATE_PERSISTENT
        STATE_PERSISTENT,               // ActivityManager.PROCESS_STATE_PERSISTENT_UI
        STATE_TOP,                      // ActivityManager.PROCESS_STATE_TOP
        STATE_IMPORTANT_FOREGROUND,     // ActivityManager.PROCESS_STATE_FOREGROUND_SERVICE
        STATE_IMPORTANT_FOREGROUND,     // ActivityManager.PROCESS_STATE_BOUND_FOREGROUND_SERVICE
        STATE_IMPORTANT_FOREGROUND,     // ActivityManager.PROCESS_STATE_IMPORTANT_FOREGROUND
        STATE_IMPORTANT_BACKGROUND,     // ActivityManager.PROCESS_STATE_IMPORTANT_BACKGROUND
        STATE_IMPORTANT_BACKGROUND,     // ActivityManager.PROCESS_STATE_TRANSIENT_BACKGROUND
        STATE_BACKUP,                   // ActivityManager.PROCESS_STATE_BACKUP
        STATE_SERVICE,                  // ActivityManager.PROCESS_STATE_SERVICE
        STATE_RECEIVER,                 // ActivityManager.PROCESS_STATE_RECEIVER
        STATE_TOP,                      // ActivityManager.PROCESS_STATE_TOP_SLEEPING
        STATE_HEAVY_WEIGHT,             // ActivityManager.PROCESS_STATE_HEAVY_WEIGHT
        STATE_HOME,                     // ActivityManager.PROCESS_STATE_HOME
        STATE_LAST_ACTIVITY,            // ActivityManager.PROCESS_STATE_LAST_ACTIVITY
        STATE_CACHED_ACTIVITY,          // ActivityManager.PROCESS_STATE_CACHED_ACTIVITY
        STATE_CACHED_ACTIVITY_CLIENT,   // ActivityManager.PROCESS_STATE_CACHED_ACTIVITY_CLIENT
        STATE_CACHED_ACTIVITY,          // ActivityManager.PROCESS_STATE_CACHED_RECENT
        STATE_CACHED_EMPTY,             // ActivityManager.PROCESS_STATE_CACHED_EMPTY
    }
```
&emsp;&emsp;相对于linux的process state，android process state更加细化。
### *Process types*{:.header3-font}
#### linux process types

```
- 交互进程:由shell启动的进程,通过终端控制台(tty)控制。终端控制台关闭，进程也就被关闭了。
- 批处理进程
- daemon process:脱离于tty运行的进程。
```

#### android process types

>It is important that application developers understand how different application components (in particular Activity, Service, and BroadcastReceiver) impact the lifetime of the application's process. Not using these components correctly can result in the system killing the application's process while it is doing important work

1. foreground process
- running Activity at the top of the screen that the use is interacting with（its `onResume()` method has been called）
- running BroadcastReceiver(its `onReceive()` method is executing)
- Service is currently executing code in one of its callback(`onCreate(),onStart(),onDestroy()`)
2. visible process
- running Activity is visible to the user on-screen but not in the foreground(its `onPause()` method has been called)
- Service is running as a foreground service,through `startForeground()` method
- It is `hosting a service that the system is using` for a particular feature that the user is aware, such as a live wallpaper, input method service, etc.

3. service process
it is one holding a Service that has been started with the `startService()` method。
Services that have been running for a long time (such as 30 minutes or more) may be demoted in importance to allow their process to drop to the cached LRU list described next.

4. cached process
These processes often hold one or more Activity instances that are not currently visible to the user (the `onStop()` method has been called and returned)

### *Process priority*{:.header3-font}
#### linux priority
通过设置进程的nice值，取值范围为-20～+19，来改变其priority

#### android priority
```java
    /**
     * Standard priority of application threads.
     * Use with {@link #setThreadPriority(int)} and
     * {@link #setThreadPriority(int, int)}, <b>not</b> with the normal
     * {@link java.lang.Thread} class.
     */
    public static final int THREAD_PRIORITY_DEFAULT = 0;

    /*
     * ***************************************
     * ** Keep in sync with utils/threads.h **
     * ***************************************
     */
    
    /**
     * Lowest available thread priority.  Only for those who really, really
     * don't want to run if anything else is happening.
     * Use with {@link #setThreadPriority(int)} and
     * {@link #setThreadPriority(int, int)}, <b>not</b> with the normal
     * {@link java.lang.Thread} class.
     */
    public static final int THREAD_PRIORITY_LOWEST = 19;
    
    /**
     * Standard priority background threads.  This gives your thread a slightly
     * lower than normal priority, so that it will have less chance of impacting
     * the responsiveness of the user interface.
     * Use with {@link #setThreadPriority(int)} and
     * {@link #setThreadPriority(int, int)}, <b>not</b> with the normal
     * {@link java.lang.Thread} class.
     */
    public static final int THREAD_PRIORITY_BACKGROUND = 10;
    
    /**
     * Standard priority of threads that are currently running a user interface
     * that the user is interacting with.  Applications can not normally
     * change to this priority; the system will automatically adjust your
     * application threads as the user moves through the UI.
     * Use with {@link #setThreadPriority(int)} and
     * {@link #setThreadPriority(int, int)}, <b>not</b> with the normal
     * {@link java.lang.Thread} class.
     */
    public static final int THREAD_PRIORITY_FOREGROUND = -2;
    
    /**
     * Standard priority of system display threads, involved in updating
     * the user interface.  Applications can not
     * normally change to this priority.
     * Use with {@link #setThreadPriority(int)} and
     * {@link #setThreadPriority(int, int)}, <b>not</b> with the normal
     * {@link java.lang.Thread} class.
     */
    public static final int THREAD_PRIORITY_DISPLAY = -4;
    
    /**
     * Standard priority of the most important display threads, for compositing
     * the screen and retrieving input events.  Applications can not normally
     * change to this priority.
     * Use with {@link #setThreadPriority(int)} and
     * {@link #setThreadPriority(int, int)}, <b>not</b> with the normal
     * {@link java.lang.Thread} class.
     */
    public static final int THREAD_PRIORITY_URGENT_DISPLAY = -8;

    /**
     * Standard priority of video threads.  Applications can not normally
     * change to this priority.
     * Use with {@link #setThreadPriority(int)} and
     * {@link #setThreadPriority(int, int)}, <b>not</b> with the normal
     * {@link java.lang.Thread} class.
     */
    public static final int THREAD_PRIORITY_VIDEO = -10;

    /**
     * Standard priority of audio threads.  Applications can not normally
     * change to this priority.
     * Use with {@link #setThreadPriority(int)} and
     * {@link #setThreadPriority(int, int)}, <b>not</b> with the normal
     * {@link java.lang.Thread} class.
     */
    public static final int THREAD_PRIORITY_AUDIO = -16;

    /**
     * Standard priority of the most important audio threads.
     * Applications can not normally change to this priority.
     * Use with {@link #setThreadPriority(int)} and
     * {@link #setThreadPriority(int, int)}, <b>not</b> with the normal
     * {@link java.lang.Thread} class.
     */
    public static final int THREAD_PRIORITY_URGENT_AUDIO = -19;

    /**
     * Minimum increment to make a priority more favorable.
     */
    public static final int THREAD_PRIORITY_MORE_FAVORABLE = -1;

    /**
     * Minimum increment to make a priority less favorable.
     */
    public static final int THREAD_PRIORITY_LESS_FAVORABLE = +1;
```
android 的priority值，并没有做什么变动，还是和linux的保持一致。

### *Process policy*{:.header3-font}
#### linux policy
```
- SCHED_FIFO:First in-first out scheduling
- SCHED_RR:Round-robin scheduling
- SCHED_DEADLINE:Sporadic task model deadline scheduling
- SCHED_OTHER:Default Linux time-sharing scheduling
- SCHED_BATCH:Scheduling batch processes
- SCHED_IDLE:Scheduling very low priority jobs
```

#### android policy
```java
    /**
     * Default scheduling policy
     * @hide
     */
    public static final int SCHED_OTHER = 0;

    /**
     * First-In First-Out scheduling policy
     * @hide
     */
    public static final int SCHED_FIFO = 1;

    /**
     * Round-Robin scheduling policy
     * @hide
     */
    public static final int SCHED_RR = 2;

    /**
     * Batch scheduling policy
     * @hide
     */
    public static final int SCHED_BATCH = 3;

    /**
     * Idle scheduling policy
     * @hide
     */
    public static final int SCHED_IDLE = 5;

    /**
     * Reset scheduler choice on fork.
     * @hide
     */
     public static final int SCHED_RESET_ON_FORK = 0x40000000;
```
### *Process group*{:.header3-font}
#### linux group 

#### android group
```java
    /**
     * Default thread group -
     * has meaning with setProcessGroup() only, cannot be used with setThreadGroup().
     * When used with setProcessGroup(), the group of each thread in the process
     * is conditionally changed based on that thread's current priority, as follows:
     * threads with priority numerically less than THREAD_PRIORITY_BACKGROUND
     * are moved to foreground thread group.  All other threads are left unchanged.
     * @hide
     */
    public static final int THREAD_GROUP_DEFAULT = -1;

    /**
     * Background thread group - All threads in
     * this group are scheduled with a reduced share of the CPU.
     * Value is same as constant SP_BACKGROUND of enum SchedPolicy.
     * FIXME rename to THREAD_GROUP_BACKGROUND.
     * @hide
     */
    public static final int THREAD_GROUP_BG_NONINTERACTIVE = 0;

    /**
     * Foreground thread group - All threads in
     * this group are scheduled with a normal share of the CPU.
     * Value is same as constant SP_FOREGROUND of enum SchedPolicy.
     * Not used at this level.
     * @hide
     **/
    private static final int THREAD_GROUP_FOREGROUND = 1;

    /**
     * System thread group.
     * @hide
     **/
    public static final int THREAD_GROUP_SYSTEM = 2;

    /**
     * Application audio thread group.
     * @hide
     **/
    public static final int THREAD_GROUP_AUDIO_APP = 3;

    /**
     * System audio thread group.
     * @hide
     **/
    public static final int THREAD_GROUP_AUDIO_SYS = 4;

    /**
     * Thread group for top foreground app.
     * @hide
     **/
    public static final int THREAD_GROUP_TOP_APP = 5;

    /**
     * Thread group for RT app.
     * @hide
     **/
    public static final int THREAD_GROUP_RT_APP = 6;

    /**
     * Thread group for bound foreground services that should
     * have additional CPU restrictions during screen off
     * @hide
     **/
    public static final int THREAD_GROUP_RESTRICTED = 7;
```

### *Process siganl*{:.header3-font}
#### linux siganl
```
       SIGHUP        1       Term    Hangup detected on controlling terminal
                                     or death of controlling process
       SIGINT        2       Term    Interrupt from keyboard
       SIGQUIT       3       Core    Quit from keyboard
       SIGILL        4       Core    Illegal Instruction
       SIGABRT       6       Core    Abort signal from abort(3)
       SIGFPE        8       Core    Floating-point exception
       SIGKILL       9       Term    Kill signal
       SIGSEGV      11       Core    Invalid memory reference
       SIGPIPE      13       Term    Broken pipe: write to pipe with no
                                     readers; see pipe(7)
       SIGALRM      14       Term    Timer signal from alarm(2)
       SIGTERM      15       Term    Termination signal
       SIGUSR1   30,10,16    Term    User-defined signal 1
       SIGUSR2   31,12,17    Term    User-defined signal 2
       SIGCHLD   20,17,18    Ign     Child stopped or terminated
       SIGCONT   19,18,25    Cont    Continue if stopped
       SIGSTOP   17,19,23    Stop    Stop process
       SIGTSTP   18,20,24    Stop    Stop typed at terminal
       SIGTTIN   21,21,26    Stop    Terminal input for background process
       SIGTTOU   22,22,27    Stop    Terminal output for background process
       ...
```
#### android siganl
```java
    public static final int SIGNAL_QUIT = 3;
    public static final int SIGNAL_KILL = 9;
    public static final int SIGNAL_USR1 = 10;
```

&emsp;&emsp;总的来说主要有变化的是process state和process types。
## *3.Introduction*{:.header2-font}

### *updateLruProcessLocked*{:.header3-font}

#### 插入当前的进程
----
> AMS#updateLruProcessLocked
{:.filename}
```java
final void updateLruProcessLocked(ProcessRecord app, boolean activityChange,
            ProcessRecord client) {
        final boolean hasActivity = app.activities.size() > 0 || app.hasClientActivities
                || app.treatLikeActivity || app.recentTasks.size() > 0;
        final boolean hasService = false; // not impl yet. app.services.size() > 0;
        if (!activityChange && hasActivity) {
            // The process has activities, so we are only allowing activity-based adjustments
            // to move it.  It should be kept in the front of the list with other
            // processes that have activities, and we don't want those to change their
            // order except due to activity operations.
            return;
        }

        mLruSeq++;
        final long now = SystemClock.uptimeMillis();
        app.lastActivityTime = now;
        ...
        int lrui = mLruProcesses.lastIndexOf(app);

        ...

        if (lrui >= 0) {
            if (lrui < mLruProcessActivityStart) {
                mLruProcessActivityStart--;
            }
            if (lrui < mLruProcessServiceStart) {
                mLruProcessServiceStart--;
            }
            mLruProcesses.remove(lrui);
        }

    
        int nextIndex;
        if (hasActivity) {
            final int N = mLruProcesses.size();
            if ((app.activities.size() == 0 || app.recentTasks.size() > 0)
                    && mLruProcessActivityStart < (N - 1)) {
                // Process doesn't have activities, but has clients with
                // activities...  move it up, but one below the top (the top
                // should always have a real activity).
                if (DEBUG_LRU) Slog.d(TAG_LRU,
                        "Adding to second-top of LRU activity list: " + app);
                mLruProcesses.add(N - 1, app);
                // To keep it from spamming the LRU list (by making a bunch of clients),
                // we will push down any other entries owned by the app.
                final int uid = app.info.uid;
                for (int i = N - 2; i > mLruProcessActivityStart; i--) {
                    ProcessRecord subProc = mLruProcesses.get(i);
                    if (subProc.info.uid == uid) {
                        // We want to push this one down the list.  If the process after
                        // it is for the same uid, however, don't do so, because we don't
                        // want them internally to be re-ordered.
                        if (mLruProcesses.get(i - 1).info.uid != uid) {
                            if (DEBUG_LRU) Slog.d(TAG_LRU,
                                    "Pushing uid " + uid + " swapping at " + i + ": "
                                    + mLruProcesses.get(i) + " : " + mLruProcesses.get(i - 1));
                            ProcessRecord tmp = mLruProcesses.get(i);
                            mLruProcesses.set(i, mLruProcesses.get(i - 1));
                            mLruProcesses.set(i - 1, tmp);
                            i--;
                        }
                    } else {
                        // A gap, we can stop here.
                        break;
                    }
                }
            } else {
                // Process has activities, put it at the very tipsy-top.
                if (DEBUG_LRU) Slog.d(TAG_LRU, "Adding to top of LRU activity list: " + app);
                mLruProcesses.add(app);
            }
            nextIndex = mLruProcessServiceStart;
        } else if (hasService) {
            // Process has services, put it at the top of the service list.
            if (DEBUG_LRU) Slog.d(TAG_LRU, "Adding to top of LRU service list: " + app);
            mLruProcesses.add(mLruProcessActivityStart, app);
            nextIndex = mLruProcessServiceStart;
            mLruProcessActivityStart++;
        } else  {
            // Process not otherwise of interest, it goes to the top of the non-service area.
            int index = mLruProcessServiceStart;
            if (client != null) {
                // If there is a client, don't allow the process to be moved up higher
                // in the list than that client.
                int clientIndex = mLruProcesses.lastIndexOf(client);
                if (DEBUG_LRU && clientIndex < 0) Slog.d(TAG_LRU, "Unknown client " + client
                        + " when updating " + app);
                if (clientIndex <= lrui) {
                    // Don't allow the client index restriction to push it down farther in the
                    // list than it already is.
                    clientIndex = lrui;
                }
                if (clientIndex >= 0 && index > clientIndex) {
                    index = clientIndex;
                }
            }
            if (DEBUG_LRU) Slog.d(TAG_LRU, "Adding at " + index + " of LRU list: " + app);
            mLruProcesses.add(index, app);
            nextIndex = index-1;
            mLruProcessActivityStart++;
            mLruProcessServiceStart++;
        }
```
有Activity的进程：
1. 该进程存在Activity
2. 该进程为Service进程，其绑定的client进程（bindService）存在Activity
3. 该进程为Service进程，flag=BIND_TREAT_LIKE_ACTIVITY时，Service将被当成Activity。

&emsp;&emsp;第一种会将进程直接添加到mLruProcesses尾部，后两种会将进程添加到mLruProcesses倒数第二位，从这里可以看出存在Activity的进程比和Activity相互关联的Service进程优先级更高。

有Service的进程：

&emsp;&emsp;由于hasService总是为false，这部分代码还没有完善。不过我们可以大致知道，对于进程的管理越来越细化了，之前是根据Activity来划分，接下去还会出现根据Service来划分。这里有个地方需要提及一下，Android团队在源码中使用了mLruProcessServiceStart/mLruProcessActivityStart这两个字段来分割Service进程和Activity进程。

其他的进程：
- 对于当前进程来说，存在其client进程。

&emsp;&emsp;取client进程和当前进程在mLruProcesses的最大index，并且和mLruProcessServiceStart比较，两者之间取最小值，最后将当前进程插入到最后这个最新的位置中。从这里可以看出，client进程的index如果大于当前进程，将帮助当前进程往前添加。如果小于，还是呆在原地不动。
- 对于当前进程来说，不存在client进程。

&emsp;&emsp;直接添加到mLruProcessServiceStart的位置。

#### 重排序和当前线程相互关联的进程
----
>AMS#updateLruProcessLocked
{:.filename}
```java
        // If the app is currently using a content provider or service,
        // bump those processes as well.
        for (int j=app.connections.size()-1; j>=0; j--) {
            ConnectionRecord cr = app.connections.valueAt(j);
            if (cr.binding != null && !cr.serviceDead && cr.binding.service != null
                    && cr.binding.service.app != null
                    && cr.binding.service.app.lruSeq != mLruSeq
                    && !cr.binding.service.app.persistent) {
                nextIndex = updateLruProcessInternalLocked(cr.binding.service.app, now, nextIndex,
                        "service connection", cr, app);
            }
        }
        for (int j=app.conProviders.size()-1; j>=0; j--) {
            ContentProviderRecord cpr = app.conProviders.get(j).provider;
            if (cpr.proc != null && cpr.proc.lruSeq != mLruSeq && !cpr.proc.persistent) {
                nextIndex = updateLruProcessInternalLocked(cpr.proc, now, nextIndex,
                        "provider reference", cpr, app);
            }
        }
    }
```
&emsp;&emsp;如果当前进程存在service connection，则帮助绑定的service进程提高在mLruProcessses中的index。
&emsp;&emsp;如果当前进程存在provider reference，则帮助ContentProvider进程提高在mLruProcesses中的index。

### *updateOomAdjLocked*{:.header3-font}

adj级别 |取值|介绍
---|---|---|
INVALID_ADJ|-10000|
NATIVE_ADJ |-1000 | native进程，不受jvm控制
SYSTEM_ADJ |-900 | system_server进程
PERSISTENT_PROC_ADJ|-800|persistent进程,在AndroidManifest申明“android：persistent=true”，即带有FLAG_SYSTEM标记，比如telephony进程
PERSISTENT_SERVICE_ADJ|-700|绑定系统进程或者persistent进程的一种进程
FOREGROUND_APP_ADJ |0|foreground进程
VISIBLE_APP_LAYER_MAX |(PERCEPTIBLE_APP_ADJ - VISIBLE_APP_ADJ - 1)|
VISIBLE_APP_ADJ |100|visible进程
PERCEPTIBLE_APP_ADJ|200|用户可察觉的进程，但却不可见，比如音乐播放后台
BACKUP_APP_ADJ |300|备份进程。执行bindBackupAgent过程的进程
HEAVY_WEIGHT_APP_ADJ|400|附带重量级应用的进程，运行于后台。在init.rc脚本中启动的，比如zygote.当应用的privateFlags=PRIVATE_FLAG_CANT_SAVE_STATE
SERVICE_ADJ |500|service进程
HOME_APP_ADJ |600|home应用的进程
PREVIOUS_APP_ADJ |700|上一个应用的进程
SERVICE_B_ADJ |800|SERVICE_ADJ的B list(不同于SERVICE_ADJ的A list，是用来标识old和decrepit的services)
CACHED_APP_MIN_ADJ~CACHED_APP_MAX_ADJ |900~906|cache进程
UNKNOWN_ADJ |1001|
{:.inner-borders}


#### ASS#rankTaskLayersIfNeeded
---
>AMS#updateOomAdjLocked
{:.filename}
```java
        ...
        // Reset state in all uid records.
        for (int i=mActiveUids.size()-1; i>=0; i--) {
            final UidRecord uidRec = mActiveUids.valueAt(i);
            if (false && DEBUG_UID_OBSERVERS) Slog.i(TAG_UID_OBSERVERS,
                    "Starting update of " + uidRec);
            uidRec.reset();
        }

        mStackSupervisor.rankTaskLayersIfNeeded();

        mAdjSeq++;
        mNewNumServiceProcs = 0;
        mNewNumAServiceProcs = 0;

        final int emptyProcessLimit = mConstants.CUR_MAX_EMPTY_PROCESSES;
        final int cachedProcessLimit = mConstants.CUR_MAX_CACHED_PROCESSES - emptyProcessLimit;

        // Let's determine how many processes we have running vs.
        // how many slots we have for background processes; we may want
        // to put multiple processes in a slot of there are enough of
        // them.
        int numSlots = (ProcessList.CACHED_APP_MAX_ADJ
                - ProcessList.CACHED_APP_MIN_ADJ + 1) / 2;
        int numEmptyProcs = N - mNumNonCachedProcs - mNumCachedHiddenProcs;
        if (numEmptyProcs > cachedProcessLimit) {
            // If there are more empty processes than our limit on cached
            // processes, then use the cached process limit for the factor.
            // This ensures that the really old empty processes get pushed
            // down to the bottom, so if we are running low on memory we will
            // have a better chance at keeping around more cached processes
            // instead of a gazillion empty processes.
            numEmptyProcs = cachedProcessLimit;
        }
        int emptyFactor = numEmptyProcs/numSlots;
        if (emptyFactor < 1) emptyFactor = 1;
        int cachedFactor = (mNumCachedHiddenProcs > 0 ? mNumCachedHiddenProcs : 1)/numSlots;
        if (cachedFactor < 1) cachedFactor = 1;
        int stepCached = 0;
        int stepEmpty = 0;
        int numCached = 0;
        int numEmpty = 0;
        int numTrimming = 0;

        mNumNonCachedProcs = 0;
        mNumCachedHiddenProcs = 0;

        // First update the OOM adjustment for each of the
        // application processes based on their current state.
        int curCachedAdj = ProcessList.CACHED_APP_MIN_ADJ;
        int nextCachedAdj = curCachedAdj+1;
        int curEmptyAdj = ProcessList.CACHED_APP_MIN_ADJ;
        int nextEmptyAdj = curEmptyAdj+2;

        boolean retryCycles = false;

        // need to reset cycle state before calling computeOomAdjLocked because of service connections
        for (int i=N-1; i>=0; i--) {
            ProcessRecord app = mLruProcesses.get(i);
            app.containsCycle = false;
        }
```
从ActivityDisplay的尾部开始遍历得到ActivityStack，每一个ActivityStack都包含着一组TaskRecord在mTaskHistory。紧急着从mTaskHistory尾端开始遍历得到TaskRecord。最尾端的TaskRecord为最近使用的。ActivityStack会从尾端到头部依次递增给TaskRecord的mLayerRank复制。显然越往后数值越大。

#### computeOomAdjLocked
-----
```java
        for (int i=N-1; i>=0; i--) {
            ProcessRecord app = mLruProcesses.get(i);
            if (!app.killedByAm && app.thread != null) {
                app.procStateChanged = false;
                computeOomAdjLocked(app, ProcessList.UNKNOWN_ADJ, TOP_APP, true, now);

                // if any app encountered a cycle, we need to perform an additional loop later
                retryCycles |= app.containsCycle;

                // If we haven't yet assigned the final cached adj
                // to the process, do that now.
                if (app.curAdj >= ProcessList.UNKNOWN_ADJ) {
                    switch (app.curProcState) {
                        case ActivityManager.PROCESS_STATE_CACHED_ACTIVITY:
                        case ActivityManager.PROCESS_STATE_CACHED_ACTIVITY_CLIENT:
                        case ActivityManager.PROCESS_STATE_CACHED_RECENT:
                            // This process is a cached process holding activities...
                            // assign it the next cached value for that type, and then
                            // step that cached level.
                            app.curRawAdj = curCachedAdj;
                            app.curAdj = app.modifyRawOomAdj(curCachedAdj);
                            if (DEBUG_LRU && false) Slog.d(TAG_LRU, "Assigning activity LRU #" + i
                                    + " adj: " + app.curAdj + " (curCachedAdj=" + curCachedAdj
                                    + ")");
                            if (curCachedAdj != nextCachedAdj) {
                                stepCached++;
                                if (stepCached >= cachedFactor) {
                                    stepCached = 0;
                                    curCachedAdj = nextCachedAdj;
                                    nextCachedAdj += 2;
                                    if (nextCachedAdj > ProcessList.CACHED_APP_MAX_ADJ) {
                                        nextCachedAdj = ProcessList.CACHED_APP_MAX_ADJ;
                                    }
                                }
                            }
                            break;
                        default:
                            // For everything else, assign next empty cached process
                            // level and bump that up.  Note that this means that
                            // long-running services that have dropped down to the
                            // cached level will be treated as empty (since their process
                            // state is still as a service), which is what we want.
                            app.curRawAdj = curEmptyAdj;
                            app.curAdj = app.modifyRawOomAdj(curEmptyAdj);
                            if (DEBUG_LRU && false) Slog.d(TAG_LRU, "Assigning empty LRU #" + i
                                    + " adj: " + app.curAdj + " (curEmptyAdj=" + curEmptyAdj
                                    + ")");
                            if (curEmptyAdj != nextEmptyAdj) {
                                stepEmpty++;
                                if (stepEmpty >= emptyFactor) {
                                    stepEmpty = 0;
                                    curEmptyAdj = nextEmptyAdj;
                                    nextEmptyAdj += 2;
                                    if (nextEmptyAdj > ProcessList.CACHED_APP_MAX_ADJ) {
                                        nextEmptyAdj = ProcessList.CACHED_APP_MAX_ADJ;
                                    }
                                }
                            }
                            break;
                    }
                }


            }
        }

        // Cycle strategy:
        // - Retry computing any process that has encountered a cycle.
        // - Continue retrying until no process was promoted.
        // - Iterate from least important to most important.
        int cycleCount = 0;
        while (retryCycles) {
            cycleCount++;
            retryCycles = false;

            for (int i=0; i<N; i++) {
                ProcessRecord app = mLruProcesses.get(i);
                if (!app.killedByAm && app.thread != null && app.containsCycle == true) {
                    app.adjSeq--;
                    app.completedAdjSeq--;
                }
            }

            for (int i=0; i<N; i++) {
                ProcessRecord app = mLruProcesses.get(i);
                if (!app.killedByAm && app.thread != null && app.containsCycle == true) {
                    if (computeOomAdjLocked(app, ProcessList.UNKNOWN_ADJ, TOP_APP, true, now)) {
                        retryCycles = true;
                    }
                }
            }
        }
```

从mLruProcesses数组的尾部开始遍历得到ProcessRecord，通过computeOomAdjLocked方法，开始计算每个ProcessRecord的adj值

#### applyOomAdjLocked
-----
```java
        for (int i=N-1; i>=0; i--) {
            ProcessRecord app = mLruProcesses.get(i);
            if (!app.killedByAm && app.thread != null) {
                applyOomAdjLocked(app, true, now, nowElapsed);

                // Count the number of process types.
                switch (app.curProcState) {
                    case ActivityManager.PROCESS_STATE_CACHED_ACTIVITY:
                    case ActivityManager.PROCESS_STATE_CACHED_ACTIVITY_CLIENT:
                        mNumCachedHiddenProcs++;
                        numCached++;
                        if (numCached > cachedProcessLimit) {
                            app.kill("cached #" + numCached, true);
                        }
                        break;
                    case ActivityManager.PROCESS_STATE_CACHED_EMPTY:
                        if (numEmpty > mConstants.CUR_TRIM_EMPTY_PROCESSES
                                && app.lastActivityTime < oldTime) {
                            app.kill("empty for "
                                    + ((oldTime + ProcessList.MAX_EMPTY_TIME - app.lastActivityTime)
                                    / 1000) + "s", true);
                        } else {
                            numEmpty++;
                            if (numEmpty > emptyProcessLimit) {
                                app.kill("empty #" + numEmpty, true);
                            }
                        }
                        break;
                    default:
                        mNumNonCachedProcs++;
                        break;
                }

                if (app.isolated && app.services.size() <= 0 && app.isolatedEntryPoint == null) {
                    // If this is an isolated process, there are no services
                    // running in it, and it's not a special process with a
                    // custom entry point, then the process is no longer
                    // needed.  We agressively kill these because we can by
                    // definition not re-use the same process again, and it is
                    // good to avoid having whatever code was running in them
                    // left sitting around after no longer needed.
                    app.kill("isolated not needed", true);
                } else {
                    // Keeping this process, update its uid.
                    final UidRecord uidRec = app.uidRecord;
                    if (uidRec != null) {
                        uidRec.ephemeral = app.info.isInstantApp();
                        if (uidRec.curProcState > app.curProcState) {
                            uidRec.curProcState = app.curProcState;
                        }
                        if (app.foregroundServices) {
                            uidRec.foregroundServices = true;
                        }
                    }
                }

                if (app.curProcState >= ActivityManager.PROCESS_STATE_HOME
                        && !app.killedByAm) {
                    numTrimming++;
                }
            }
        }
```

应用oom adj的值，当需要杀掉目标进程则返回false

#### IApplicationThread#scheduleTrimMemory
-----
```java
        final int numCachedAndEmpty = numCached + numEmpty;
        int memFactor;
        if (numCached <= mConstants.CUR_TRIM_CACHED_PROCESSES
                && numEmpty <= mConstants.CUR_TRIM_EMPTY_PROCESSES) {
            if (numCachedAndEmpty <= ProcessList.TRIM_CRITICAL_THRESHOLD) {
                memFactor = ProcessStats.ADJ_MEM_FACTOR_CRITICAL;
            } else if (numCachedAndEmpty <= ProcessList.TRIM_LOW_THRESHOLD) {
                memFactor = ProcessStats.ADJ_MEM_FACTOR_LOW;
            } else {
                memFactor = ProcessStats.ADJ_MEM_FACTOR_MODERATE;
            }
        } else {
            memFactor = ProcessStats.ADJ_MEM_FACTOR_NORMAL;
        }
        // We always allow the memory level to go up (better).  We only allow it to go
        // down if we are in a state where that is allowed, *and* the total number of processes
        // has gone down since last time.
        if (DEBUG_OOM_ADJ) Slog.d(TAG_OOM_ADJ, "oom: memFactor=" + memFactor
                + " last=" + mLastMemoryLevel + " allowLow=" + mAllowLowerMemLevel
                + " numProcs=" + mLruProcesses.size() + " last=" + mLastNumProcesses);
        if (memFactor > mLastMemoryLevel) {
            if (!mAllowLowerMemLevel || mLruProcesses.size() >= mLastNumProcesses) {
                memFactor = mLastMemoryLevel;
                if (DEBUG_OOM_ADJ) Slog.d(TAG_OOM_ADJ, "Keeping last mem factor!");
            }
        }
        if (memFactor != mLastMemoryLevel) {
            EventLogTags.writeAmMemFactor(memFactor, mLastMemoryLevel);
        }
        mLastMemoryLevel = memFactor;
        mLastNumProcesses = mLruProcesses.size();
        boolean allChanged = mProcessStats.setMemFactorLocked(memFactor, !isSleepingLocked(), now);
        final int trackerMemFactor = mProcessStats.getMemFactorLocked();
        if (memFactor != ProcessStats.ADJ_MEM_FACTOR_NORMAL) {
            if (mLowRamStartTime == 0) {
                mLowRamStartTime = now;
            }
            int step = 0;
            int fgTrimLevel;
            switch (memFactor) {
                case ProcessStats.ADJ_MEM_FACTOR_CRITICAL:
                    fgTrimLevel = ComponentCallbacks2.TRIM_MEMORY_RUNNING_CRITICAL;
                    break;
                case ProcessStats.ADJ_MEM_FACTOR_LOW:
                    fgTrimLevel = ComponentCallbacks2.TRIM_MEMORY_RUNNING_LOW;
                    break;
                default:
                    fgTrimLevel = ComponentCallbacks2.TRIM_MEMORY_RUNNING_MODERATE;
                    break;
            }
            int factor = numTrimming/3;
            int minFactor = 2;
            if (mHomeProcess != null) minFactor++;
            if (mPreviousProcess != null) minFactor++;
            if (factor < minFactor) factor = minFactor;
            int curLevel = ComponentCallbacks2.TRIM_MEMORY_COMPLETE;
            for (int i=N-1; i>=0; i--) {
                ProcessRecord app = mLruProcesses.get(i);
                if (allChanged || app.procStateChanged) {
                    setProcessTrackerStateLocked(app, trackerMemFactor, now);
                    app.procStateChanged = false;
                }
                if (app.curProcState >= ActivityManager.PROCESS_STATE_HOME
                        && !app.killedByAm) {
                    if (app.trimMemoryLevel < curLevel && app.thread != null) {
                        try {
                            if (DEBUG_SWITCH || DEBUG_OOM_ADJ) Slog.v(TAG_OOM_ADJ,
                                    "Trimming memory of " + app.processName + " to " + curLevel);
                            app.thread.scheduleTrimMemory(curLevel);
                        } catch (RemoteException e) {
                        }
                        if (false) {
                            // For now we won't do this; our memory trimming seems
                            // to be good enough at this point that destroying
                            // activities causes more harm than good.
                            if (curLevel >= ComponentCallbacks2.TRIM_MEMORY_COMPLETE
                                    && app != mHomeProcess && app != mPreviousProcess) {
                                // Need to do this on its own message because the stack may not
                                // be in a consistent state at this point.
                                // For these apps we will also finish their activities
                                // to help them free memory.
                                mStackSupervisor.scheduleDestroyAllActivities(app, "trim");
                            }
                        }
                    }
                    app.trimMemoryLevel = curLevel;
                    step++;
                    if (step >= factor) {
                        step = 0;
                        switch (curLevel) {
                            case ComponentCallbacks2.TRIM_MEMORY_COMPLETE:
                                curLevel = ComponentCallbacks2.TRIM_MEMORY_MODERATE;
                                break;
                            case ComponentCallbacks2.TRIM_MEMORY_MODERATE:
                                curLevel = ComponentCallbacks2.TRIM_MEMORY_BACKGROUND;
                                break;
                        }
                    }
                } else if (app.curProcState == ActivityManager.PROCESS_STATE_HEAVY_WEIGHT
                        && !app.killedByAm) {
                    if (app.trimMemoryLevel < ComponentCallbacks2.TRIM_MEMORY_BACKGROUND
                            && app.thread != null) {
                        try {
                            if (DEBUG_SWITCH || DEBUG_OOM_ADJ) Slog.v(TAG_OOM_ADJ,
                                    "Trimming memory of heavy-weight " + app.processName
                                    + " to " + ComponentCallbacks2.TRIM_MEMORY_BACKGROUND);
                            app.thread.scheduleTrimMemory(
                                    ComponentCallbacks2.TRIM_MEMORY_BACKGROUND);
                        } catch (RemoteException e) {
                        }
                    }
                    app.trimMemoryLevel = ComponentCallbacks2.TRIM_MEMORY_BACKGROUND;
                } else {
                    if ((app.curProcState >= ActivityManager.PROCESS_STATE_IMPORTANT_BACKGROUND
                            || app.systemNoUi) && app.pendingUiClean) {
                        // If this application is now in the background and it
                        // had done UI, then give it the special trim level to
                        // have it free UI resources.
                        final int level = ComponentCallbacks2.TRIM_MEMORY_UI_HIDDEN;
                        if (app.trimMemoryLevel < level && app.thread != null) {
                            try {
                                if (DEBUG_SWITCH || DEBUG_OOM_ADJ) Slog.v(TAG_OOM_ADJ,
                                        "Trimming memory of bg-ui " + app.processName
                                        + " to " + level);
                                app.thread.scheduleTrimMemory(level);
                            } catch (RemoteException e) {
                            }
                        }
                        app.pendingUiClean = false;
                    }
                    if (app.trimMemoryLevel < fgTrimLevel && app.thread != null) {
                        try {
                            if (DEBUG_SWITCH || DEBUG_OOM_ADJ) Slog.v(TAG_OOM_ADJ,
                                    "Trimming memory of fg " + app.processName
                                    + " to " + fgTrimLevel);
                            app.thread.scheduleTrimMemory(fgTrimLevel);
                        } catch (RemoteException e) {
                        }
                    }
                    app.trimMemoryLevel = fgTrimLevel;
                }
            }
        } else {
            if (mLowRamStartTime != 0) {
                mLowRamTimeSinceLastIdle += now - mLowRamStartTime;
                mLowRamStartTime = 0;
            }
            for (int i=N-1; i>=0; i--) {
                ProcessRecord app = mLruProcesses.get(i);
                if (allChanged || app.procStateChanged) {
                    setProcessTrackerStateLocked(app, trackerMemFactor, now);
                    app.procStateChanged = false;
                }
                if ((app.curProcState >= ActivityManager.PROCESS_STATE_IMPORTANT_BACKGROUND
                        || app.systemNoUi) && app.pendingUiClean) {
                    if (app.trimMemoryLevel < ComponentCallbacks2.TRIM_MEMORY_UI_HIDDEN
                            && app.thread != null) {
                        try {
                            if (DEBUG_SWITCH || DEBUG_OOM_ADJ) Slog.v(TAG_OOM_ADJ,
                                    "Trimming memory of ui hidden " + app.processName
                                    + " to " + ComponentCallbacks2.TRIM_MEMORY_UI_HIDDEN);
                            app.thread.scheduleTrimMemory(
                                    ComponentCallbacks2.TRIM_MEMORY_UI_HIDDEN);
                        } catch (RemoteException e) {
                        }
                    }
                    app.pendingUiClean = false;
                }
                app.trimMemoryLevel = 0;
            }
        }
```

在回调application层的接口之前会计算其level，而level又与memory factory有关。

```java
        int memFactor;
        if (numCached <= mConstants.CUR_TRIM_CACHED_PROCESSES
                && numEmpty <= mConstants.CUR_TRIM_EMPTY_PROCESSES) {
            if (numCachedAndEmpty <= ProcessList.TRIM_CRITICAL_THRESHOLD) {
                memFactor = ProcessStats.ADJ_MEM_FACTOR_CRITICAL;
            } else if (numCachedAndEmpty <= ProcessList.TRIM_LOW_THRESHOLD) {
                memFactor = ProcessStats.ADJ_MEM_FACTOR_LOW;
            } else {
                memFactor = ProcessStats.ADJ_MEM_FACTOR_MODERATE;
            }
        } else {
            memFactor = ProcessStats.ADJ_MEM_FACTOR_NORMAL;
        }
        ...
        if (memFactor > mLastMemoryLevel) {
            if (!mAllowLowerMemLevel || mLruProcesses.size() >= mLastNumProcesses) {
                memFactor = mLastMemoryLevel;
                ...
            }
        }
       ...
```
用一张表单展示上面的代码逻辑

memory 因素| 取值|计算条件
---|---|---
ADJ_MEM_FACTOR_NORMAL	|0|	Cached>5或者Empty>8
ADJ_MEM_FACTOR_MODERATE	|1	|Cached<=5 && Empty<=8
ADJ_MEM_FACTOR_LOW	|2	|Cached+Empty<=5
ADJ_MEM_FACTOR_CRITICAL	|3|	Cached+Empty<=3

具体如何得到level值的就不继续细看了，有兴趣自行研究，这里提供些level的常量值。
```java
    /**
     * Level for {@link #onTrimMemory(int)}: the process is nearing the end
     * of the background LRU list, and if more memory isn't found soon it will
     * be killed.
     */
    static final int TRIM_MEMORY_COMPLETE = 80;
    
    /**
     * Level for {@link #onTrimMemory(int)}: the process is around the middle
     * of the background LRU list; freeing memory can help the system keep
     * other processes running later in the list for better overall performance.
     */
    static final int TRIM_MEMORY_MODERATE = 60;
    
    /**
     * Level for {@link #onTrimMemory(int)}: the process has gone on to the
     * LRU list.  This is a good opportunity to clean up resources that can
     * efficiently and quickly be re-built if the user returns to the app.
     */
    static final int TRIM_MEMORY_BACKGROUND = 40;
    
    /**
     * Level for {@link #onTrimMemory(int)}: the process had been showing
     * a user interface, and is no longer doing so.  Large allocations with
     * the UI should be released at this point to allow memory to be better
     * managed.
     */
    static final int TRIM_MEMORY_UI_HIDDEN = 20;

    /**
     * Level for {@link #onTrimMemory(int)}: the process is not an expendable
     * background process, but the device is running extremely low on memory
     * and is about to not be able to keep any background processes running.
     * Your running process should free up as many non-critical resources as it
     * can to allow that memory to be used elsewhere.  The next thing that
     * will happen after this is {@link #onLowMemory()} called to report that
     * nothing at all can be kept in the background, a situation that can start
     * to notably impact the user.
     */
    static final int TRIM_MEMORY_RUNNING_CRITICAL = 15;

    /**
     * Level for {@link #onTrimMemory(int)}: the process is not an expendable
     * background process, but the device is running low on memory.
     * Your running process should free up unneeded resources to allow that
     * memory to be used elsewhere.
     */
    static final int TRIM_MEMORY_RUNNING_LOW = 10;

    /**
     * Level for {@link #onTrimMemory(int)}: the process is not an expendable
     * background process, but the device is running moderately low on memory.
     * Your running process may want to release some unneeded resources for
     * use elsewhere.
     */
    static final int TRIM_MEMORY_RUNNING_MODERATE = 5;
```
文中还有一些具体的细节没有展开，有空再来填坑。

