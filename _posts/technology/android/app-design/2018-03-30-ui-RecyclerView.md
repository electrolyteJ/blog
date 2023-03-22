---
layout: post
title: RecylerView
description: 
author: 电解质
tag:
- android
---


## Usage
对于RecyclerView的使用我们已经习以为常，就像这样子。
```
public class MyActivity extends Activity {
    private RecyclerView mRecyclerView;
    private RecyclerView.Adapter mAdapter;
    private RecyclerView.LayoutManager mLayoutManager;
 
    @Override 
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.my_activity);
        mRecyclerView = (RecyclerView) findViewById(R.id.my_recycler_view);
 
        // use this setting to improve performance if you know that changes 
        // in content do not change the layout size of the RecyclerView 
        mRecyclerView.setHasFixedSize(true);
 
        // use a linear layout manager 
        mLayoutManager = new LinearLayoutManager(this);
        mRecyclerView.setLayoutManager(mLayoutManager);
 
        // specify an adapter (see also next example) 
        mAdapter = new MyAdapter(myDataset);
        mRecyclerView.setAdapter(mAdapter);
    } 
    // ... 
}

public class MyAdapter extends RecyclerView.Adapter<MyAdapter.MyViewHolder> { 
    private String[] mDataset;
 
    // Provide a reference to the views for each data item 
    // Complex data items may need more than one view per item, and 
    // you provide access to all the views for a data item in a view holder 
    public static class MyViewHolder extends RecyclerView.ViewHolder { 
        // each data item is just a string in this case 
        public TextView mTextView;
        public MyViewHolder(TextView v) {
            super(v);
            mTextView = v;
        } 
    } 
 
    // Provide a suitable constructor (depends on the kind of dataset) 
    public MyAdapter(String[] myDataset) {
        mDataset = myDataset;
    } 
 
    // Create new views (invoked by the layout manager) 
    @Override 
    public MyAdapter.MyViewHolder onCreateViewHolder(ViewGroup parent,
                                                   int viewType) {
        // create a new view 
        TextView v = (TextView) LayoutInflater.from(parent.getContext())
                .inflate(R.layout.my_text_view, parent, false);
        ... 
        MyViewHolder vh = new MyViewHolder(v);
        return vh;
    } 
 
    // Replace the contents of a view (invoked by the layout manager) 
    @Override 
    public void onBindViewHolder(MyViewHolder holder, int position) {
        // - get element from your dataset at this position 
        // - replace the contents of the view with that element 
        holder.mTextView.setText(mDataset[position]);
 
    } 
 
    // Return the size of your dataset (invoked by the layout manager) 
    @Override 
    public int getItemCount() { 
        return mDataset.length;
    } 
} 

```
对于外部使用者可以通过override LayoutManager改变item之间的布局方式，通过Adapter可以将从后端get到的数据，adapter为View显示的数据。我们试着这样想一件事，如果信息流界面不存在滑动，那么就不需要做数据的recycle，但是往往信息流是需要滑动的，所以为了保证内存的合理利用和数据被快速使用必然需要用到缓存，已经对于缓存的处理。了解这几点，我们再来看看RecyclerView的设计。


