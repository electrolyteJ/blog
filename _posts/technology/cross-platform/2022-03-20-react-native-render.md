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
    ? require('./BridgelessUIManager')
    : require('./PaperUIManager');

module.exports = UIManager;
```

### *3.react应用页面再次渲染*{:.header3-font}

## *Reference*{:.header2-font}

[JS 层渲染之 diff 算法](https://juejin.cn/post/6844904197096226824)

[Native层的渲染流程](https://juejin.cn/post/6844904184542822408)

[ReactNative 知识小集(2)-渲染原理](https://zhuanlan.zhihu.com/p/32749940)