---
layout: post
title: Android | ListView的设计
description: ListView设计
tag:
- android
- renderer-ui
---

# Model
# 1.数据可观察设计

```
观察者
    class AdapterDataSetObserver extends AdapterView<ListAdapter>.AdapterDataSetObserver {
        @Override
        public void onChanged() {
            super.onChanged();
            if (mFastScroll != null) {
                mFastScroll.onSectionsChanged();
            }
        }

        @Override
        public void onInvalidated() {
            super.onInvalidated();
            if (mFastScroll != null) {
                mFastScroll.onSectionsChanged();
            }
        }
    }
```
当外部调用notifyDataSetChanged就会通知观察者调用onChanged，给外部提供的是全局刷新，显然这里的处理不如RecyclerView，即提供全局刷新也提供局部刷新，所以性能效率都很差。
# 2.数据可复用设计(cache view)

## RecycleBin
- 在屏幕内的View(on-screen): mActiveViews
- 在屏幕外的View(off-screen)：mScrapViews
- 内存双缓存：mActiveViews,mScrapViews（RecycledViewPool的祖先）
```
View[] mActiveViews = new View[0];
ArrayList<View>[] mScrapViews;//viewtype决定了其数量，相当于RecyclerView&RecyclerViewPool的成员变量SparseArray<ScrapData> mScrap = new SparseArray<>();
ArrayList<View> mCurrentScrap;//mScrapViews数组的index==0的元素
//setHasTransientState(true)防止在执行动画是被回收，标识其transient state。
SparseArray<View> mTransientStateViews; //key为position
LongSparseArray<View> mTransientStateViewsById;//key为getItemId

setViewTypeCount //viewtype的数量决定了mScrapViews的size。
markChildrenDirty //标脏，所以子类会重新layout
clear //清理缓存view并且移除已经detach的view

fillActiveViews
getActiveView
addScrapView
getScrapView
scrapActiveViews //move active views to scarp heap

fullyDetachScrapViews //scrapview全部从view树remove
removeDetachedView //从view树remove某个view
```
## 获取View的缓存机制
- mRecycler.getTransientStateView(position)
- mRecycler.getScrapView(position)

# View层

布局的方式：
```
    static final int LAYOUT_NORMAL = 0;//来自于系统unsolicited的layout（requestLayout）
    static final int LAYOUT_FORCE_TOP = 1;//从顶部向下刷新
    static final int LAYOUT_FORCE_BOTTOM = 3;//从底部向上刷新
    static final int LAYOUT_SYNC = 5;//数据集发生变化，需要同步到ui
    /**
     * Make a mSelectedItem appear in a specific location and build the rest of
     * the views from there. The top is specified by mSpecificTop.
     
     setSelectionFromTop/setSelection
     */
    static final int LAYOUT_SPECIFIC = 4;
    
    
    /**
     * Force the selected item to be on somewhere on the screen
     */
    static final int LAYOUT_SET_SELECTION = 2;

    /**
     * Layout as a result of using the navigation keys
     */
    static final int LAYOUT_MOVE_SELECTION = 6;
```

Some Methods of ListView fill into itemView
```
- fillUp //从指定的position和nextBottom开始，向上fill
- fillDown //从指定的position和nextTop开始，向下fill
```

```
- fillFromSelection // Fills the grid based on positioning the new selection at a specific location. The selection may be moved so that it does not intersect the faded edges. The grid is then filled upwards and downwards from there.
- fillFromTop //从顶部开始，自上而下到某个item
- fillFromMiddle //从中间开始，向四周扩散。

//相似，都是positioin插入，然后向四周扩散。
- fillAboveAndBelow // Once the selected view as been placed, fill up the visible area above and below it
- fillSpecific //Put a specific item at a specific location on the screen and then build up and down from there
//相似

- fillGap//滚动时调用该方法fill into itemView，向上滚动就fill down itemView，向下滚动就fill up itemView
```

header 1 | layout mode
---|---
fillFromSelection/fillFromMiddle | LAYOUT_SET_SELECTION
fillSpecific(指定mSyncPosition的位置开始) | LAYOUT_SYNC
fillUp(指定某个itemView位置，从下到上填充) |LAYOUT_FORCE_BOTTOM
fillFromTop(mFirstPosition位置为屏幕上第一个可见itemView，从上到下填充所有itemView) |LAYOUT_FORCE_TOP
fillSpecific(指定selectedPosition位置开始)|LAYOUT_SPECIFIC
moveSelection|LAYOUT_MOVE_SELECTION

deltaY < 0 表示手势上滑(moving up)，内容向下填充(fill down)

向上滚动（手势上滑，内容向上填充）：fillGap--->fillDown(position为底部位置值，在底部的位置填充一个itemView)--->fillSpecific(顶部itemVIew从-1开始fillUp，fillDown 从1开始)

deltaY > 0 表示手势下拉(moving down)，内容向上填充（fill up）

向下滚动（手势下拉，内容向下填充）：fillGap--->fillUp(position为顶部位置值，在顶部的位置填充一个itemView)