## Model层
首先我们来研究Adapter的设计和数据缓存的设计。
```
public static abstract class Adapter {
        private final AdapterDataObservable mObservable = new AdapterDataObservable();
        private boolean mHasStableIds = false;
        private int mViewTypeCount = 1;
        public abstract ViewHolder createViewHolder(ViewGroup parent, int viewType);
        public abstract void bindViewHolder(ViewHolder holder, int position);
       
        public int getItemViewType(int position) {
            return 0;
        }
       
        public void setItemViewTypeCount(int count) {
            if (hasObservers()) {
                throw new IllegalStateException("Cannot change the item view type count while " +
                        "the adapter has registered observers.");
            }
            if (count < 1) {
                throw new IllegalArgumentException("Adapter must support at least 1 view type");
            }
            mViewTypeCount = count;
        }
      
        public final int getItemViewTypeCount() {
            return mViewTypeCount;
        }
        public void setHasStableIds(boolean hasStableIds) {
            if (hasObservers()) {
                throw new IllegalStateException("Cannot change whether this adapter has " +
                        "stable IDs while the adapter has registered observers.");
            }
            mHasStableIds = true;
        }
        
        public final boolean hasStableIds() {
            return mHasStableIds;
        }
       
        public void onViewRecycled(ViewHolder holder) {
        }
        public final boolean hasObservers() {
            return mObservable.hasObservers();
        }
        public void registerAdapterDataObserver(AdapterDataObserver observer) {
            mObservable.registerObserver(observer);
        }
        public void unregisterAdapterDataObserver(AdapterDataObserver observer) {
            mObservable.unregisterObserver(observer);
        }
        public void notifyDataSetChanged() {
            mObservable.notifyChanged();
        }
        public void notifyItemChanged(int position) {
            mObservable.notifyItemRangeChanged(position, 1);
        }
        public void notifyItemRangeChanged(int positionStart, int itemCount) {
            mObservable.notifyItemRangeChanged(positionStart, itemCount);
        }
        public void notifyDataItemInserted(int position) {
            mObservable.notifyItemRangeInserted(position, 1);
        }
        public void notifyDataItemRangeInserted(int positionStart, int itemCount) {
            mObservable.notifyItemRangeInserted(positionStart, itemCount);
        }
        public void notifyDataItemRemoved(int position) {
            mObservable.notifyItemRangeRemoved(position, 1);
        }
        public void notifyDataItemRangeRemoved(int positionStart, int itemCount) {
            mObservable.notifyItemRangeRemoved(positionStart, itemCount);
        }
    }
```
我们都知道Adapter子类需要实现createViewHolder、bindViewHolder、getItemCount的方法，ViewHolder的作用主要是保存item中各个view对象，这样的效果是可以缓存item中个view对象，不用每次多find view数，节省cpu计算。为了让信息流的item多元化，我们可以在Adapter子类override getItemViewType方法，为每个不同类型的item提供唯一标识。当然了还有更新数据的notifyXxx方法
- AdapterDataObservable/AdapterDataObserver(RecyclerViewDataObserver)  :被观察的对象为底层数据 registerAdapterDataObserver/unregisterAdapterDataObserver
- ViewHolder、Recycler ：cache createViewHolder/bindViewHolder/onViewRecycled
- view type  ：abundant  getItemViewType/getItemViewTypeCount/setItemViewTypeCount

