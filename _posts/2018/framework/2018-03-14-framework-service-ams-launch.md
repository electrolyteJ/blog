---
layout: post
title: Framework层的服务 --- AMS启动流程
description: 来一起聊聊AMS的启动流程
author: 电解质
date: 2018-03-14
tag:
- Android Senior Engineer
---
* TOC
{:toc}
## *1.Summary*{:.header2-font}
&emsp;&emsp;
## *2.About*{:.header2-font}
&emsp;&emsp;
## *3.Introduction*{:.header2-font}

AMS启动流程中主要的方法也就是下面的三个：
- ActivityManagerService构造方法
- start方法
- systemReady方法

其实AMS启动流程中还会初始化一些其他东西，比如将WMS对象注入到AMS这，这样就可以实现UI交互。

### *ActivityManagerService构造方法*{:.header3-font}

```java
    public ActivityManagerService(Context systemContext) {

        ...

        mHandlerThread = new ServiceThread(TAG,
                THREAD_PRIORITY_FOREGROUND, false /*allowIo*/);
        mHandlerThread.start();
        mHandler = new MainHandler(mHandlerThread.getLooper());
        mUiHandler = mInjector.getUiHandler(this);

       ...

        /* static; one-time init here */
        if (sKillHandler == null) {
            sKillThread = new ServiceThread(TAG + ":kill",
                    THREAD_PRIORITY_BACKGROUND, true /* allowIo */);
            sKillThread.start();
            sKillHandler = new KillHandler(sKillThread.getLooper());
        }

        mFgBroadcastQueue = new BroadcastQueue(this, mHandler,
                "foreground", BROADCAST_FG_TIMEOUT, false);
        mBgBroadcastQueue = new BroadcastQueue(this, mHandler,
                "background", BROADCAST_BG_TIMEOUT, true);
        mBroadcastQueues[0] = mFgBroadcastQueue;
        mBroadcastQueues[1] = mBgBroadcastQueue;

        mServices = new ActiveServices(this);
        mProviderMap = new ProviderMap(this);
        mAppErrors = new AppErrors(mUiContext, this);

        // TODO: Move creation of battery stats service outside of activity manager service.
        File dataDir = Environment.getDataDirectory();
        File systemDir = new File(dataDir, "system");
        systemDir.mkdirs();
        mBatteryStatsService = new BatteryStatsService(systemDir, mHandler);
        mBatteryStatsService.getActiveStatistics().readLocked();
        mBatteryStatsService.scheduleWriteToDisk();
        mOnBattery = DEBUG_POWER ? true
                : mBatteryStatsService.getActiveStatistics().getIsOnBattery();
        mBatteryStatsService.getActiveStatistics().setCallback(this);

        mProcessStats = new ProcessStatsService(this, new File(systemDir, "procstats"));

        mAppOpsService = mInjector.getAppOpsService(new File(systemDir, "appops.xml"), mHandler);
        mAppOpsService.startWatchingMode(AppOpsManager.OP_RUN_IN_BACKGROUND, null,
                new IAppOpsCallback.Stub() {
                    @Override public void opChanged(int op, int uid, String packageName) {
                        if (op == AppOpsManager.OP_RUN_IN_BACKGROUND && packageName != null) {
                            if (mAppOpsService.checkOperation(op, uid, packageName)
                                    != AppOpsManager.MODE_ALLOWED) {
                                runInBackgroundDisabled(uid);
                            }
                        }
                    }
                });

        mGrantFile = new AtomicFile(new File(systemDir, "urigrants.xml"));

        mUserController = new UserController(this);

        mVrController = new VrController(this);

        ...

        mStackSupervisor = createStackSupervisor();
        mStackSupervisor.onConfigurationChanged(mTempConfig);
        mKeyguardController = mStackSupervisor.mKeyguardController;
        mCompatModePackages = new CompatModePackages(this, systemDir, mHandler);
        mIntentFirewall = new IntentFirewall(new IntentFirewallInterface(), mHandler);
        mTaskChangeNotificationController =
                new TaskChangeNotificationController(this, mStackSupervisor, mHandler);
        mActivityStarter = new ActivityStarter(this, mStackSupervisor);
        mRecentTasks = new RecentTasks(this, mStackSupervisor);

        mProcessCpuThread = new Thread("CpuTracker") {
            @Override
            public void run() {
                synchronized (mProcessCpuTracker) {
                    mProcessCpuInitLatch.countDown();
                    mProcessCpuTracker.init();
                }
                while (true) {
                    try {
                        try {
                            synchronized(this) {
                                final long now = SystemClock.uptimeMillis();
                                long nextCpuDelay = (mLastCpuTime.get()+MONITOR_CPU_MAX_TIME)-now;
                                long nextWriteDelay = (mLastWriteTime+BATTERY_STATS_TIME)-now;
                                //Slog.i(TAG, "Cpu delay=" + nextCpuDelay
                                //        + ", write delay=" + nextWriteDelay);
                                if (nextWriteDelay < nextCpuDelay) {
                                    nextCpuDelay = nextWriteDelay;
                                }
                                if (nextCpuDelay > 0) {
                                    mProcessCpuMutexFree.set(true);
                                    this.wait(nextCpuDelay);
                                }
                            }
                        } catch (InterruptedException e) {
                        }
                        updateCpuStatsNow();
                    } catch (Exception e) {
                        Slog.e(TAG, "Unexpected exception collecting process stats", e);
                    }
                }
            }
        };

        ...
    }
```

