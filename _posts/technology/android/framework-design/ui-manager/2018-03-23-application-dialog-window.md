---
layout: post
title: 这些Window们 --- Dialog的Window创建
description: 子窗口
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

### *创建Dialog*{:.header3-font}

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

### *setContentView*{:.header3-font}

```java
public void setContentView(@LayoutRes int layoutResID) {
        mWindow.setContentView(layoutResID);
    }
```
&emsp;&emsp;和Activity一样都是通过Window的setContentView方法，来完成DecorView的创建和布局的加载。完成了这些下面就是要让WMS把我们的布局展现出来了。Activity是在onResum阶段之后调用了Activity的makeVisible方法完成的。那么Dialog是怎么做的 ？答案是通过Dialog的show方法。

### *show*{:.header3-font}

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