### 1.数据可观察设计
```
被观察者(model层数据发生变化会通过Adapter上报)：
    static class AdapterDataObservable extends Observable<AdapterDataObserver> {
        public boolean hasObservers() {
            return !mObservers.isEmpty();
        }
        public void notifyChanged() {
            // since onChanged() is implemented by the app, it could do anything, including
            // removing itself from {@link mObservers} - and that could cause problems if
            // an iterator is used on the ArrayList {@link mObservers}.
            // to avoid such problems, just march thru the list in the reverse order.
            for (int i = mObservers.size() - 1; i >= 0; i--) {
                mObservers.get(i).onChanged();
            }
        }
        public void notifyItemRangeChanged(int positionStart, int itemCount) {
            // since onItemRangeChanged() is implemented by the app, it could do anything, including
            // removing itself from {@link mObservers} - and that could cause problems if
            // an iterator is used on the ArrayList {@link mObservers}.
            // to avoid such problems, just march thru the list in the reverse order.
            for (int i = mObservers.size() - 1; i >= 0; i--) {
                mObservers.get(i).onItemRangeChanged(positionStart, itemCount);
            }
        }
        public void notifyItemRangeInserted(int positionStart, int itemCount) {
            // since onItemRangeInserted() is implemented by the app, it could do anything,
            // including removing itself from {@link mObservers} - and that could cause problems if
            // an iterator is used on the ArrayList {@link mObservers}.
            // to avoid such problems, just march thru the list in the reverse order.
            for (int i = mObservers.size() - 1; i >= 0; i--) {
                mObservers.get(i).onItemRangeInserted(positionStart, itemCount);
            }
        }
        public void notifyItemRangeRemoved(int positionStart, int itemCount) {
            // since onItemRangeRemoved() is implemented by the app, it could do anything, including
            // removing itself from {@link mObservers} - and that could cause problems if
            // an iterator is used on the ArrayList {@link mObservers}.
            // to avoid such problems, just march thru the list in the reverse order.
            for (int i = mObservers.size() - 1; i >= 0; i--) {
                mObservers.get(i).onItemRangeRemoved(positionStart, itemCount);
            }
        }
    }
}

观察者(View得知数据有变化，进行post ui)：
    private class RecyclerViewDataObserver extends AdapterDataObserver {
        // These two fields act like a SparseLongArray for tracking nearby position-id mappings.
        // Values with the same index correspond to one another. mPositions is in ascending order.
        private int[] mPositions;
        private long[] mIds;
        private int mMappingSize;
        void initIdMapping() {
        }
        void clearIdMapping() {
            mPositions = null;
            mIds = null;
            mMappingSize = 0;
        }
        @Override
        public void onChanged() {
            if (mAdapter.hasStableIds()) {
                // TODO Determine what actually changed
            } else {
                mRecycler.onGenericDataChanged();
                markKnownViewsDirty();
                requestLayout();
            }
        }
        @Override
        public void onItemRangeChanged(int positionStart, int itemCount) {
            postAdapterUpdate(obtainUpdateOp(UpdateOp.UPDATE, positionStart, itemCount));
        }
        @Override
        public void onItemRangeInserted(int positionStart, int itemCount) {
            postAdapterUpdate(obtainUpdateOp(UpdateOp.ADD, positionStart, itemCount));
        }
        @Override
        public void onItemRangeRemoved(int positionStart, int itemCount) {
            postAdapterUpdate(obtainUpdateOp(UpdateOp.REMOVE, positionStart, itemCount));
        }
    }
```
在上报时，可以通过notifyItemChanged方法上报，刷新全部item(全局刷新)；也可以通过notifyDataItemXxx方法进行payload刷新(局部刷新)

### 2.数据可复用设计(cache ViewHolder)
如何设计一个cache？
- LRU cache
- Eviction policy,
- Cache concurrency
- Distributed cache system

#### ViewHolder
这一块主要是用来cache Viewholder，在ListView的设计中ViewHolder用来节省find  views带来cpu计算，ViewHolder的名字就和其职能一样见名知意，一个itemView对应一个ViewHolder，不存在多个相同类型的ItemView对应一个Viewholder，两者之间的关系比较简单纯粹。而在RecyclerView中ViewHolder的设计更加复杂，活得不过纯粹了。除了基本的holder views之外,还使用flag、id表示View、Adapter、Animator的一些状态和关系用来管理ViewHolder也实现多个相同类型的itemView
可以使用同一个ViewHolder。当然，如果你想一个itemView对应一个ViewHolder,使用itemId用来表示和itemView的对应，让ViewHolder不可复用。

ViewHolder的几个关键属性
```
mPosition
mItemId//如果信息流中有广告的位置，可以固定住其ViewHolder
mItemViewType //相同类型的itemView使用同种ViewHolder
```

状态
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
#### Recycler

对于View的种类有这么几种:
- 在屏幕内的View(on-screen):attached
- 在屏幕外的View(off-screen): 
    - scrap view(still attached,but marked for removal or reuse，当数据被移除或者viewholder失效)
    
四级缓存:
- scrapList(mAttachScrap or mChangedScrap)：
- mCacheView(size为2)
- ViewCacheExtension
- RecycledViewPool(每种itemType各为5个)

