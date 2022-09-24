---
layout: post
title: React Native ---  初代渲染器
description: 如何渲染一个dom树的页面
date: 2022-03-20 22:50:00
share: false
comments: false
tag:
# - react native
- cross-platform
published : true 
---
* TOC
{:toc}
## *Introduction*{:.header2-font}
### 名词解释
- 渲染器renderer: React 可以自定义渲染器renderer，用于适配各个平台，浏览器、移动端、终端等。React的渲染器renderer有React DOM、React Native、Ink。
- 渲染流水线pipeline：pipeline 的原义是将计算机指令处理过程拆分为多个步骤，并通过多个硬件处理单元并行执行来加快指令执行速度。其具体执行过程类似工厂中的流水线，并因此得名。React Native 渲染器(Fabric Renderer)在多个线程之间分配渲染流水线（render pipeline）任务。
- 渲染流水线可大致分为三个阶段phase：
    - 渲染（Render）
    - 提交（Commit）
    - 挂载（Mount）
- 线程模型：渲染流水线的各个阶段可能发生在不同的线程，大多数渲染流水线发生在javascript线程与后台线程，当UI线程上有高优先级事件，渲染器能够在 UI 线程上同步执行所有渲染流水线。
    - UIThread
    - JSThread
    - BGThread


React Native渲染场景我们分为初次渲染与再次渲染，为了提高再次渲染的性能，使用了diff算法，通过比较前后两次的virtual dom，计算出差异项然后局部更新, 接下来我们先来分析初次渲染。

### *1.自定义native ui component*{:.header3-font}
先来点代码示例看看如何定义并且使用native ui component

native ui componetn 声明
```java
// view
internal class MyImageView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyleAttr: Int = -1
) : androidx.appcompat.widget.AppCompatImageView(
    context, attrs, defStyleAttr
) {
    init {
        Log.d("cjf","MyImageView init")
    }
    fun setSource(sources: ReadableArray?) {
        Log.d("cjf","source:"+sources)
    }
    fun setBorderRadius(borderRadius: Float) {
        Log.d("cjf","setBorderRadius:"+borderRadius)

    }
    fun setScaleType(toScaleType: ScalingUtils.ScaleType?) {}
    fun onReceiveNativeEvent() {
        val event = Arguments.createMap()
        event.putString("message", "MyMessage")
        val reactContext = context as ReactContext
        reactContext.getJSModule(RCTEventEmitter::class.java).receiveEvent(id, "topChange", event)
    }
}
//view manager
public class MyImageViewManager extends SimpleViewManager<MyImageView> {

   ReactApplicationContext mCallerContext;

   public MyImageViewManager(ReactApplicationContext reactContext) {
      mCallerContext = reactContext;
   }

   @Override
   public String getName() {
      return "MyImageView";
   }

   @Override
   public MyImageView createViewInstance(ThemedReactContext context) {
      return new MyImageView(context);
   }


   @ReactProp(name = "src")
   public void setSrc(MyImageView view, @Nullable ReadableArray sources) {
      view.setSource(sources);
   }

   @ReactProp(name = "borderRadius", defaultFloat = 0f)
   public void setBorderRadius(MyImageView view, float borderRadius) {
      view.setBorderRadius(borderRadius);
   }

   @ReactProp(name = ViewProps.RESIZE_MODE)
   public void setResizeMode(MyImageView view, @Nullable String resizeMode) {
      view.setScaleType(ImageResizeMode.toScaleType(resizeMode));
   }

   @Override
   public Map getExportedCustomBubblingEventTypeConstants() {
      //java层的topChange 与 js层的onChange进行映射
      return MapBuilder.builder().put(
              "topChange",
              MapBuilder.of(
                      "phasedRegistrationNames",
                      MapBuilder.of("bubbled", "onChange")
              )
      ).build();
   }

}

//包
public class MyAppPackage implements ReactPackage {

    @Override
    public List<NativeModule> createNativeModules(ReactApplicationContext reactContext) {
        List<NativeModule> modules = new ArrayList<>();
        modules.add(new CalendarModule(reactContext));
        return modules;
    }

    @Override
    public List<ViewManager> createViewManagers(ReactApplicationContext reactContext) {
        return Arrays.asList(new MyImageViewManager(reactContext));
    }
}
```

myview.js文件
```javascript
import { NativeModules, Button, requireNativeComponent } from "react-native";
import React from "react";
class MyCustomView extends React.Component {
  constructor(props) {
    super(props);
    this._onChange = this._onChange.bind(this);
  }
  _onChange(event) {
    if (!this.props.onChangeMessage) {
      return;
    }
    this.props.onChangeMessage(event.nativeEvent.message);
  }
  render() {
    const MyImageView = requireNativeComponent("MyImageView");
    return <MyImageView {...this.props} onChange={this._onChange} />;
  }
}
module.exports = MyCustomView;
```

