---
layout: post
title: Android | WMS服务
description: Window的管理者
author: 电解质
date: 2018-03-22
tag:
- android
---
* TOC
{:toc}

## *启动流程*
WMS启动流程中主要的方法也就是下面的三个：
- main
- displayReady
- systemReady

### *main方法*{:.header3-font}
```java
public static WindowManagerService main(final Context context, final InputManagerService im,
            final boolean haveInputMethods, final boolean showBootMsgs, final boolean onlyCore,
            WindowManagerPolicy policy) {
        DisplayThread.getHandler().runWithScissors(() ->
                sInstance = new WindowManagerService(context, im, haveInputMethods, showBootMsgs,
                        onlyCore, policy), 0);
        return sInstance;
    }
```
&emsp;&emsp;使用android.display工作线程初始化WindowManagerService对象，接下来来看看WMS构造器。

WindowManagerService构造器
```java
   private WindowManagerService(Context context, InputManagerService inputManager,
            boolean haveInputMethods, boolean showBootMsgs, boolean onlyCore,
            WindowManagerPolicy policy) {
        installLock(this, INDEX_WINDOW);
        mRoot = new RootWindowContainer(this);
        mContext = context;
        mHaveInputMethods = haveInputMethods;
        mAllowBootMessages = showBootMsgs;
        mOnlyCore = onlyCore;
        mLimitedAlphaCompositing = context.getResources().getBoolean(
                com.android.internal.R.bool.config_sf_limitedAlpha);
        mHasPermanentDpad = context.getResources().getBoolean(
                com.android.internal.R.bool.config_hasPermanentDpad);
        mInTouchMode = context.getResources().getBoolean(
                com.android.internal.R.bool.config_defaultInTouchMode);
        mDrawLockTimeoutMillis = context.getResources().getInteger(
                com.android.internal.R.integer.config_drawLockTimeoutMillis);
        mAllowAnimationsInLowPowerMode = context.getResources().getBoolean(
                com.android.internal.R.bool.config_allowAnimationsInLowPowerMode);
        mMaxUiWidth = context.getResources().getInteger(
                com.android.internal.R.integer.config_maxUiWidth);
        mInputManager = inputManager; // Must be before createDisplayContentLocked.
        mDisplayManagerInternal = LocalServices.getService(DisplayManagerInternal.class);
        mDisplaySettings = new DisplaySettings();
        mDisplaySettings.readSettingsLocked();

        mWindowPlacerLocked = new WindowSurfacePlacer(this);
        mPolicy = policy;
        mTaskSnapshotController = new TaskSnapshotController(this);

        LocalServices.addService(WindowManagerPolicy.class, mPolicy);

        if(mInputManager != null) {
            final InputChannel inputChannel = mInputManager.monitorInput(TAG_WM);
            mPointerEventDispatcher = inputChannel != null
                    ? new PointerEventDispatcher(inputChannel) : null;
        } else {
            mPointerEventDispatcher = null;
        }

        mFxSession = new SurfaceSession();
        mDisplayManager = (DisplayManager)context.getSystemService(Context.DISPLAY_SERVICE);
        mDisplays = mDisplayManager.getDisplays();
        for (Display display : mDisplays) {
            createDisplayContentLocked(display);
        }

        mKeyguardDisableHandler = new KeyguardDisableHandler(mContext, mPolicy);

        mPowerManager = (PowerManager)context.getSystemService(Context.POWER_SERVICE);
        mPowerManagerInternal = LocalServices.getService(PowerManagerInternal.class);

        if (mPowerManagerInternal != null) {
            mPowerManagerInternal.registerLowPowerModeObserver(
                    new PowerManagerInternal.LowPowerModeListener() {
                @Override
                public int getServiceType() {
                    return ServiceType.ANIMATION;
                }

                @Override
                public void onLowPowerModeChanged(PowerSaveState result) {
                    synchronized (mWindowMap) {
                        final boolean enabled = result.batterySaverEnabled;
                        if (mAnimationsDisabled != enabled && !mAllowAnimationsInLowPowerMode) {
                            mAnimationsDisabled = enabled;
                            dispatchNewAnimatorScaleLocked(null);
                        }
                    }
                }
            });
            mAnimationsDisabled = mPowerManagerInternal
                    .getLowPowerState(ServiceType.ANIMATION).batterySaverEnabled;
        }
        mScreenFrozenLock = mPowerManager.newWakeLock(
                PowerManager.PARTIAL_WAKE_LOCK, "SCREEN_FROZEN");
        mScreenFrozenLock.setReferenceCounted(false);

        mAppTransition = new AppTransition(context, this);
        mAppTransition.registerListenerLocked(mActivityManagerAppTransitionNotifier);

        final AnimationHandler animationHandler = new AnimationHandler();
        animationHandler.setProvider(new SfVsyncFrameCallbackProvider());
        mBoundsAnimationController = new BoundsAnimationController(context, mAppTransition,
                AnimationThread.getHandler(), animationHandler);

        mActivityManager = ActivityManager.getService();
        mAmInternal = LocalServices.getService(ActivityManagerInternal.class);
        mAppOps = (AppOpsManager)context.getSystemService(Context.APP_OPS_SERVICE);
        AppOpsManager.OnOpChangedInternalListener opListener =
                new AppOpsManager.OnOpChangedInternalListener() {
                    @Override public void onOpChanged(int op, String packageName) {
                        updateAppOpsState();
                    }
                };
        mAppOps.startWatchingMode(OP_SYSTEM_ALERT_WINDOW, null, opListener);
        mAppOps.startWatchingMode(AppOpsManager.OP_TOAST_WINDOW, null, opListener);

        // Get persisted window scale setting
        mWindowAnimationScaleSetting = Settings.Global.getFloat(context.getContentResolver(),
                Settings.Global.WINDOW_ANIMATION_SCALE, mWindowAnimationScaleSetting);
        mTransitionAnimationScaleSetting = Settings.Global.getFloat(context.getContentResolver(),
                Settings.Global.TRANSITION_ANIMATION_SCALE,
                context.getResources().getFloat(
                        R.dimen.config_appTransitionAnimationDurationScaleDefault));

        setAnimatorDurationScale(Settings.Global.getFloat(context.getContentResolver(),
                Settings.Global.ANIMATOR_DURATION_SCALE, mAnimatorDurationScaleSetting));

        IntentFilter filter = new IntentFilter();
        // Track changes to DevicePolicyManager state so we can enable/disable keyguard.
        filter.addAction(ACTION_DEVICE_POLICY_MANAGER_STATE_CHANGED);
        // Listen to user removal broadcasts so that we can remove the user-specific data.
        filter.addAction(Intent.ACTION_USER_REMOVED);
        mContext.registerReceiver(mBroadcastReceiver, filter);

        mSettingsObserver = new SettingsObserver();

        mHoldingScreenWakeLock = mPowerManager.newWakeLock(
                PowerManager.SCREEN_BRIGHT_WAKE_LOCK | PowerManager.ON_AFTER_RELEASE, TAG_WM);
        mHoldingScreenWakeLock.setReferenceCounted(false);

        mAnimator = new WindowAnimator(this);

        mAllowTheaterModeWakeFromLayout = context.getResources().getBoolean(
                com.android.internal.R.bool.config_allowTheaterModeWakeFromWindowLayout);


        LocalServices.addService(WindowManagerInternal.class, new LocalService());
        initPolicy();

        // Add ourself to the Watchdog monitors.
        Watchdog.getInstance().addMonitor(this);

        openSurfaceTransaction();
        try {
            createWatermarkInTransaction();
        } finally {
            closeSurfaceTransaction();
        }

        showEmulatorDisplayOverlayIfNeeded();
    }
```

