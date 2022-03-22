---
layout: post
title: React Native ---  渲染机制
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

React Native渲染我们分为初次渲染与再次渲染，为了提高再次渲染的性能，使用了diff算法，通过比较前后两次的virtual dom，计算出差异项然后局部更新, 接下来我们先来分析初次渲染。

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
js侧与java侧的接口调用主要采用turbo，所以js侧的UIManager对应的java侧的UIManagerModule，如何不理解turbo，可以查看这一篇文章[React Native---Java和JavaScript通信机制]({{site.baseurl}}/2022-03-10/react-native-java-js-interoperability)

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
根据设计模式为了保持java侧与js侧的接口一致性，UIManagerModule的内部实现全全交给了UIImplementation。
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


## *Reference*{:.header2-font}

[JS 层渲染之 diff 算法](https://juejin.cn/post/6844904197096226824)

[Native层的渲染流程](https://juejin.cn/post/6844904184542822408)

[ReactNative 知识小集(2)-渲染原理](https://zhuanlan.zhihu.com/p/32749940)

[2022 年 React Native 的全新架构更新](https://www.codetd.com/pt/article/13682554)

[The how and why on React’s usage of linked list in Fiber to walk the component’s tree](https://medium.com/react-in-depth/the-how-and-why-on-reacts-usage-of-linked-list-in-fiber-67f1014d0eb7)