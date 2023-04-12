---
layout: post
title: Android | Window
description: 打开窗口看UI
author: 电解质
date: 2018-03-23
tag:
- android
- renderer-ui
---
* TOC
{:toc}

Window在Android中是非常重要的，围绕其实现的系统也是非常的复杂，但是Android团队通过封装其Framework层接口，向外提供了WindowManager，能让开发者简单而又快速的add自己的view。不过对于想更加深入理解像应用窗口、子窗口、系统窗口如何被coding出来的程序员来说，阅读Activity、Dialog、Toast等是非常有用的。

## *Window*
### *窗口类型(type)*

首先要知道Android中窗口的分布是按照z-order的，也就是指向屏幕外的z轴。z-order值越大，就会覆盖住值越小的，从而也就更能被我们看到。这些值被按照窗口类型分为：应用窗口（1-99）、子窗口（1000 - 1999）、系统窗口（2000-2999）

![]({{site.asseturl}}/{{ page.date | date: "%Y-%m-%d" }}/2018-03-23-Window-types.png)

### *窗口标识(flag)*
其次，你还可以控制窗口的flag，是否焦点、是否允许在锁屏显示、是否全屏等。

![]({{site.asseturl}}/{{ page.date | date: "%Y-%m-%d" }}/2018-03-23-Window-flags.png)

### *软键盘与窗口的调校模式(soft input mode)*
还有控制ime的参数

![]({{site.asseturl}}/{{ page.date | date: "%Y-%m-%d" }}/2018-03-23-Window-softinput.png)


当然了你还可以设置窗口的其他属性，比如宽高、透明度、gravity、margin等。

## *Activity的应用窗口创建* 

### *attach*

&emsp;&emsp;当Activity被ClassLoader加载到应用进程之后，初始化的过程就最先调用attach方法,不明白的可以看看[Framework层的服务 --- AMS管理四大组件]({{site.baseurl}}/2018-03-15/framework-service-ams-component)

```java
final void attach(Context context, ActivityThread aThread,
            Instrumentation instr, IBinder token, int ident,
            Application application, Intent intent, ActivityInfo info,
            CharSequence title, Activity parent, String id,
            NonConfigurationInstances lastNonConfigurationInstances,
            Configuration config, String referrer, IVoiceInteractor voiceInteractor,
            Window window, ActivityConfigCallback activityConfigCallback) {
        attachBaseContext(context);

        mFragments.attachHost(null /*parent*/);

        mWindow = new PhoneWindow(this, window, activityConfigCallback);
        mWindow.setWindowControllerCallback(this);
        mWindow.setCallback(this);
        mWindow.setOnWindowDismissedCallback(this);
        mWindow.getLayoutInflater().setPrivateFactory(this);
        if (info.softInputMode != WindowManager.LayoutParams.SOFT_INPUT_STATE_UNSPECIFIED) {
            mWindow.setSoftInputMode(info.softInputMode);
        }
        if (info.uiOptions != 0) {
            mWindow.setUiOptions(info.uiOptions);
        }

        ...

        mWindow.setWindowManager(
                (WindowManager)context.getSystemService(Context.WINDOW_SERVICE),
                mToken, mComponent.flattenToString(),
                (info.flags & ActivityInfo.FLAG_HARDWARE_ACCELERATED) != 0);
        if (mParent != null) {
            mWindow.setContainer(mParent.getWindow());
        }
        mWindowManager = mWindow.getWindowManager();
        mCurrentConfig = config;

        mWindow.setColorMode(info.colorMode);
    }
```

&emsp;&emsp;Activity的attach方法中，会通过Window的实现类PhoneWindow创建一个Window，并且通过一些回调方法通知Activity做一些事情，也会设置和窗口自身相关的颜色、ui，以及出现窗口之后ime对应的模式等，其中我们最为熟悉的回调接口有Callback。下面罗列了它的部分方法。

