---
layout: post
title: 这些Window们 --- Toast的Window创建
description: 系统窗口
author: 电解质
date: 2018-03-23
share: true
comments: true
tag:
- Android Senior Engineer
---
* TOC
{:toc}

## *1.Introduction*{:.header2-font}


### *addView*{:.header3-font}

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

### *removeView*{:.header3-font}

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







