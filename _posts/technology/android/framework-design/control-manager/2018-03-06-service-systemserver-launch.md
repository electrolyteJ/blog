---
layout: post
title: Framework层的服务 --- SystemServer启动流程
description: 简单梳理一下SystemServer的启动流程
author: 电解质
date: 2018-03-06
share: true
comments: true
tag:
- framework-design/service
---
* TOC
{:toc}
## *1.Summary*{:.header2-font}
&emsp;&emsp;熟悉软件的启动过程能让我们快速了解整个系统运作流程，这是入门学习一样新事物的绝佳路径，所以，让我们来了解一下Android系统framework层是如何被启动的。由于这一篇文章我们只关注framework-java层，所以SystemServer是我们要攻克的类。SystemServer是system_server进程的启动入口类，而system_server进程承载着整个framework-java层，负责与application层交互。SystemServer类会启动大都是我们熟知的类，比如ActivityManagerService、PackageManagerService、WindowManagerService，这些类都是一些binder，用来进行和application层的某个应用进程通信。为了让system_server进程常驻内存中，会开启一个looper。该looper存在于system_server进程的主线程，用来切换工作线程的任务到主线程。比如WindowManagerService$H类。
## *2.Introduction*{:.header2-font}

&emsp;&emsp;SystemServer启动流程中涉及到很多的服务，由于我们重点关注AMS、PKMS、WMS所以就让我们讲这三个服务吧。
### *SystemServer启动流程*{:.header3-font}
&emsp;&emsp;SystemServer的启动流程主要有下面这几个阶段需要我们关注一下。
- main方法
- SystemServer构造器
- run方法

那么接下来让我们从main方法开始看吧。

&emsp;&emsp;由zygote fork出system_server进程，那么必然会调用SystemServer的main方法

```java
    public static void main(String[] args) {
        new SystemServer().run();
    }
```
由于SystemServer构造器较为简单，服务的初始化都是在run方法完成的，所以重点来关注一下run方法。
```java
    private void run() {

    ...
    try {
    
        Looper.prepareMainLooper();
        
        // Initialize native services.
            System.loadLibrary("android_servers");
        ...       
        // Initialize the system context.
            createSystemContext();
            
        // Create the system service manager.
            mSystemServiceManager = new SystemServiceManager(mSystemContext);
            mSystemServiceManager.setRuntimeRestarted(mRuntimeRestart);
            LocalServices.addService(SystemServiceManager.class, mSystemServiceManager);
            // Prepare the thread pool for init tasks that can be parallelized
            SystemServerInitThreadPool.get();        
    } finally {
            traceEnd();  // InitBeforeStartServices
    }
    
    // Start services.
    try {
            traceBeginAndSlog("StartServices");
            startBootstrapServices();
            startCoreServices();
            startOtherServices();
            SystemServerInitThreadPool.shutdown();
     } catch (Throwable ex) {
            Slog.e("System", "******************************************");
            Slog.e("System", "************ Failure starting system services", ex);
            throw ex;
    } finally {
            traceEnd();
    }
        
    ...
    Looper.loop();
    ...
    
    }
```
&emsp;&emsp;在run方法中主要会有下面的一些主要初始化
- 初始化配置文件（*.prop）
- 加载so库(libandroid_servers)
- 初始化Context
- 初始化Service管理者
- 初始化众多的Service
- 启动looper

对于这些初始化我们并没有必要都去看，只要关注初始化的Context和Service。

### *初始化Context*{:.header3-font}
```java
 private void createSystemContext() {
        ActivityThread activityThread = ActivityThread.systemMain();
        mSystemContext = activityThread.getSystemContext();
        mSystemContext.setTheme(DEFAULT_SYSTEM_THEME);

        final Context systemUiContext = activityThread.getSystemUiContext();
        systemUiContext.setTheme(DEFAULT_SYSTEM_THEME);
    }
```
&emsp;&emsp;在这里我们能够看到调用了ActivityThread的systemMain静态方法去初始化了一个ActivityThread对象，不同于每个应用中的ActivityThread。那么哪里不同呢？为什么framework层要有这样一个ActivityThread对象。这里就不买关子了，framework层给ActivityThread#attach传递的参数为true，应用层传递的是false，这样我们就知道framework层有些东西不能给application层使用，来看看是什么代码。
```java
private void attach(boolean system) {
        sCurrentActivityThread = this;
        mSystemThread = system;
        if (!system) {
        
            ...
            
        } else {
            // Don't set application object here -- if the system crashes,
            // we can't display an alert, we just want to die die die.
            android.ddm.DdmHandleAppName.setAppName("system_process",
                    UserHandle.myUserId());
            try {
                mInstrumentation = new Instrumentation();
                ContextImpl context = ContextImpl.createAppContext(
                        this, getSystemContext().mPackageInfo);
                mInitialApplication = context.mPackageInfo.makeApplication(true, null);
                mInitialApplication.onCreate();
            } catch (Exception e) {
                throw new RuntimeException(
                        "Unable to instantiate Application():" + e.toString(), e);
            }
        }

        ...
}
```
&emsp;&emsp;这里我们就可以知道framework层主要做了这些事：
- 创建一个ActivityThread对象（初始化Instrumentation对象、Application对象、application类的Context对象）
- 创建一个system类的Context对象
- 创建一个systemui类的Context对象。我们都知道Context提供了一系列的全局方法，比如启动Service、BroadcastReceiver等。