frameworks/base/core/java/android/view/Window.java
```java
 public interface Callback {
        //点击事件分发
        public boolean dispatchKeyEvent(KeyEvent event);
        
        ...
        
        public boolean dispatchTouchEvent(MotionEvent event);
        
        ...
        //menu创建
        public boolean onCreatePanelMenu(int featureId, Menu menu);
        ...
        
        public boolean onMenuItemSelected(int featureId, MenuItem item);
        
        ...
        //window属性、内容变化
        public void onWindowAttributesChanged(WindowManager.LayoutParams attrs);

        public void onContentChanged();
        
        public void onWindowFocusChanged(boolean hasFocus);
        
        ...
        public void onAttachedToWindow();
         
        ... 
        public void onDetachedFromWindow();

        ...
        public boolean onSearchRequested();

        ...
        //action mode类型的menu，menu类型还有context menu、option menu
        public ActionMode onWindowStartingActionMode(ActionMode.Callback callback);

        ...
        public void onActionModeStarted(ActionMode mode);
        ...
        public void onActionModeFinished(ActionMode mode);
}
```
&emsp;&emsp;dispatchXxx方法就是事件分发，由于Activity实现了Window$Callback的dispatchXxx方法才让其具备了接收点击事件的能力。

如果忘记了点击事件的分发，看看这个流程就清楚了。
```
ViewrootImpl$ViewPostImeInputStage#processKeyEvent
---> DecorView#dispatchTouchEvent
--> Activity(Window$Callback)#dispatchTouchEvent
---> Window#superDispatchTouchEvent
---> DecorView#superDispatchTouchEvent
---> ViewGroup
---> View
```