app.js文件
```javascript
import MyCustomView from './myviews';

export default function App() {
  return (
    <View style={styles.container}>
      <Text>Open up App.js to start working on your app!</Text>
      <StatusBar style="auto" />
      <MyCustomView></MyCustomView>
    </View>
  );
}
```

在myview.js文件中通过requireNativeComponent函数懒加载HostComponent(native ui component).

requireNativeComponent.js
```typescript
const requireNativeComponent = <T>(uiViewClassName: string): HostComponent<T> =>
  ((createReactNativeComponentClass(uiViewClassName, () =>
    getNativeComponentAttributes(uiViewClassName),
  ): any): HostComponent<T>);
```
调用requireNativeComponent函数时会将组件名为key，获取组件属性的闭包存储在viewConfigCallbacks结构中。当进行页面的渲染时，

  

### *2.react应用页面初次渲染*{:.header3-font}
之前在react应用启动流程篇章里面，最后我们讲到调用ReactNativeRenderer-prod.js中render函数进行组件的渲染时，会先创建ReactRootView对应的根节点FiberRootNode，接下就updateContainer开始渲染各个组件。
```typescript
//element：PerformanceLoggerContext.Provider 树  ，container：FiberRootNode
function updateContainer(element, container, parentComponent, callback) {
  var current = container.current,
    eventTime = requestEventTime(),
    lane = requestUpdateLane(current);
  a: if (parentComponent) {
      ...
  } else parentComponent = emptyContextObject;
  //FiberRootNode的context为null
  null === container.context
    ? (container.context = parentComponent)
    : (container.pendingContext = parentComponent);
  container = createUpdate(eventTime, lane);
  container.payload = { element: element };
  callback = void 0 === callback ? null : callback;
  null !== callback && (container.callback = callback);
  enqueueUpdate(current, container);
  element = scheduleUpdateOnFiber(current, lane, eventTime);
  null !== element && entangleTransitions(element, current, lane);
  return lane;
}
```
workInProgress的tag为5或者6时调用`ReactNativePrivateInterface.UIManager.createView`创建组件

UIManager.js
```typescript
//UIManagerJSInterface 接口声明
export interface UIManagerJSInterface extends Spec {
  +getViewManagerConfig: (viewManagerName: string) => Object;
  +hasViewManagerConfig: (viewManagerName: string) => boolean;
  +createView: (
    reactTag: ?number,
    viewName: string,
    rootTag: RootTag,
    props: Object,
  ) => void;
  +updateView: (reactTag: number, viewName: string, props: Object) => void;
  +manageChildren: (
    containerTag: ?number,
    moveFromIndices: Array<number>,
    moveToIndices: Array<number>,
    addChildReactTags: Array<number>,
    addAtIndices: Array<number>,
    removeAtIndices: Array<number>,
  ) => void;
}
//BridgelessUIManager文件或者PaperUIManager文件为UIManagerJSInterface 接口实现
const UIManager: UIManagerJSInterface =
  global.RN$Bridgeless === true
    ? require('./BridgelessUIManager')//log打印
    : require('./PaperUIManager');//真正的实现

module.exports = UIManager;
```

NativeUIManager.js
```typescript
export interface Spec extends TurboModule {
    +createView: (
    reactTag: ?number,
    viewName: string,
    rootTag: RootTag,
    props: Object,
  ) => void;
}
// 通过global.__turboModuleProxy获取名为UIManager的模块
export default (TurboModuleRegistry.getEnforcing<Spec>('UIManager'): Spec);
```
js侧与java侧的接口调用主要采用turbo，所以js侧的UIManager对应的java侧的UIManagerModule，如果不理解turbo，可以查看这一篇文章[React Native---Java和JavaScript互操作]({{site.baseurl}}/2022-03-10/react-native-java-js-interoperability)