从AMS的构造器我们就可以看到主要做一些初始化的工作
- 初始化一些HandlerThread用于异步处理耗时消息，比如`mHandlerThread是ActivityManagerService`线程，mProcStartHandlerThread是`ActivityManagerService:procStart`线程;
- 初始化一些Handler，比如mHandler(MainHandler)是个运行在ActivityManagerServicer线程的类,mUiHandler(UiHandler)是个运行在android.ui线程的类，mProcStartHandler(Handler)；
- 初始化处理四大组件的类，ActivityStackSupervisor、ActiveService、BroadcastQueue等;
- AMS的职责还包括对进程和电量的管理.通过updateOomAdjLocked、updateLruProcessLocked、updateProcessForegroundLocked等方法将进程分为四种.

    - foreground process 
    - visible process
    - service process 
    - cached process

### *start方法*{:.header3-font}

```java
 private void start() {
        removeAllProcessGroups();
        mProcessCpuThread.start();

        mBatteryStatsService.publish(mContext);
        mAppOpsService.publish(mContext);
        Slog.d("AppOps", "AppOpsService published");
        LocalServices.addService(ActivityManagerInternal.class, new LocalService());
        // Wait for the synchronized block started in mProcessCpuThread,
        // so that any other acccess to mProcessCpuTracker from main thread
        // will be blocked during mProcessCpuTracker initialization.
        try {
            mProcessCpuInitLatch.await();
        } catch (InterruptedException e) {
            Slog.wtf(TAG, "Interrupted wait during start", e);
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Interrupted wait during start");
        }
    }
```

&emsp;&emsp;start方法中最为主要的就是启动线程ProcessCpuThread，在AMS的构造过程中，就初始化了ProcessCPUThread对象。通过CountDownLatch#await方法判断count值如果不为0，则阻塞主线程，然后在mProcessCpuThread线程中(线程名为：CpuTracker)中将count值减少1，致使被主线程继续执行任务。
```java
mProcessCpuThread = new Thread("CpuTracker") {
            @Override
            public void run() {
                synchronized (mProcessCpuTracker) {
                    mProcessCpuInitLatch.countDown();
                    mProcessCpuTracker.init();
                }
                while (true) {
                    try {
                        try {
                            synchronized(this) {
                                final long now = SystemClock.uptimeMillis();
                                long nextCpuDelay = (mLastCpuTime.get()+MONITOR_CPU_MAX_TIME)-now;
                                long nextWriteDelay = (mLastWriteTime+BATTERY_STATS_TIME)-now;
                                //Slog.i(TAG, "Cpu delay=" + nextCpuDelay
                                //        + ", write delay=" + nextWriteDelay);
                                if (nextWriteDelay < nextCpuDelay) {
                                    nextCpuDelay = nextWriteDelay;
                                }
                                if (nextCpuDelay > 0) {
                                    mProcessCpuMutexFree.set(true);
                                    this.wait(nextCpuDelay);
                                }
                            }
                        } catch (InterruptedException e) {
                        }
                        updateCpuStatsNow();
                    } catch (Exception e) {
                        Slog.e(TAG, "Unexpected exception collecting process stats", e);
                    }
                }
            }
        };
```
&emsp;&emsp;ProcessCPUThread线程是一个轮询器，用来更新ProcessCpuTracker对象的成员变量，也就是将最新cpu stat数据提供给AMS。

更新的方式有以下几种：
- 通过ProcessCPUThread的notify方法让正在等待的ProcessCPUThread线程，继续执行线程。AMS的updateCpuStats方法就是封装了notify。
- 定时刷新的时间。当其他线程没有调用ProcessCPUThread的notify，那么超过定时的时间之后就会自动刷新。