&emsp;&emsp;除了dispatchXxxx方法，Activity还override了onWindowAttributesChanged、onContentChanged(DecorView被创建后回调）、onWindowFocusChanged等

```
ViewRootImpl$ViewRootHandler#handleMessage
--->View#dispatchWindowFocusChanged
--->DecorView#onWindowFocusChanged
--->View#onWindowFocusChanged
--->Activity(Window$Callback)#onWindowFocusChanged
```


### *setTheme*
```java
  @Override
    public void setTheme(int resid) {
        super.setTheme(resid);
        mWindow.setTheme(resid);
    }
```

PhoneWindow是Window在手机上的实现类,所以这里其实调用的是PhoneWindow的setTheme方法。

frameworks/base/core/java/com/android/internal/policy/PhoneWindow.java
```java
   @Override
    public void setTheme(int resid) {
        mTheme = resid;
        if (mDecor != null) {
            Context context = mDecor.getContext();
            if (context instanceof DecorContext) {
                context.setTheme(resid);
            }
        }
    }
```
Context的实现类ContextImpl

/Users/hawks.jamesf/AOSP8.0r1/frameworks/base/core/java/android/app/ContextImpl.java

```java
    @Override
    public void setTheme(int resId) {
        synchronized (mSync) {
            if (mThemeResource != resId) {
                mThemeResource = resId;
                initializeTheme();
            }
        }
    }
    ...
    private void initializeTheme() {
        if (mTheme == null) {
            mTheme = mResources.newTheme();
        }
        mTheme.applyStyle(mThemeResource, true);
    }
```


Resource的实现类ResourcesImpl
frameworks/base/core/java/android/content/res/ResourcesImpl.java

```java
        void applyStyle(int resId, boolean force) {
            synchronized (mKey) {
                AssetManager.applyThemeStyle(mTheme, resId, force);

                mThemeResId = resId;
                mKey.append(resId, force);
            }
        }
```
&emsp;&emsp;到这里我们基本就知道了原来是通过AssetManager的native方法applyThemeStyle进行主题加载的。


### *onCreate*

在Activity这一阶段我们最常使用的就是通过setContentView加载自定义的布局，所以我们直接来看看如何其过程。

```java
    public void setContentView(@LayoutRes int layoutResID) {
        getWindow().setContentView(layoutResID);
        initWindowDecorActionBar();
    }
```
方法很简单加载内容和加载action bar，先来看看如何加载内容的。

frameworks/base/core/java/com/android/internal/policy/PhoneWindow.java
```java
    @Override
    public void setContentView(int layoutResID) {
        // Note: FEATURE_CONTENT_TRANSITIONS may be set in the process of installing the window
        // decor, when theme attributes and the like are crystalized. Do not check the feature
        // before this happens.
        if (mContentParent == null) {
            installDecor();
        } else if (!hasFeature(FEATURE_CONTENT_TRANSITIONS)) {
            mContentParent.removeAllViews();
        }

        if (hasFeature(FEATURE_CONTENT_TRANSITIONS)) {
            final Scene newScene = Scene.getSceneForLayout(mContentParent, layoutResID,
                    getContext());
            transitionTo(newScene);
        } else {
            mLayoutInflater.inflate(layoutResID, mContentParent);
        }
        mContentParent.requestApplyInsets();
        final Callback cb = getCallback();
        if (cb != null && !isDestroyed()) {
            cb.onContentChanged();
        }
        mContentParentExplicitlySet = true;
    }

}
```
对于内容的加载主要分为这几个步骤：

- 没有DecorView就创建DecorView，DecorView主要用来放置action bar和content
- 回调给实现了Window$Callback的类，提示内容已经发生了变化。

&emsp;&emsp;让我们先来看看DecorView的创建吧。

frameworks/base/core/java/com/android/internal/policy/PhoneWindow.java
```java
 private void installDecor() {
        mForceDecorInstall = false;
        if (mDecor == null) {
            mDecor = generateDecor(-1);
            mDecor.setDescendantFocusability(ViewGroup.FOCUS_AFTER_DESCENDANTS);
            mDecor.setIsRootNamespace(true);
            if (!mInvalidatePanelMenuPosted && mInvalidatePanelMenuFeatures != 0) {
                mDecor.postOnAnimation(mInvalidatePanelMenuRunnable);
            }
        } else {
            mDecor.setWindow(this);
        }
        if (mContentParent == null) {
            mContentParent = generateLayout(mDecor);
            ...    
            final DecorContentParent decorContentParent = (DecorContentParent) mDecor.findViewById(
                    R.id.decor_content_parent);
            ...
            
        }
        
        ...
        // Only inflate or create a new TransitionManager if the caller hasn't
        // already set a custom one.
        if (hasFeature(FEATURE_ACTIVITY_TRANSITIONS)) {
                if (mTransitionManager == null) {
                    final int transitionRes = getWindowStyle().getResourceId(
                            R.styleable.Window_windowContentTransitionManager,
                            0);
                    if (transitionRes != 0) {
                        final TransitionInflater inflater = TransitionInflater.from(getContext());
                        mTransitionManager = inflater.inflateTransitionManager(transitionRes,
                                mContentParent);
                    } else {
                        mTransitionManager = new TransitionManager();
                    }
                }
                
                ...
                
        }
                
 }
```
&emsp;&emsp;通过generateDecor创建DecorView，而通过generateLayout填充布局，当布局填充完成就可以获得mContentParent，而mContentParent就是用来放置我们自定义的布局。如果对于DecorView的布局不清楚，给你一个布局xml，你应该就能懂了。

frameworks/base/core/res/res/layout/screen_action_bar.xml
```xml
<com.android.internal.widget.ActionBarOverlayLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/decor_content_parent"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:splitMotionEvents="false"
    android:theme="?attr/actionBarTheme">
    <FrameLayout android:id="@android:id/content"
                 android:layout_width="match_parent"
                 android:layout_height="match_parent" />
    <com.android.internal.widget.ActionBarContainer
        android:id="@+id/action_bar_container"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_alignParentTop="true"
        style="?attr/actionBarStyle"
        android:transitionName="android:action_bar"
        android:touchscreenBlocksFocus="true"
        android:keyboardNavigationCluster="true"
        android:gravity="top">
        <com.android.internal.widget.ActionBarView
            android:id="@+id/action_bar"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            style="?attr/actionBarStyle" />
        <com.android.internal.widget.ActionBarContextView
            android:id="@+id/action_context_bar"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:visibility="gone"
            style="?attr/actionModeStyle" />
    </com.android.internal.widget.ActionBarContainer>
    <com.android.internal.widget.ActionBarContainer android:id="@+id/split_action_bar"
                  android:layout_width="match_parent"
                  android:layout_height="wrap_content"
                  style="?attr/actionBarSplitStyle"
                  android:visibility="gone"
                  android:touchscreenBlocksFocus="true"
                  android:keyboardNavigationCluster="true"
                  android:gravity="center"/>
</com.android.internal.widget.ActionBarOverlayLayout>
```
&emsp;&emsp;看完这个你应该就能反应过来，其实DecorView这个ViewGroup包裹着ActionBarOverlayLayout（父类是DecorContentParent），而ActionBarOverlayLayout包裹着content、action bar等。但是为了便于讲解很多就将DecorView和ActionBarOverlayLayout并在一块了，原本两层布局说成一层。知道这个我们再来继续看一下具体是如何填充的。

frameworks/base/core/java/com/android/internal/policy/PhoneWindow.java
```java
 protected ViewGroup generateLayout(DecorView decor) {
        // Apply data from current theme.
        ...
        
        
        // Inflate the window decor.
                int layoutResource;
        int features = getLocalFeatures();
        // System.out.println("Features: 0x" + Integer.toHexString(features));
        if ((features & (1 << FEATURE_SWIPE_TO_DISMISS)) != 0) {
            ...
        } else if ((features & ((1 << FEATURE_LEFT_ICON) | (1 << FEATURE_RIGHT_ICON))) != 0) {
            ...
            // System.out.println("Title Icons!");
        } else if ((features & ((1 << FEATURE_PROGRESS) | (1 << FEATURE_INDETERMINATE_PROGRESS))) != 0
                && (features & (1 << FEATURE_ACTION_BAR)) == 0) {
            ...
            // System.out.println("Progress!");
        } else if ((features & (1 << FEATURE_CUSTOM_TITLE)) != 0) {
            ...
        } else if ((features & (1 << FEATURE_NO_TITLE)) == 0) {
            // If no other features and not embedded, only need a title.
            // If the window is floating, we need a dialog layout
            if (mIsFloating) {
                TypedValue res = new TypedValue();
                getContext().getTheme().resolveAttribute(
                        R.attr.dialogTitleDecorLayout, res, true);
                layoutResource = res.resourceId;
            } else if ((features & (1 << FEATURE_ACTION_BAR)) != 0) {
                layoutResource = a.getResourceId(
                        R.styleable.Window_windowActionBarFullscreenDecorLayout,
                        R.layout.screen_action_bar);
            } else {
                layoutResource = R.layout.screen_title;
            }
            // System.out.println("Title!");
        } else if ((features & (1 << FEATURE_ACTION_MODE_OVERLAY)) != 0) {
            ...
        } else {
           ...
           // System.out.println("Simple!");
        }
        
        ...
        mDecor.startChanging();
        mDecor.onResourcesLoaded(mLayoutInflater, layoutResource);
        
         ViewGroup contentParent = (ViewGroup)findViewById(ID_ANDROID_CONTENT);
        ...
        mDecor.finishChanging();

        return contentParent;
}
```
&emsp;&emsp;首先根据主题来设置窗口，比如沉浸式，接着调用DecorView的onResourcesLoaded方法加载，而onResourcesLoaded方法里面先用inflate获得布局，在用addView加载布局。弄完了这些，那么自定义View如何被填充呢，`mLayoutInflater.inflate(layoutResID, mContentParent);` 就是使用inflate。尽管如此，但是DecorView并不是可见的，只要在onResume执行完之后，通过WindowManager将DecorView传给WMS，并且DecorView的属性为VISIBLE，才可见。

在OnDestory之后回调用WindowManager的removeViewImmediate让WMS去掉View。
```java
 private void handleDestroyActivity(IBinder token, boolean finishing,
            int configChanges, boolean getNonConfigInstance) {

        ActivityClientRecord r = performDestroyActivity(token, finishing,
                configChanges, getNonConfigInstance);
        if (r != null) {
            cleanUpPendingRemoveWindows(r, finishing);
            WindowManager wm = r.activity.getWindowManager();
            View v = r.activity.mDecor;
            if (v != null) {
                if (r.activity.mVisibleFromServer) {
                    mNumVisibleActivities--;
                }
                IBinder wtoken = v.getWindowToken();
                if (r.activity.mWindowAdded) {
                    if (r.mPreserveWindow) {
                        // Hold off on removing this until the new activity's
                        // window is being added.
                        r.mPendingRemoveWindow = r.window;
                        r.mPendingRemoveWindowManager = wm;
                        // We can only keep the part of the view hierarchy that we control,
                        // everything else must be removed, because it might not be able to
                        // behave properly when activity is relaunching.
                        r.window.clearContentView();
                    } else {
                        wm.removeViewImmediate(v);
                    }
                ...
                }
            ..
            }
            ...
        }
        ...
}
```
                


## *Dialog的子窗口创建*

### *创建Dialog*

```java
    Dialog(@NonNull Context context, @StyleRes int themeResId, boolean createContextThemeWrapper) {
        if (createContextThemeWrapper) {
            if (themeResId == ResourceId.ID_NULL) {
                final TypedValue outValue = new TypedValue();
                context.getTheme().resolveAttribute(R.attr.dialogTheme, outValue, true);
                themeResId = outValue.resourceId;
            }
            mContext = new ContextThemeWrapper(context, themeResId);
        } else {
            mContext = context;
        }

        mWindowManager = (WindowManager) context.getSystemService(Context.WINDOW_SERVICE);

        final Window w = new PhoneWindow(mContext);
        mWindow = w;
        w.setCallback(this);
        w.setOnWindowDismissedCallback(this);
        w.setOnWindowSwipeDismissedCallback(() -> {
            if (mCancelable) {
                cancel();
            }
        });
        w.setWindowManager(mWindowManager, null, null);
        w.setGravity(Gravity.CENTER);

        mListenersHandler = new ListenersHandler(this);
    }
```
&emsp;&emsp;很简单的构造器就是初始化Window对象，并且设置监听Window变化的回调。接着再来看看窗口的DecorView的创建和布局加载

### *setContentView*

```java
public void setContentView(@LayoutRes int layoutResID) {
        mWindow.setContentView(layoutResID);
    }
```
&emsp;&emsp;和Activity一样都是通过Window的setContentView方法，来完成DecorView的创建和布局的加载。完成了这些下面就是要让WMS把我们的布局展现出来了。Activity是在onResum阶段之后调用了Activity的makeVisible方法完成的。那么Dialog是怎么做的 ？答案是通过Dialog的show方法。

### *show*

```java
 public void show() {

        ...

        mWindowManager.addView(mDecor, l);
        mShowing = true;

    }
```
&emsp;&emsp;除了给我们提供show添加View，Dialog还为我们提供了移除View的操作，看看下面的代码你就懂了。
```java
    @Override
    public void dismiss() {
        if (Looper.myLooper() == mHandler.getLooper()) {
            dismissDialog();
        } else {
            mHandler.post(mDismissAction);
        }
    }

    void dismissDialog() {
        ...

        try {
            mWindowManager.removeViewImmediate(mDecor);
        } finally {
            if (mActionMode != null) {
                mActionMode.finish();
            }
            mDecor = null;
            mWindow.closeAllPanels();
            onStop();
            mShowing = false;

            sendDismissMessage();
        }
    }
```
&emsp;&emsp;由于Dialog的type为TYPE_APPLICATION_ATTACHED_DIALOG，之前我们讲的Activity的type是TYPE_APPLICATION，所以Dialog必须依附于Activity，其使用的token id就是父Window的，而不是Activity的AppWindowToken id。而接下来要将的Toast的TYPE_TOAST，不需要依附于任何的窗口。我们也可以定义自己的系统窗口，需要在Android manifest中声明权限，并且配置type为TYPE_APPLICATION_OVERLAY，这个Android O之后的API变动，之前的版本都是使用TYPE_SYSTEM_OVERLAY。

## *Toast的系统窗口创建*

### *addView*

frameworks/base/core/java/android/widget/Toast.java
&emsp;&emsp;当调用show时，就能显示弹出Toas，所以看看它是如何show的。
```java
    public void show() {
        if (mNextView == null) {
            throw new RuntimeException("setView must have been called");
        }

        INotificationManager service = getService();
        String pkg = mContext.getOpPackageName();
        TN tn = mTN;
        tn.mNextView = mNextView;

        try {
            service.enqueueToast(pkg, tn, mDuration);
        } catch (RemoteException e) {
            // Empty
        }
    }
```

&emsp;&emsp;主要是通过Binder将数据传给NMS，NMS将这些数据封装成ToastRecord，而这一些ToastRecord被保存在mToastQueue里面。通过showNextToastLocked来完成Toast显示。

frameworks/base/services/core/java/com/android/server/notification/NotificationManagerService.java
```java
public class NotificationManagerService extends SystemService {

   private final IBinder mService = new INotificationManager.Stub() {
        // Toasts
        // ============================================================================

        @Override
        public void enqueueToast(String pkg, ITransientNotification callback, int duration)
        {
            ...

            synchronized (mToastQueue) {
                int callingPid = Binder.getCallingPid();
                long callingId = Binder.clearCallingIdentity();
                try {
                    ToastRecord record;
                    int index = indexOfToastLocked(pkg, callback);
                    // If it's already in the queue, we update it in place, we don't
                    // move it to the end of the queue.
                    if (index >= 0) {
                        record = mToastQueue.get(index);
                        record.update(duration);
                    } else {
                        // Limit the number of toasts that any given package except the android
                        // package can enqueue.  Prevents DOS attacks and deals with leaks.
                        if (!isSystemToast) {
                            int count = 0;
                            final int N = mToastQueue.size();
                            for (int i=0; i<N; i++) {
                                 final ToastRecord r = mToastQueue.get(i);
                                 if (r.pkg.equals(pkg)) {
                                     count++;
                                     if (count >= MAX_PACKAGE_NOTIFICATIONS) {
                                         Slog.e(TAG, "Package has already posted " + count
                                                + " toasts. Not showing more. Package=" + pkg);
                                         return;
                                     }
                                 }
                            }
                        }

                        Binder token = new Binder();
                        mWindowManagerInternal.addWindowToken(token, TYPE_TOAST, DEFAULT_DISPLAY);
                        record = new ToastRecord(callingPid, pkg, callback, duration, token);
                        mToastQueue.add(record);
                        index = mToastQueue.size() - 1;
                        keepProcessAliveIfNeededLocked(callingPid);
                    }
                    // If it's at index 0, it's the current toast.  It doesn't matter if it's
                    // new or just been updated.  Call back and tell it to show itself.
                    // If the callback fails, this will remove it from the list, so don't
                    // assume that it's valid after this.
                    if (index == 0) {
                        showNextToastLocked();
                    }
                } finally {
                    Binder.restoreCallingIdentity(callingId);
                }
            }
        }
}
}
```
&emsp;&emsp;不过为了防止DOS攻击，限制了50次发送Toast。接下来让我们来看看showNextToastLocked方法。


frameworks/base/services/core/java/com/android/server/notification/NotificationManagerService.java
```java
public class NotificationManagerService extends SystemService {
   @GuardedBy("mToastQueue")
    void showNextToastLocked() {
        ToastRecord record = mToastQueue.get(0);
        while (record != null) {
            if (DBG) Slog.d(TAG, "Show pkg=" + record.pkg + " callback=" + record.callback);
            try {
                record.callback.show(record.token);
                scheduleTimeoutLocked(record);
                return;
            } catch (RemoteException e) {
                ...
            }
        }
    }
}
```
&emsp;&emsp;看到这里已经很清楚了吧，其实在Application层通过enqueueToast方法，已经将Application层的TN(Binder)传给了Framework层，当时机成熟之时就会回调给Application层。


frameworks/base/core/java/android/widget/Toast.java
```java
private static class TN extends ITransientNotification.Stub {


    TN(String packageName, @Nullable Looper looper) {
        ...
        mHandler = new Handler(looper, null) {
                @Override
                public void handleMessage(Message msg) {
                    switch (msg.what) {
                        case SHOW: {
                            IBinder token = (IBinder) msg.obj;
                            handleShow(token);
                            break;
                        }
                        case HIDE: {
                            handleHide();
                            // Don't do this in handleHide() because it is also invoked by
                            // handleShow()
                            mNextView = null;
                            break;
                        }
                        case CANCEL: {
                            handleHide();
                            // Don't do this in handleHide() because it is also invoked by
                            // handleShow()
                            mNextView = null;
                            try {
                                getService().cancelToast(mPackageName, TN.this);
                            } catch (RemoteException e) {
                            }
                            break;
                        }
                    }
                }
            };

    }
}
```
&emsp;&emsp;Application层通过Handler调度到了在show出Toas的线程。

frameworks/base/core/java/android/widget/Toast.java
```java
 public void handleShow(IBinder windowToken) {
            ...
            if (mView != mNextView) {
                // remove the old view if necessary
                handleHide();
                mView = mNextView;
                Context context = mView.getContext().getApplicationContext();
                String packageName = mView.getContext().getOpPackageName();
                if (context == null) {
                    context = mView.getContext();
                }
                mWM = (WindowManager)context.getSystemService(Context.WINDOW_SERVICE);
                // We can resolve the Gravity here by using the Locale for getting
                // the layout direction
                final Configuration config = mView.getContext().getResources().getConfiguration();
                final int gravity = Gravity.getAbsoluteGravity(mGravity, config.getLayoutDirection());
                mParams.gravity = gravity;
                if ((gravity & Gravity.HORIZONTAL_GRAVITY_MASK) == Gravity.FILL_HORIZONTAL) {
                    mParams.horizontalWeight = 1.0f;
                }
                if ((gravity & Gravity.VERTICAL_GRAVITY_MASK) == Gravity.FILL_VERTICAL) {
                    mParams.verticalWeight = 1.0f;
                }
                mParams.x = mX;
                mParams.y = mY;
                mParams.verticalMargin = mVerticalMargin;
                mParams.horizontalMargin = mHorizontalMargin;
                mParams.packageName = packageName;
                mParams.hideTimeoutMilliseconds = mDuration ==
                    Toast.LENGTH_LONG ? LONG_DURATION_TIMEOUT : SHORT_DURATION_TIMEOUT;
                mParams.token = windowToken;
                if (mView.getParent() != null) {
                    if (localLOGV) Log.v(TAG, "REMOVE! " + mView + " in " + this);
                    mWM.removeView(mView);
                }
                ...
                try {
                    mWM.addView(mView, mParams);
                    trySendAccessibilityEvent();
                } catch (WindowManager.BadTokenException e) {
                    /* ignore */
                }
            }
        }
```
&emsp;&emsp;到这里我们就知道了，如何show出一个Toast，那么如何remove掉的。其实是通过NotificationManagerService的scheduleTimeoutLocked方法。

### *removeView*

frameworks/base/services/core/java/com/android/server/notification/NotificationManagerService.java
```java

        {
        public WorkerHandler(Looper looper) {
            super(looper);
        }

        @Override
        public void handleMessage(Message msg)
        {
            switch (msg.what)
            {
                case MESSAGE_TIMEOUT:
                    handleTimeout((ToastRecord)msg.obj);
                    break;
                case MESSAGE_SAVE_POLICY_FILE:
                    handleSavePolicyFile();
                    break;
                case MESSAGE_SEND_RANKING_UPDATE:
                    handleSendRankingUpdate();
                    break;
                case MESSAGE_LISTENER_HINTS_CHANGED:
                    handleListenerHintsChanged(msg.arg1);
                    break;
                case MESSAGE_LISTENER_NOTIFICATION_FILTER_CHANGED:
                    handleListenerInterruptionFilterChanged(msg.arg1);
                    break;
            }
        }

    }
    ...
    private void handleTimeout(ToastRecord record)
    {
        if (DBG) Slog.d(TAG, "Timeout pkg=" + record.pkg + " callback=" + record.callback);
        synchronized (mToastQueue) {
            int index = indexOfToastLocked(record.pkg, record.callback);
            if (index >= 0) {
                cancelToastLocked(index);
            }
        }
    }
    ...
    @GuardedBy("mToastQueue")
    private void scheduleTimeoutLocked(ToastRecord r)
    {
        mHandler.removeCallbacksAndMessages(r);
        Message m = Message.obtain(mHandler, MESSAGE_TIMEOUT, r);
        long delay = r.duration == Toast.LENGTH_LONG ? LONG_DELAY : SHORT_DELAY;
        mHandler.sendMessageDelayed(m, delay);
    }

        @GuardedBy("mToastQueue")
    void cancelToastLocked(int index) {
        ToastRecord record = mToastQueue.get(index);
        try {
            record.callback.hide();
        } catch (RemoteException e) {
            Slog.w(TAG, "Object died trying to hide notification " + record.callback
                    + " in package " + record.pkg);
            // don't worry about this, we're about to remove it from
            // the list anyway
        }

        ToastRecord lastToast = mToastQueue.remove(index);
        mWindowManagerInternal.removeWindowToken(lastToast.token, true, DEFAULT_DISPLAY);

        keepProcessAliveIfNeededLocked(record.pid);
        if (mToastQueue.size() > 0) {
            // Show the next one. If the callback fails, this will remove
            // it from the list, so don't assume that the list hasn't changed
            // after this point.
            showNextToastLocked();
        }
    }
```
这回就明白了，原来是通过NMS中的Handler发送延时remove view的消息。然后通过TN会回到给Application层的应用，然后调用WindowManager的removeView方法。