### *displayReady方法*{:.header3-font}
```java
   public void displayReady() {
        for (Display display : mDisplays) {
            displayReady(display.getDisplayId());
        }

        synchronized(mWindowMap) {
            final DisplayContent displayContent = getDefaultDisplayContentLocked();
            if (mMaxUiWidth > 0) {
                displayContent.setMaxUiWidth(mMaxUiWidth);
            }
            readForcedDisplayPropertiesLocked(displayContent);
            mDisplayReady = true;
        }

        try {
            mActivityManager.updateConfiguration(null);
        } catch (RemoteException e) {
        }

        synchronized(mWindowMap) {
            mIsTouchDevice = mContext.getPackageManager().hasSystemFeature(
                    PackageManager.FEATURE_TOUCHSCREEN);
            configureDisplayPolicyLocked(getDefaultDisplayContentLocked());
        }

        try {
            mActivityManager.updateConfiguration(null);
        } catch (RemoteException e) {
        }

        updateCircularDisplayMaskIfNeeded();
    }
```

### *systemReady方法*{:.header3-font}
```java
 public void systemReady() {
        mPolicy.systemReady();
        mTaskSnapshotController.systemReady();
 } 
```

WindowManagerPolicy是一个接口，其实现类为PhoneWindowManager,所以systemReady的源代码如下

```java
    @Override
    public void systemReady() {
        // In normal flow, systemReady is called before other system services are ready.
        // So it is better not to bind keyguard here.
        mKeyguardDelegate.onSystemReady();

        mVrManagerInternal = LocalServices.getService(VrManagerInternal.class);
        if (mVrManagerInternal != null) {
            mVrManagerInternal.addPersistentVrModeStateListener(mPersistentVrModeListener);
        }

        readCameraLensCoverState();
        updateUiMode();
        synchronized (mLock) {
            updateOrientationListenerLp();
            mSystemReady = true;
            mHandler.post(new Runnable() {
                @Override
                public void run() {
                    updateSettings();
                }
            });
            // If this happens, for whatever reason, systemReady came later than systemBooted.
            // And keyguard should be already bound from systemBooted
            if (mSystemBooted) {
                mKeyguardDelegate.onBootCompleted();
            }
        }

        mSystemGestures.systemReady();
        mImmersiveModeConfirmation.systemReady();

        mAutofillManagerInternal = LocalServices.getService(AutofillManagerInternal.class);
    }
```



<!-- ## *4.Reference*{:.header2-font} -->

