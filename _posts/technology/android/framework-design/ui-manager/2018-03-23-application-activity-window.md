---
layout: post
title: 这些Window们 --- Activity的Window创建
description: 应用窗口
author: 电解质
date: 2018-03-23
share: true
comments: true
tag:
- android-framework-design
---
* TOC
{:toc}

## *1.Introduction*{:.header2-font}

### *attach*{:.header3-font}

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


### *setTheme*{:.header3-font}
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


### *onCreate*{:.header3-font}

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
                



