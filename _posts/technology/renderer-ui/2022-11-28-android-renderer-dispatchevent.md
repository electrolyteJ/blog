---
layout: post
title: Android | Android UI事件分发
description: 事件分发
tag:
- android
- renderer-ui
---
* TOC
{:toc}


# *View树事件分发*
说完了View树的测绘过程，我们还需要来了解它的事件分发。
```
input pipline
1. aq:native-pre-ime(NativePreImeInputStage)
Delivers `pre-ime` input events `to a native activity`.Does not support pointer events
2. ViewPreImeInputStage
 Delivers `pre-ime` input events `to the view hierarchy`.Does not support pointer events.
3. aq:ime(ImeInputStage)
Delivers input events `to the ime`.Does not support pointer events
4. EarlyPostImeInputStage
Performs early processing of post-ime input events.
5. aq:native-post-ime(NativePostImeInputStage) 
Delivers `post-ime` input events `to a native activity`
6. ViewPostImeInputStage--->`processPointerEvent`
Delivers `post-ime` input events `to the view hierarchy`
7. SyntheticInputStage
Performs synthesis of new input events from unhandled input events
```
在ViewRootImpl#setView的最后会注册事件管道,这里我们只看ViewPostImeInputStage

ViewRootImpl$ViewPostImeInputStage.java
```java
final class ViewPostImeInputStage extends InputStage {

        @Override
        protected int onProcess(QueuedInputEvent q) {
            if (q.mEvent instanceof KeyEvent) {
                return processKeyEvent(q);
            } else {
                final int source = q.mEvent.getSource();
                if ((source & InputDevice.SOURCE_CLASS_POINTER) != 0) {
                    return processPointerEvent(q);
                } else if ((source & InputDevice.SOURCE_CLASS_TRACKBALL) != 0) {
                    return processTrackballEvent(q);
                } else {
                    return processGenericMotionEvent(q);
                }
            }
        }
        ...
        private int processPointerEvent(QueuedInputEvent q) {
            final MotionEvent event = (MotionEvent)q.mEvent;

            mAttachInfo.mUnbufferedDispatchRequested = false;
            mAttachInfo.mHandlingPointerEvent = true;
            boolean handled = mView.dispatchPointerEvent(event);
            maybeUpdatePointerIcon(event);
            maybeUpdateTooltip(event);
            mAttachInfo.mHandlingPointerEvent = false;
            if (mAttachInfo.mUnbufferedDispatchRequested && !mUnbufferedInputDispatch) {
                mUnbufferedInputDispatch = true;
                if (mConsumeBatchedInputScheduled) {
                    scheduleConsumeBatchedInputImmediately();
                }
            }
            return handled ? FINISH_HANDLED : FORWARD;
        }
        ...
}
```
事件分发从View树的根节点开始(dispatchPointerEvent)，但是为了让事件也能经过Activity，根节点会先发Activity，Activity再发给Window，Window再给根节点，后面就是自顶向下发送，所以通过这样一种逻辑我们可以给根节点发送一个我们模拟的事件就能做到自动化控制页面的效果了。由于事件分发代码较多，我们这里用伪代码来简化一下。

ViewGroup.java/View.java
```java
ViewGroup.java
@Override
public boolean dispatchTouchEvent(MotionEvent ev) {
     intercepted = onInterceptTouchEvent(ev)
     if(intercepted){ 
        handled = super.dispatchTouchEvent(event);
     }
    }
    ...
    return handled;
}
View.java
public boolean dispatchTouchEvent(MotionEvent event) {
    //OnTouchListener
     if (li != null && li.mOnTouchListener != null
                    && (mViewFlags & ENABLED_MASK) == ENABLED
                    && li.mOnTouchListener.onTouch(this, event)) {
                result = true;
    }
    
    if (!result && onTouchEvent(event)) {
                result = true;
    }
    
    //在onTouchEvent方法里面执行
     performClick();
}
ViewGroup
- onInterceptTouchEvent //定义View重写该方法
- OnTouchListener#onTouch //暴露给外部使用的监听接口
- onTouchEvent //自定义View重写该方法
- OnClickListener#onClick //暴露给外部使用的监听接口

View
- OnTouchListener#onTouch //暴露给外部使用的监听接口
- onTouchEvent //自定义View重写该方法 
- OnClickListener#onClick //暴露给外部使用的监听接口
```
与叶子节点不同的是，其父节点具备拦截功能，在事件分发的过程如果子节点不希望父节点拦截事件,可以通过`requestDisallowInterceptTouchEvent`




