---
layout: post
title: Android | RecyclerView的设计
description: 缓存设计、扩展性
tag:
- android
- renderer-ui
---
* TOC
{:toc}

# UI更新

当调用`adapter.notifyXxx`方法进行UI更新时(刷新全部item,加入payload刷新部分item)，会调用内部的AdapterDataObservable通知观察者RecyclerViewDataObserver调用requestLayout或者postOnAnimation重新绘制UI。
```
- onMeasure
- onLayout
    - dispatchLayout
        - dispatchLayoutStep1(处理Adapter更新，决定哪个动画要run，保存当前View的信息,也可能predictive layout并且保存信息)
        - dispatchLayoutStep2(do actul layout, measure和layout过程)
            - onLayoutChildren
        - dispatchLayoutStep3
```

# ViewHolder缓存

对于View的种类有这么几种:
- 在屏幕内的View(on-screen):attached
- 在屏幕外的View(off-screen): 
    - scrap view(still attached,but marked for removal or reuse，当数据被移除或者viewholder失效)

ViewHolder是item的数据模型，有item中各个控件的对象、item在信息流中的位置、item的id、item的类型、item的使用状态flag等信息。其中flag标示表明了其各个状态，比如View正在执行动画、View已经被绑定。
```
FLAG_INVALID // mPosition, mItemId and mItemViewType多不可用
FLAG_BOUND //已经被绑定， mPosition, mItemId and mItemViewType多可用
FLAG_NOT_RECYCLABLE //ViewHolder不能被复用，直接走onCreateViewholder
FLAG_RETURNED_FROM_SCRAP
FLAG_IGNORE //ViewHolder的缓存机制全权交给LayouManager

FLAG_UPDATE //数据太老需要重新绑定
FLAG_REMOVED// 数据集被remove，但是在outgoing animations场景View可能还在被使用。

FLAG_TMP_DETACHED //view从parent被detach

FLAG_ADAPTER_POSITION_UNKNOWN
FLAG_ADAPTER_FULLUPDATE//Set when a addChangePayload(null) is called

FLAG_MOVED//使用动画
FLAG_APPEARED_IN_PRE_LAYOUT//Used by ItemAnimator when a ViewHolder appears in pre-layout
FLAG_BOUNCED_FROM_HIDDEN_LIST

```

ViewHolder的缓存设计与Recycler类息息相关，Recycler采用了多级缓存 scrapList(mAttachScrap or mChangedScrap)、mCacheView(size为2) 、ViewCacheExtension、RecycledViewPool(每种itemType各为5个)。RecyclerView在测绘的时候会遍历所有的子view，然后通过其ViewHolder的flag执行垃圾分类。如果viewholder有效 或者 viewholder指向数据没有被remove，就将被保存到mAttachedScrap或者mChangedScrap(对于viewholder需要update是保存在mChangedScrap)；如果viewholder失效并且其指向的数据也被remove，那么就会被保存到mCachedViews和RecycledViewPool其中一个(如果mCachedViews满了就会先移动老ViewHolder到RecycledViewPool再插入新的到mCachedViews)。

Recycler获取ViewHolder默认通过postion或者itemViewType,如果无法确定复用的ViewHolder的位置，就像信息流广告位，则可以重写itemId，通过itemId从缓存池获取ViewHolder。下面来看看获取ViewHolder的路径
```
# 预布局阶段
 1. getChangedScrapViewForPosition 从mChangedScrap缓存获取ViewHolder
 2. getScrapOrHiddenOrCachedHolderForPosition 从mAttachedScrap缓存取被mark为scrap的ViewHolder 或者 从View的LayoutParams取ViewHolder 或者 从mCachedViews缓存取
 3. getScrapOrCachedViewForId  如果Adapter有stable id,则根据stable id从mAttachedScrap缓存获取ViewHolder或者从mCachedViews缓存取
 4. 从自定义mViewCacheExtension缓存获取ViewHolder
 5. 从RecycledViewPool缓存获取ViewHolder
 6. createViewHolder 构造一个新的ViewHolder

 # 非预布局阶段
 1. getScrapOrHiddenOrCachedHolderForPosition 从mAttachedScrap缓存取被mark为scrap的ViewHolder 或者 从View的LayoutParams取ViewHolder 或者 从mCachedViews缓存取
 2. getScrapOrCachedViewForId  如果Adapter有stable id,则根据stable id从mAttachedScrap缓存获取ViewHolder或者从mCachedViews缓存取
 3. 从自定义mViewCacheExtension缓存获取ViewHolder
 4. 从RecycledViewPool缓存获取ViewHolder
 5. createViewHolder 构造一个新的ViewHolder
```

在Recycler有个共享池子RecycledViewPool保存detach itemview，detach itemview的ViewHolder通常被reset了，所以复用时需要flag为re-bound。RecycledViewPool内存有个mScrap(ScrapData类的松散列表)，相当于ListView中RecycleBin的属性mScrapViews(类型为ArrayList<View>[])，mScrap通过viewType的key查找ViewHolder对象。RecycledViewPool的作用更加强大，它可以让多个RecyclerView共享ViewHolder

<!-- # 扩展性：Adapter(适配View与数据)、LayoutManager -->

# FAQ

在信息流存在大量图片时，使用notifyDataSetChanged方法容易，出现闪屏跳动，对于相同的item可以复用ViewHolder。

步骤
```
1.setHasStableId(true)
Adapter默认使用setHasStableId(false)，所以getItemId都是返回NO_ID，导致每个item使用自己的ViewHolder，不存在共用。
2.override getItemId(int position)
```
具体的原理在于Recycler这个类
```
    public final class Recycler {
        ...
        public View getViewForPosition(Adapter adapter, int position) {
            ViewHolder holder;
            ...
                if (mAdapter.hasStableIds()) {
                    //通过外部override getItemId方法使得相同的data set可以获取相同的ViewHolder
                    final long id = adapter.getItemId(position);
                    holder = getScrapViewForId(id, type);
                } else {
                    //如果ViewHolder的postion等于Adapter的postion并且ViewHolder的itemViewType等于Adapter的itemViewType则从mAttachedScrap获取ViewHoler，这是为了使得data set和ViewHolder set两个数据集合对齐，默认采用这种方式
                    holder = getScrapViewForPosition(position, type);
                }
             
            ...
            //关于ViewHolder的缓存有两层，当mAttachedScrap不存在时，就会从mRecyclerPool获取，如果mRecyclerPool不存在，则从Adapter#createViewHolder获取.双缓存
            return holder.itemView;
            
        }
        ...
    }
    public static abstract class ViewHolder {
        public final View itemView;
        int mPosition = NO_POSITION;
        long mItemId = NO_ID;
        int mItemViewType = INVALID_TYPE;
        boolean mIsDirty = true;
        public ViewHolder(View itemView) {
            if (itemView == null) {
                throw new IllegalArgumentException("itemView may not be null");
            }
            this.itemView = itemView;
        }
        public final int getPosition() {
            return mPosition;
        }
        public final long getItemId() {
            return mItemId;
        }
        public final int getItemViewType() {
            return mItemViewType;
        }
    }
```

# 参考资料
[How to Avoid That RecyclerView’s Views are Blinking when notifyDataSetChanged()](https://medium.com/@hanru.yeh/recyclerviews-views-are-blinking-when-notifydatasetchanged-c7b76d5149a2)