&emsp;&emsp;Context的分类activityContext、applicationContext、systemuiContext、systemContext

```java
Context分类         |ContextImpl container, ActivityThread mainThread,LoadedApk packageInfo, String splitName,     Binder activityToken, UserHandle user, int flags,ClassLoader classLoader)
Activity           |                 null,                mainThread,          packageInfo, activityInfo.splitName,      activityToken,           null,         0,             classLoader
Service/Application|                 null,                mainThread,          packageInfo,                   null,               null,           null,         0,                 null
Provider           |                 this,               mMainThread,                   pi,                   null,     mActivityToken,           user,      flags,                null
systemuiContext    |                 null, systemContext.mMainThread,          packageInfo,                   null,               null,           null,         0,                 null
systemContext      |                 null,                mainThread,          packageInfo,                   null,               null,           null,         0,                 null
```

### *初始化众多的Service*{:.header3-font}
&emsp;&emsp;服务被分为三种：
- 开机服务（ActivityManagerService、PackageManagerService、PowerManagerService、LightsService、RecoverySystemService、DeviceIdentifiersPolicyService、DisplayManagerService、UserManagerService等）
- 核心服务（DropBoxManagerService、UsageStatsService、BatteryService、WebViewUpdateService等）
- 其他服务（VibratorService、WindowManagerService、TelephonyRegistry、MmsServiceBroker等）

开机服务和核心服务都是在主线程初始化的，而其他服务部分是在工作线程初始化，这样可以让其加快启动速度。


#### ActivityManagerServicee
---

先来看看ActivityManagerServicee

AMS：
```java
private void startBootstrapServices() {
        ...
        // Activity manager runs the show.
        traceBeginAndSlog("StartActivityManager");
        mActivityManagerService = mSystemServiceManager.startService(
                ActivityManagerService.Lifecycle.class).getService();
        mActivityManagerService.setSystemServiceManager(mSystemServiceManager);
        mActivityManagerService.setInstaller(installer);
        traceEnd();
        
        ...
        
        traceBeginAndSlog("InitPowerManagement");
        mActivityManagerService.initPowerManagement();
        traceEnd();
        
        ...
        
        traceBeginAndSlog("SetSystemProcess");
        mActivityManagerService.setSystemProcess();
        traceEnd();
        
        ...

}

private void startCoreServices() {
        ...
        traceBeginAndSlog("StartUsageService");
        mSystemServiceManager.startService(UsageStatsService.class);
        mActivityManagerService.setUsageStatsManager(
                LocalServices.getService(UsageStatsManagerInternal.class));
        traceEnd();
        
        ...
}

private void startOtherServices() {
    ...
    try {
        ...
        
            traceBeginAndSlog("InstallSystemProviders");
            mActivityManagerService.installSystemProviders();
            traceEnd();
            
        ...
    
            traceBeginAndSlog("InitWatchdog");
            final Watchdog watchdog = Watchdog.getInstance();
            watchdog.init(context, mActivityManagerService);
            traceEnd();
        ...
        
            traceBeginAndSlog("SetWindowManagerService");
            mActivityManagerService.setWindowManager(wm);
            traceEnd();
        }  catch (RuntimeException e) {
        ...
        }
        
    mActivityManagerService.systemReady(() -> {
        ...
        
        mActivityManagerService.startObservingNativeCrashes();
    }
            
}
```

这里我列举出来ActivityManagerService对象被调用的地方，其中我们需要知道的就四个阶段

- 构造ActivityManagerService
- start
- setSystemServiceManager
- setInstaller
- systemReady

#### PackageManagerService
---