RecyclerView在测绘的时候会遍历所有的子view，然后通过其ViewHolder的flag执行垃圾分类。如果viewholder有效 或者 viewholder指向数据没有被remove则将被保存到mAttachedScrap和mChangedScrap中其中一个(对于viewholder需要update的是保存在mChangedScrap)；如果viewholder失效并且其指向的数据也被remove，那么就会被保存到mCachedViews和RecycledViewPool其中一个(如果mCachedViews满了就会先移动老的到RecycledViewPool在插入新的到mCachedViews)。RecyclerView每次测绘都会执行上面的逻辑，然后


Recycler类
``` 
final ArrayList<ViewHolder> mAttachedScrap = new ArrayList<>();// 滚动时的scrap heap
ArrayList<ViewHolder> mChangedScrap = null; //刷新时(data changed)的scrap heap。
final ArrayList<ViewHolder> mCachedViews = new ArrayList<ViewHolder>();
RecycledViewPool mRecyclerPool;
  
- scrapView：Mark an attached view as scrap
- getScrapViewAt
- getScrapCount
- unscrapView
- clearScrap

- addViewHolderToRecycledViewPool:Prepares the ViewHolder to be removed/recycled, and inserts it into the RecycledViewPool.
- tryGetViewHolderForPositionByDeadline
```

#### RecycledViewPool
保存detach itemview，detach itemview的ViewHolder通常被reset了，所以复用时需要re-bound

```
static class ScrapData {
    final ArrayList<ViewHolder> mScrapHeap = new ArrayList<>();
    int mMaxScrap = DEFAULT_MAX_SCRAP;
    long mCreateRunningAverageNs = 0;
    long mBindRunningAverageNs = 0;
}
SparseArray<ScrapData> mScrap = new SparseArray<>();
- putRecycledView
- getRecycledView
```
RecycledViewPool的属性mScrap相当于ListView中RecycleBin的属性mScrapViews(类型为ArrayList<View>[])，不过mScrap采用的是key-value存储数据，其中key为viewType。RecycledViewPool的作用更加强大，它可以让多个RecyclerView共享ViewHolder，从而起到节省资源高可复用的效果

#### 获取ViewHolder的缓存机制
```
 - getChangedScrapViewForPosition // 0) If there is a changed scrap, try to find from there 。取最新的缓存
 - getScrapOrHiddenOrCachedHolderForPosition // 1) Find by position from scrap/hidden list/cache。取被mark为scrap的attach缓存
 - getScrapOrCachedViewForId // 2) Find from scrap/cache via stable ids, if exists 。取stable id的缓存
 - createViewHolder //3) new ViewHolder 。构造一个缓存
```

在ViewHolder缓存设计中，系统默认获取的方式是通过postion和itemViewType,当然你也可以自定义item id比如使用product id，记得初始化ViewHolder#mItemId表示item的唯一性


## View层
- onMeasure
- onLayout
    - dispatchLayout
        - dispatchLayoutStep1(处理Adapter更新，决定那个动画要run，保存当前View的信息,也可能predictive layout并且保存信息)
        - dispatchLayoutStep2(do actul layout,measure和layout过程)
            - onLayoutChildren
        - dispatchLayoutStep3


### 1.执行动画(data changed = false)



### 2.执行刷新(data changed = true)

```
public class RecyclerView extends ViewGroup {
    ...
    public void setAdapter(Adapter adapter) {
        if (mAdapter != null) {
            adapter.unregisterAdapterDataObserver(mObserver);
        }
        mAdapter = adapter;
        if (adapter != null) {
            adapter.registerAdapterDataObserver(mObserver);
        }
        mRecycler.onAdapterChanged();
        requestLayout();
    }
    ...
}
```
当View注入了Adapter对象


### FAQ

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
[How to Avoid That RecyclerView’s Views are Blinking when notifyDataSetChanged()](https://medium.com/@hanru.yeh/recyclerviews-views-are-blinking-when-notifydatasetchanged-c7b76d5149a2)