```java
@ReactModule(name = UIManagerModule.NAME)
public class UIManagerModule extends ReactContextBaseJavaModule
    implements OnBatchCompleteListener, LifecycleEventListener, UIManager {
  ...
  @ReactMethod
  public void createView(int tag, String className, int rootViewTag, ReadableMap props) {
    if (DEBUG) {
      String message =
          "(UIManager.createView) tag: " + tag + ", class: " + className + ", props: " + props;
      FLog.d(ReactConstants.TAG, message);
      PrinterHolder.getPrinter().logMessage(ReactDebugOverlayTags.UI_MANAGER, message);
    }
    mUIImplementation.createView(tag, className, rootViewTag, props);
  }
  ...
}
```
根据设计模式为了保持java侧与js侧的接口一致性UIManagerModule只负责接口声明，实现全部交给UIImplementation。
```java
public class UIImplementation {
  protected Object uiImplementationThreadLock = new Object();
  //事件分发
  protected final EventDispatcher mEventDispatcher;
  protected final ReactApplicationContext mReactContext;
  //shadow node的注册中心，shadow树
  protected final ShadowNodeRegistry mShadowNodeRegistry = new ShadowNodeRegistry();
  //ViewManager注册中心，管理ui组件
  private final ViewManagerRegistry mViewManagers;
  //存放来自于js侧操作dom的指令
  private final UIViewOperationQueue mOperationsQueue;
  private final NativeViewHierarchyOptimizer mNativeViewHierarchyOptimizer;
  private final int[] mMeasureBuffer = new int[4];

  private long mLastCalculateLayoutTime = 0;
  protected @Nullable LayoutUpdateListener mLayoutUpdateListener;
  ...
    public void createView(int tag, String className, int rootViewTag, ReadableMap props) {
    if (!mViewOperationsEnabled) {
      return;
    }

    synchronized (uiImplementationThreadLock) {
      ReactShadowNode cssNode = createShadowNode(className);
      ReactShadowNode rootNode = mShadowNodeRegistry.getNode(rootViewTag);
      Assertions.assertNotNull(rootNode, "Root node with tag " + rootViewTag + " doesn't exist");
      cssNode.setReactTag(tag); // Thread safety needed here
      cssNode.setViewClassName(className);
      cssNode.setRootTag(rootNode.getReactTag());
      cssNode.setThemedContext(rootNode.getThemedContext());

      mShadowNodeRegistry.addNode(cssNode);

      ReactStylesDiffMap styles = null;
      if (props != null) {
        styles = new ReactStylesDiffMap(props);
        cssNode.updateProperties(styles);
      }

      handleCreateView(cssNode, rootViewTag, styles);
    }
  }

  protected void handleCreateView(
      ReactShadowNode cssNode, int rootViewTag, @Nullable ReactStylesDiffMap styles) {
    if (!cssNode.isVirtual()) {
      mNativeViewHierarchyOptimizer.handleCreateView(cssNode, cssNode.getThemedContext(), styles);
    }
  }
}
```
从UIImplementation的成员变量就能大概猜测其职能，维系一棵js侧树的shadow树来决定prop有没有发生变化，变化了就会发送操作指令create、update对真实的dom树进行更新。在createView阶段，会创建ShadowNode(LayoutShadowNode),对js侧的react dom树进行shadow。
整棵ShadowNode树的基石是yoga，关于yoga后续有空可以来讲解一下。NativeViewHierarchyOptimizer会将操作指令发送到UIViewOperationQueue，等待下一帧绘制时，读取并且处理队列中的指令，比如ViewManager#createView方法。

### *3.react应用页面再次渲染*{:.header3-font}
```java
public class UIImplementation {
  ...
  /** Invoked by React to create a new node with a given tag has its properties changed. */
  public void updateView(int tag, String className, ReadableMap props) {
    if (!mViewOperationsEnabled) {
      return;
    }

    ViewManager viewManager = mViewManagers.get(className);
    if (viewManager == null) {
      throw new IllegalViewOperationException("Got unknown view type: " + className);
    }
    ReactShadowNode cssNode = mShadowNodeRegistry.getNode(tag);
    if (cssNode == null) {
      throw new IllegalViewOperationException("Trying to update non-existent view with tag " + tag);
    }

    if (props != null) {
      ReactStylesDiffMap styles = new ReactStylesDiffMap(props);
      cssNode.updateProperties(styles);
      handleUpdateView(cssNode, className, styles);
    }
  }
  protected void handleUpdateView(
      ReactShadowNode cssNode, String className, ReactStylesDiffMap styles) {
    if (!cssNode.isVirtual()) {
      mNativeViewHierarchyOptimizer.handleUpdateView(cssNode, className, styles);
    }
  }
  ...
}
```

更新流程的调用链`UIImplementation#updateView ---> UIImplementation#handleUpdateView ---> NativeViewHierarchyOptimizer#handleUpdateView ---> UIViewOperationQueue#enqueueUpdateProperties ---> android系统绘制下一帧时 ---> UpdatePropertiesOperation#execute`。
在NativeViewHierarchyOptimizer#handleUpdateView的逻辑中通过shadow树判断要不要将更新的指令放到UIViewOperationQueue中。等到android系统开始绘制下一帧时，会从UIViewOperationQueue获取指令并且处理
```java
  private final class UpdatePropertiesOperation extends ViewOperation {

    private final ReactStylesDiffMap mProps;

    private UpdatePropertiesOperation(int tag, ReactStylesDiffMap props) {
      super(tag);
      mProps = props;
    }

    @Override
    public void execute() {
      mNativeViewHierarchyManager.updateProperties(mTag, mProps);
    }
  }
```
调用链`NativeViewHierarchyManager#updateProperties ---> ViewManager#updateProperties ---> ViewManagerPropertyUpdater#updateProps ---> FallbackViewManagerSetter#setProperty ---> ViewManagersPropertyCache.PropSetter#updateViewProp` 