# 1.执行滚动(data changed = false, onInterceptTouchEvent/onTouchEvent)
```
    static final int TOUCH_MODE_REST = -1;//初始位置
 
    static final int TOUCH_MODE_DOWN = 0;//标明有touch 事件，可能是tap也可能是scroll
    static final int TOUCH_MODE_DONE_WAITING = 2;
    
    static final int TOUCH_MODE_TAP = 1;//敲击屏幕
    static final int TOUCH_MODE_SCROLL = 3;//滚动手势
    static final int TOUCH_MODE_FLING = 4;//fling手势
    static final int TOUCH_MODE_OVERSCROLL = 5;//滚动越界了
    static final int TOUCH_MODE_OVERFLING = 6;//fling越界了，并且讲会回弹(spring back)
```
当用户touch屏幕之后，可能会发生这些操作：滚动、越界滚动、fling、越界fling。
对于越界的操作通常会有回弹的效果，对于滚动和fling本质是其实差不多，都是是内容发生了偏移，所以取其基本操作(滚动)来具体分析一下。

当用户手势进行move时，如果其mode为TOUCH_MODE_SCROLL，之会执行scrollIfNeeded，该方法主要介绍了三个参数，x,y为手势距离屏幕的距离，以及event。在其方法体内的代码逻辑整合了TOUCH_MODE_SCROLL和TOUCH_MODE_OVERSCROLL


## touch move:TOUCH_MODE_SCROLL/TOUCH_MODE_OVERSCROLL
```
  if (mTouchMode == TOUCH_MODE_SCROLL) {
        
            
            if (y != mLastY) {
                // We may be here after stopping a fling and continuing to scroll.
                // If so, we haven't disallowed intercepting touch events yet.
                // Make sure that we do so in case we're in a parent that can intercept.
                if ((mGroupFlags & FLAG_DISALLOW_INTERCEPT) == 0 &&
                        Math.abs(rawDeltaY) > mTouchSlop) {
                    final ViewParent parent = getParent();
                    if (parent != null) {
                        parent.requestDisallowInterceptTouchEvent(true);
                    }
                }

                final int motionIndex;
                if (mMotionPosition >= 0) {
                    motionIndex = mMotionPosition - mFirstPosition;
                } else {
                    // If we don't have a motion position that we can reliably track,
                    // pick something in the middle to make a best guess at things below.
                    motionIndex = getChildCount() / 2;
                }

                int motionViewPrevTop = 0;
                View motionView = this.getChildAt(motionIndex);
                if (motionView != null) {
                    motionViewPrevTop = motionView.getTop();
                }

                // No need to do all this work if we're not going to move anyway
                boolean atEdge = false;
                if (incrementalDeltaY != 0) {
                    atEdge = trackMotionScroll(deltaY, incrementalDeltaY);
                }

                // Check to see if we have bumped into the scroll limit
                motionView = this.getChildAt(motionIndex);
                if (motionView != null) {
                    // Check if the top of the motion view is where it is
                    // supposed to be
                    final int motionViewRealTop = motionView.getTop();
                    if (atEdge) {
                        // Apply overscroll

                        int overscroll = -incrementalDeltaY -
                                (motionViewRealTop - motionViewPrevTop);
                        if (dispatchNestedScroll(0, overscroll - incrementalDeltaY, 0, overscroll,
                                mScrollOffset)) {
                            lastYCorrection -= mScrollOffset[1];
                            if (vtev != null) {
                                vtev.offsetLocation(0, mScrollOffset[1]);
                                mNestedYOffset += mScrollOffset[1];
                            }
                        } else {
                            final boolean atOverscrollEdge = overScrollBy(0, overscroll,
                                    0, mScrollY, 0, 0, 0, mOverscrollDistance, true);

                            if (atOverscrollEdge && mVelocityTracker != null) {
                                // Don't allow overfling if we're at the edge
                                mVelocityTracker.clear();
                            }

                            final int overscrollMode = getOverScrollMode();
                            if (overscrollMode == OVER_SCROLL_ALWAYS ||
                                    (overscrollMode == OVER_SCROLL_IF_CONTENT_SCROLLS &&
                                            !contentFits())) {
                                if (!atOverscrollEdge) {
                                    mDirection = 0; // Reset when entering overscroll.
                                    mTouchMode = TOUCH_MODE_OVERSCROLL;
                                }
                                if (incrementalDeltaY > 0) {
                                    mEdgeGlowTop.onPull((float) -overscroll / getHeight(),
                                            (float) x / getWidth());
                                    if (!mEdgeGlowBottom.isFinished()) {
                                        mEdgeGlowBottom.onRelease();
                                    }
                                    invalidateTopGlow();
                                } else if (incrementalDeltaY < 0) {
                                    mEdgeGlowBottom.onPull((float) overscroll / getHeight(),
                                            1.f - (float) x / getWidth());
                                    if (!mEdgeGlowTop.isFinished()) {
                                        mEdgeGlowTop.onRelease();
                                    }
                                    invalidateBottomGlow();
                                }
                            }
                        }
                    }
                    mMotionY = y + lastYCorrection + scrollOffsetCorrection;
                }
                mLastY = y + lastYCorrection + scrollOffsetCorrection;
            }
        }
```