```java
 private final void startProcessLocked(ProcessRecord app, String hostingType,
            String hostingNameStr, String abiOverride, String entryPoint, String[] entryPointArgs) {
    ...
    
    checkTime(startTime, "startProcess: starting to update cpu stats");
    updateCpuStats();
    checkTime(startTime, "startProcess: done updating cpu stats");
    ...
}
```
&emsp;&emsp;通过ProcessCPUThread的notify刷新的场景有很多，比如上面代码展示的，启动一个进程，就会刷新。如果你用过Linux终端程序Htop的话，那么Htop就相当于ProcessCpuTracker。这里在说一下，AMS中处理有监控CPU的还有监控内存的MemInfoReader。

### *systemReady方法*{:.header3-font}

```java
public void systemReady(final Runnable goingCallback, BootTimingsTraceLog traceLog) {

    synchronized(this) {
            if (mSystemReady) {
                // If we're done calling all the receivers, run the next "boot phase" passed in
                // by the SystemServer
                if (goingCallback != null) {
                    goingCallback.run();
                }
                return;
            }

        ...
    }
    ...
    
    retrieveSettings();
    final int currentUserId;
        synchronized (this) {
            currentUserId = mUserController.getCurrentUserIdLocked();
            readGrantedUriPermissionsLocked();
    }
    
    ...
    traceLog.traceBegin("ActivityManagerStartApps");
    ...
     synchronized (this) {
            // Only start up encryption-aware persistent apps; once user is
            // unlocked we'll come back around and start unaware apps
            startPersistentApps(PackageManager.MATCH_DIRECT_BOOT_AWARE);
            
            ...
            
            startHomeActivityLocked(currentUserId, "systemReady");
            
            try {
                if (AppGlobals.getPackageManager().hasSystemUidErrors()) {
                    Slog.e(TAG, "UIDs on the system are inconsistent, you need to wipe your"
                            + " data partition or your device will be unstable.");
                    mUiHandler.obtainMessage(SHOW_UID_ERROR_UI_MSG).sendToTarget();
                }
            } catch (RemoteException e) {
            }

            if (!Build.isBuildConsistent()) {
                Slog.e(TAG, "Build fingerprint is not consistent, warning user");
                mUiHandler.obtainMessage(SHOW_FINGERPRINT_ERROR_UI_MSG).sendToTarget();
            }
            
            long ident = Binder.clearCallingIdentity();
            try {
                Intent intent = new Intent(Intent.ACTION_USER_STARTED);
                intent.addFlags(Intent.FLAG_RECEIVER_REGISTERED_ONLY
                        | Intent.FLAG_RECEIVER_FOREGROUND);
                intent.putExtra(Intent.EXTRA_USER_HANDLE, currentUserId);
                broadcastIntentLocked(null, null, intent,
                        null, null, 0, null, null, null, AppOpsManager.OP_NONE,
                        null, false, false, MY_PID, SYSTEM_UID,
                        currentUserId);
                intent = new Intent(Intent.ACTION_USER_STARTING);
                intent.addFlags(Intent.FLAG_RECEIVER_REGISTERED_ONLY);
                intent.putExtra(Intent.EXTRA_USER_HANDLE, currentUserId);
                broadcastIntentLocked(null, null, intent,
                        null, new IIntentReceiver.Stub() {
                            @Override
                            public void performReceive(Intent intent, int resultCode, String data,
                                    Bundle extras, boolean ordered, boolean sticky, int sendingUser)
                                    throws RemoteException {
                            }
                        }, 0, null, null,
                        new String[] {INTERACT_ACROSS_USERS}, AppOpsManager.OP_NONE,
                        null, true, false, MY_PID, SYSTEM_UID, UserHandle.USER_ALL);
            } catch (Throwable t) {
                Slog.wtf(TAG, "Failed sending first user broadcasts", t);
            } finally {
                Binder.restoreCallingIdentity(ident);
            }
            
            mStackSupervisor.resumeFocusedStackTopActivityLocked();
            mUserController.sendUserSwitchBroadcastsLocked(-1, currentUserId);
            traceLog.traceEnd(); // ActivityManagerStartApps
            traceLog.traceEnd(); // PhaseActivityManagerReady
     }
     
    
}
```

systemReady方法就是启动AMS的关键方法了，这个方法里面有几个比较核心的流程如下：

- startPersistentApps
- startHomeActivityLocked
- broadcastIntentLocked
- ActivityStackSupervisor#resumeFocusedStackTopActivityLocked