实例化FallbackViewManagerSetter对象的时候，会扫描ViewManager带有ReactProp注解的方法，并保存到ViewManagersPropertyCache的map中，当在setProperty刷新每个属性时，就会调用其对应的方法进行正在ui更新。

之前我们讲过NativeViewHierarchyOptimizer#handleUpdateView会通过shadow树判断要不要更新属性，这块我们深挖一下。在UIImplementation#updateView过程中，会执行两个重要事情，一个updateProperties shadow树的节点，另外一个NativeViewHierarchyOptimizer#handleUpdateView。

shadow节点的类结构图
```
ReactShadowNode
  ReactShadowNodeImpl
    LayoutShadowNode
```
LayoutShadowNode节点也有很多被ReactProp注解标注的方法。
```java
LayoutShadowNode.java
setWidth(Dynamic)
  @ReactProp(name = ViewProps.WIDTH)
setMinWidth(Dynamic)
  @ReactProp(name = ViewProps.MIN_WIDTH)
setCollapsable(boolean)
  @ReactProp(name = "collapsable")
setMaxWidth(Dynamic)
  @ReactProp(name = ViewProps.MAX_WIDTH)
setHeight(Dynamic)
  @ReactProp(name = ViewProps.HEIGHT)
setMinHeight(Dynamic)
  @ReactProp(name = ViewProps.MIN_HEIGHT)
setMaxHeight(Dynamic)
  @ReactProp(name = ViewProps.MAX_HEIGHT)
setFlex(float)
  @ReactProp(name = ViewProps.FLEX, defaultFloat = 0f)
setFlexGrow(float)
  @ReactProp(name = ViewProps.FLEX_GROW, defaultFloat = 0f)
setFlexShrink(float)
  @ReactProp(name = ViewProps.FLEX_SHRINK, defaultFloat = 0f)
setFlexBasis(Dynamic)
  @ReactProp(name = ViewProps.FLEX_BASIS)
setAspectRatio(float)
  @ReactProp(name = ViewProps.ASPECT_RATIO, defaultFloat = YogaConstants.UNDEFINED)
setFlexDirection(String)
  @ReactProp(name = ViewProps.FLEX_DIRECTION)
setFlexWrap(String)
  @ReactProp(name = ViewProps.FLEX_WRAP)
setAlignSelf(String)
  @ReactProp(name = ViewProps.ALIGN_SELF)
setAlignItems(String)
  @ReactProp(name = ViewProps.ALIGN_ITEMS)
setAlignContent(String)
  @ReactProp(name = ViewProps.ALIGN_CONTENT)
setJustifyContent(String)
  @ReactProp(name = ViewProps.JUSTIFY_CONTENT)
setOverflow(String)
  @ReactProp(name = ViewProps.OVERFLOW)
setDisplay(String)
  @ReactProp(name = ViewProps.DISPLAY)
setPosition(String)
  @ReactProp(name = ViewProps.POSITION)
setShouldNotifyOnLayout(boolean)
  @ReactProp(name = "onLayout")
setShouldNotifyPointerEnter(boolean)
  @ReactProp(name = "onPointerEnter")
setShouldNotifyPointerLeave(boolean)
  @ReactProp(name = "onPointerLeave")
setShouldNotifyPointerMove(boolean)
  @ReactProp(name = "onPointerMove")
```
看完之后是不是会很熟悉，flexbox？ 对的。LayoutShadowNode是基于yoga，而yoga是一个实现flexbox的跨平台库。

```
react 树(virtual 树) ---> shadow 树(shadow树是react树在native的影子) ---> android view树
```

在2022年react native的团队规划中，做了一次大的技术改造，将shadow树在cpp中实现，react采用fabric，整个渲染流水线发生了较大的变动。目前代码还没有完成，等完成再来分析。除了官方的优化，shopify在渲染这块也做了大胆的尝试，抛弃了平台渲染直接用skia进行dom树渲染，项目这里[react-native-skia](https://github.com/Shopify/react-native-skia)

## *Reference*{:.header2-font}

[JS 层渲染之 diff 算法](https://juejin.cn/post/6844904197096226824)

[Native层的渲染流程](https://juejin.cn/post/6844904184542822408)

[ReactNative 知识小集(2)-渲染原理](https://zhuanlan.zhihu.com/p/32749940)

[2022 年 React Native 的全新架构更新](https://www.codetd.com/pt/article/13682554)

[The how and why on React’s usage of linked list in Fiber to walk the component’s tree](https://medium.com/react-in-depth/the-how-and-why-on-reacts-usage-of-linked-list-in-fiber-67f1014d0eb7)