PKMS:
```java
  private void startBootstrapServices() {
 
        ...
        traceBeginAndSlog("StartPackageManagerService");
        mPackageManagerService = PackageManagerService.main(mSystemContext, installer,
                mFactoryTestMode != FactoryTest.FACTORY_TEST_OFF, mOnlyCore);
        mFirstBoot = mPackageManagerService.isFirstBoot();
        mPackageManager = mSystemContext.getPackageManager();
        traceEnd();
        
        ...
         if (!mOnlyCore) {
            boolean disableOtaDexopt = SystemProperties.getBoolean("config.disable_otadexopt",
                    false);
            if (!disableOtaDexopt) {
                traceBeginAndSlog("StartOtaDexOptService");
                try {
                    OtaDexoptService.main(mSystemContext, mPackageManagerService);
                } catch (Throwable e) {
                    reportWtf("starting OtaDexOptService", e);
                } finally {
                    traceEnd();
                }
            }
        }
        ...
  }
  
  private void startOtherServices() {
        ...
  
        if (!mOnlyCore) {
            traceBeginAndSlog("UpdatePackagesIfNeeded");
            try {
                mPackageManagerService.updatePackagesIfNeeded();
            } catch (Throwable e) {
                reportWtf("update packages", e);
            }
            traceEnd();
        }

        traceBeginAndSlog("PerformFstrimIfNeeded");
        try {
            mPackageManagerService.performFstrimIfNeeded();
        } catch (Throwable e) {
            reportWtf("performing fstrim", e);
        }
        traceEnd();
        ....
        
        traceBeginAndSlog("MakePackageManagerServiceReady");
        try {
            mPackageManagerService.systemReady();
        } catch (Throwable e) {
            reportWtf("making Package Manager Service ready", e);
        }
        traceEnd();
        
        ...
  }
```

这里我列举出来PackageManagerService对象被调用的地方，其中我们需要知道的就三个阶段
- main
- updatePackagesIfNeeded
- performFstrimIfNeeded
- systemReady


#### WindowManagerService
---

WMS:
```java
private void startOtherServices() {
        ...
        WindowManagerService wm = null;
        ...
        try {
            ...
    
            traceBeginAndSlog("StartWindowManagerService");
            // WMS needs sensor service ready
            ConcurrentUtils.waitForFutureNoInterrupt(mSensorServiceStart, START_SENSOR_SERVICE);
            mSensorServiceStart = null;
            wm = WindowManagerService.main(context, inputManager,
                    mFactoryTestMode != FactoryTest.FACTORY_TEST_LOW_LEVEL,
                    !mFirstBoot, mOnlyCore, new PhoneWindowManager());
            ServiceManager.addService(Context.WINDOW_SERVICE, wm);
            ServiceManager.addService(Context.INPUT_SERVICE, inputManager);
            traceEnd();
            
            ...
        } catch (RuntimeException e) {
            Slog.e("System", "******************************************");
            Slog.e("System", "************ Failure starting core service", e);
        }
        
        ...
        
        traceBeginAndSlog("MakeDisplayReady");
        try {
            wm.displayReady();
        } catch (Throwable e) {
            reportWtf("making display ready", e);
        }
        traceEnd();
        
        ...
        if (mFactoryTestMode != FactoryTest.FACTORY_TEST_LOW_LEVEL) {
        
            ...
            
            if (!disableSystemUI) {
                traceBeginAndSlog("StartStatusBarManagerService");
                try {
                    statusBar = new StatusBarManagerService(context, wm);
                    ServiceManager.addService(Context.STATUS_BAR_SERVICE, statusBar);
                } catch (Throwable e) {
                    reportWtf("starting StatusBarManagerService", e);
                }
                traceEnd();
            }
            
            ...
        
        }
        
        ...
        
        final boolean safeMode = wm.detectSafeMode();
        
        ...
        
        traceBeginAndSlog("MakeWindowManagerServiceReady");
        try {
            wm.systemReady();
        } catch (Throwable e) {
            reportWtf("making Window Manager Service ready", e);
        }
        traceEnd();
        
        ...
        
         final Configuration config = wm.computeNewConfiguration(DEFAULT_DISPLAY);
         ...
         
         final WindowManagerService windowManagerF = wm;
         
         ...
         
         mActivityManagerService.systemReady(() -> {
            ...
            traceBeginAndSlog("StartSystemUI");
            try {
                startSystemUi(context, windowManagerF);
            } catch (Throwable e) {
                reportWtf("starting System UI", e);
            }
            traceEnd();
            ...
         }
}

static final void startSystemUi(Context context, WindowManagerService windowManager) {
        Intent intent = new Intent();
        intent.setComponent(new ComponentName("com.android.systemui",
                    "com.android.systemui.SystemUIService"));
        intent.addFlags(Intent.FLAG_DEBUG_TRIAGED_MISSING);
        //Slog.d(TAG, "Starting service: " + intent);
        context.startServiceAsUser(intent, UserHandle.SYSTEM);
        windowManager.onSystemUiStarted();
    }
```

这里我列举出来WindowManagerService对象被调用的地方，其中我们需要知道的就三个阶段
- main
- displayReady
- systemReady