#### startPersistentApps
---
&emsp;&emsp;startPersistentApps方法启动的是一些系统级别的应用，比如TeleService应用。通过`directBootAware`标签来标识。这些应用属于应用层，在应用层用来和framework层交互的桥梁。

>packages/services/Telephony/AndroidManifest.xml
{:.filename}
```xml
<application android:name="PhoneApp"
            android:persistent="true"
            android:label="@string/phoneAppLabel"
            android:icon="@mipmap/ic_launcher_phone"
            android:allowBackup="false"
            android:supportsRtl="true"
            android:usesCleartextTraffic="true"
            android:defaultToDeviceProtectedStorage="true"
            android:directBootAware="true">
    ...
    
</application>  
```

#### startHomeActivityLocked

&emsp;&emsp;这一步没有什么好说的，就是启动launcher应用

#### broadcastIntentLocked
---

```java
final int broadcastIntentLocked(ProcessRecord callerApp,
            String callerPackage, Intent intent, String resolvedType,
            IIntentReceiver resultTo, int resultCode, String resultData,
            Bundle resultExtras, String[] requiredPermissions, int appOp, Bundle bOptions,
            boolean ordered, boolean sticky, int callingPid, int callingUid, int userId) {
            
        if (action != null) {
        ...
         switch (action) {
                case Intent.ACTION_UID_REMOVED:
                case Intent.ACTION_PACKAGE_REMOVED:
                case Intent.ACTION_PACKAGE_CHANGED:
                case Intent.ACTION_EXTERNAL_APPLICATIONS_UNAVAILABLE:
                case Intent.ACTION_EXTERNAL_APPLICATIONS_AVAILABLE:
                case Intent.ACTION_PACKAGES_SUSPENDED:
                case Intent.ACTION_PACKAGES_UNSUSPENDED:
                
                ...
        }
            
        // Add to the sticky list if requested.
        if (sticky) {
        
        ...
        }
        
        ...
        if ((receivers != null && receivers.size() > 0)
                || resultTo != null) {        
            
            if (oldRecord != null) {
            
            ...
                 
            } else {
                queue.enqueueOrderedBroadcastLocked(r);
                queue.scheduleBroadcastsLocked();
            }
        } else {
            // There was nobody interested in the broadcast, but we still want to record
            // that it happened.
            if (intent.getComponent() == null && intent.getPackage() == null
                    && (intent.getFlags()&Intent.FLAG_RECEIVER_REGISTERED_ONLY) == 0) {
                // This was an implicit broadcast... let's record it for posterity.
                addBroadcastStatLocked(intent.getAction(), callerPackage, 0, 0, 0);
            }
        }

        return ActivityManager.BROADCAST_SUCCESS;  
}         
```
&emsp;&emsp;broadcastIntentLocked方法很简单就是会区分系统广播（只存在于内部系统，不提供给第三发应用）和第三发应用广播，然后采取不同的处理方式发送。处理这个还会实现粘性广播。关于广播的具体发送逻辑，我们后面再讲。



#### ActivityStackSupervisor#resumeFocusedStackTopActivityLocked
----

>frameworks/base/services/core/java/.../am/ActivityStackSupervisor.java
{:.filename}
```java
    boolean resumeFocusedStackTopActivityLocked() {
        return resumeFocusedStackTopActivityLocked(null, null, null);
    }

    boolean resumeFocusedStackTopActivityLocked(
            ActivityStack targetStack, ActivityRecord target, ActivityOptions targetOptions) {
        if (targetStack != null && isFocusedStack(targetStack)) {
            return targetStack.resumeTopActivityUncheckedLocked(target, targetOptions);
        }
        final ActivityRecord r = mFocusedStack.topRunningActivityLocked();
        if (r == null || r.state != RESUMED) {
            mFocusedStack.resumeTopActivityUncheckedLocked(null, null);
        } else if (r.state == RESUMED) {
            // Kick off any lingering app transitions form the MoveTaskToFront operation.
            mFocusedStack.executeAppTransition(targetOptions);
        }
        return false;
    }
```

resumeTopActivityUncheckedLocked会将存储Activity的栈推到最前面并且将栈中的想要启动的Activity置于顶部。ActivityStackSupervisor和ActivityStack两者的区别在于，ActivityStackSupervisor主要管理者栈、任务等，而ActivityStack就是管理Activity的具体调度。下面我们还会将四大组件的启动流程。



<!-- ## *4.Reference*{:.header2-font} -->