1. trackMotionScroll：滚动内容
2. overScrollBy：越界处理，将mode改为TOUCH_MODE_OVERSCROLL


## trackMotionScroll
1. 回收View到mCurrentScrap或者mScrapViews
2. 从指定的index开始detach 指定的count
3. 通过offsetChildrenTopAndBottom滚动内容
4. 之后调用fillGap填充即将出现的itemView
5. 之后remove detached的itemView，但是itemView仍然在缓冲池中。

## touch up: TOUCH_MODE_SCROLL/TOUCH_MODE_OVERSCROLL
当手离开屏幕，mode依然为TOUCH_MODE_SCROLL时，则将会继续滑行一段
```
mFlingRunnable.start(-initialVelocity)
```
紧接着如果mode转变成立TOUCH_MODE_OVERSCROLL，则会出现反弹的效果
```
            if (Math.abs(initialVelocity) > mMinimumVelocity) {
                mFlingRunnable.startOverfling(-initialVelocity);
            } else {
                mFlingRunnable.startSpringback();
            }
```
TOUCH_MODE_FLING/TOUCH_MODE_OVERFLING


# 2.执行刷新(data changed = true,onMeasure/onLayout)

## onChanged
当有新数据来时，就会通知观察者回调onChanged
```
   class AdapterDataSetObserver extends DataSetObserver {

        private Parcelable mInstanceState = null;

        @Override
        public void onChanged() {
            mDataChanged = true;
            mOldItemCount = mItemCount;
            mItemCount = getAdapter().getCount();

            // Detect the case where a cursor that was previously invalidated has
            // been repopulated with new data.
            if (AdapterView.this.getAdapter().hasStableIds() && mInstanceState != null
                    && mOldItemCount == 0 && mItemCount > 0) {
                AdapterView.this.onRestoreInstanceState(mInstanceState);
                mInstanceState = null;
            } else {
                rememberSyncState();
            }
            checkFocus();
            requestLayout();
        }

        @Override
        public void onInvalidated() {
            mDataChanged = true;

            if (AdapterView.this.getAdapter().hasStableIds()) {
                // Remember the current state for the case where our hosting activity is being
                // stopped and later restarted
                mInstanceState = AdapterView.this.onSaveInstanceState();
            }

            // Data is invalid so we should reset our state
            mOldItemCount = mItemCount;
            mItemCount = 0;
            mSelectedPosition = INVALID_POSITION;
            mSelectedRowId = INVALID_ROW_ID;
            mNextSelectedPosition = INVALID_POSITION;
            mNextSelectedRowId = INVALID_ROW_ID;
            mNeedSync = false;

            checkFocus();
            requestLayout();
        }

        public void clearSavedState() {
            mInstanceState = null;
        }
    }
```
1.记录状态(rememberSyncState)

在rememberSyncState主要是设置listview同步的方式：SYNC_FIRST_POSITION、SYNC_SELECTED_POSITION。如果之前set过mSelectedPosition，那么listview就会从mSelectedPosition开始向四周刷新itemview;如果没有则会从mFirstPosition开始向下填充。

2. 刷新ui(requestLayout)

我们都知道当requestLayout时会调用onMeasure/onLayout，当数据集发生变化onMeasure里面只是做了一些简单的判断，真正重要的是在onLayout阶段。在onLayout阶段通过都是让子类实现layoutChildren方法，从而实现不同的布局：list、grid。那么就来看看ListView如何重写了layoutChildren方法，从而显示线性信息流布局的。

layoutChildren主要做了这么几步。

1.数据发生变化时调用handleDataChanged，设置layout mode

header 1 | header 2
---|---
TRANSCRIPT_MODE_ALWAYS_SCROLL(数据有更新就会自动滑到底部) | LAYOUT_FORCE_BOTTOM
TRANSCRIPT_MODE_NORMAL(最后一个itemView可见并且数据有更新，就会滑到底部) | LAYOUT_FORCE_BOTTOM
SYNC_SELECTED_POSITION | LAYOUT_SYNC or LAYOUT_SET_SELECTION
SYNC_FIRST_POSITION | LAYOUT_SYNC

2.layout mode为LAYOUT_SYNC时，调用fillSpecific同步数据


# 滚动

fling:手指离开(up)屏幕的速度大于系统给的(getScaledMinimumFlingVelocity、getScaledMaximumFlingVelocity),会继续滑行一段路程
- TOUCH_MODE_SCROLL
- TOUCH_MODE_FLING
- TOUCH_MODE_OVERFLING

scroll：在move的速度大于系统（getScaledTouchSlop）给的，会滚动内容


- smoothScrollBy（endFling、startScroll）
- fling（start）
- onTouchUp（start、endFling、startOverfling、startSpringback）
- onTouchDown（endFling、flywheelTouch）
- onTouchCancel（startSpringback）


OverScroller Scroller PositionScroller

onOverScrolled/overScrollBy


在手势类GestureDetector中定义了scroll、fling、single tap up、 double tap、long press，而在ListView中定义了scroll 、 over scroll、fling、over fling、tap