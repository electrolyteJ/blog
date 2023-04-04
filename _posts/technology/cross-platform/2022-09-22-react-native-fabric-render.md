---
layout: post
title: React Native |  Fabric渲染器
description: 船新渲染器
date: 2022-09-22 22:50:00
share: false
comments: false
tag:
# - react native
- cross-platform
- renderer
published : true 
---
* TOC
{:toc}

Fabric从2018年到2021年，历时4年正式启用，关于Fabric初衷和收益看[这篇文章](https://reactnative.dev/architecture/fabric-renderer), 这里我们讲几个重构的地方，在React Native的渲染流水线中存在三棵树，其中shadow树由平台各自实现的代码下沉到cpp层实现，从而使得各个平台的差异变小，除了shadow树还有布局逻辑、视图拍平算法，这些属于yoga，也就是变相的去掉了jni for yoga，直接在cpp层使用yoga。

RendererImplementation模块的renderElement函数调用React Native的渲染器开始渲染，让我们从ReactFabric模块的render函数开始讲起。
```javascript
//RendererImplementation.js
export function renderElement({
  element,
  rootTag,
  useFabric,
  useConcurrentRoot,
}: {
  element: Element<ElementType>,
  rootTag: number,
  useFabric: boolean,
  useConcurrentRoot: boolean,
}): void {
  if (useFabric) {
    require('../Renderer/shims/ReactFabric').render(
      element,
      rootTag,
      null,
      useConcurrentRoot,
    );
  } else {
    require('../Renderer/shims/ReactNative').render(element, rootTag);
  }
}
//ReactFabric.js
function render(element, containerTag, callback, concurrentRoot) {
  var root = roots.get(containerTag);

  if (!root) {
    // TODO (bvaughn): If we decide to keep the wrapper component,
    // We could create a wrapper for containerTag as well to reduce special casing.
    root = createContainer(
      containerTag,
      concurrentRoot ? ConcurrentRoot : LegacyRoot,
      null,
      false,
      null,
      "",
      onRecoverableError
    );
    roots.set(containerTag, root);
  }

  updateContainer(element, root, null, callback); // $FlowIssue Flow has hardcoded values for React DOM that don't work with RN

  return getPublicRootInstance(root);
}
```
在上面的函数中我们可以看到传统的渲染器ReactNative与新的渲染器ReactFabric走不同的分叉。fabric渲染器会将element树传给fiber。createContainer与updateContainer函数是有react-native-renderer包提供，fiber管理element树。fiber会回调HostConfig生命周期函数。
```js
const HostConfig = {
  createInstance(type, props) {
    // e.g. DOM renderer returns a DOM node
  },
  // ...
  supportsMutation: true, // it works by mutating nodes
  appendChild(parent, child) {
    // e.g. DOM renderer would call .appendChild() here
  },
  // ...
};
```

React Native团队制作了react-native-renderer npm包，其主要目的是自定义适用于移动端的react渲染器。ReactFabricHostConfig是Fabric的配置，初代渲染器的配置在ReactNativeHostConfig这个模块。
```
ReactFabricHostConfig
- appendInitialChild
- createInstance
- createTextInstance
- finalizeInitialChildren
- getRootHostContext
- getChildHostContext
- getPublicInstance
- prepareForCommit
- prepareUpdate
- resetAfterCommit
- shouldSetTextContent
- getCurrentEventPriority
- cloneInstance
- cloneHiddenInstance   
- cloneHiddenTextInstance
- createContainerChildSet
- appendChildToContainerChildSet
- finalizeContainerChildren
```

这里我们来分析一下createInstance与finalizeContainerChildren函数，其是渲染、提交两个阶段的关键函数。

除了上面提到的两个关键切入点，我们也需要知道js与cpp，cpp与java互相映射的类与接口

FabricUIManager.js
```javascript
import type {
  MeasureOnSuccessCallback,
  MeasureInWindowOnSuccessCallback,
  MeasureLayoutOnSuccessCallback,
  LayoutAnimationConfig,
} from '../Renderer/shims/ReactNativeTypes';
import type {RootTag} from 'react-native/Libraries/Types/RootTagTypes';

// TODO: type these properly.
type Node = {...};
type NodeSet = Array<Node>;
type NodeProps = {...};
type InstanceHandle = {...};
export type Spec = {|
  +createNode: (
    reactTag: number,
    viewName: string,
    rootTag: RootTag,
    props: NodeProps,
    instanceHandle: InstanceHandle,
  ) => Node,
  +cloneNode: (node: Node) => Node,
  +cloneNodeWithNewChildren: (node: Node) => Node,
  +cloneNodeWithNewProps: (node: Node, newProps: NodeProps) => Node,
  +cloneNodeWithNewChildrenAndProps: (node: Node, newProps: NodeProps) => Node,
  +createChildSet: (rootTag: RootTag) => NodeSet,
  +appendChild: (parentNode: Node, child: Node) => Node,
  +appendChildToSet: (childSet: NodeSet, child: Node) => void,
  +completeRoot: (rootTag: RootTag, childSet: NodeSet) => void,
  +measure: (node: Node, callback: MeasureOnSuccessCallback) => void,
  +measureInWindow: (
    node: Node,
    callback: MeasureInWindowOnSuccessCallback,
  ) => void,
  +measureLayout: (
    node: Node,
    relativeNode: Node,
    onFail: () => void,
    onSuccess: MeasureLayoutOnSuccessCallback,
  ) => void,
  +configureNextLayoutAnimation: (
    config: LayoutAnimationConfig,
    callback: () => void, // check what is returned here
    // This error isn't currently called anywhere, so the `error` object is really not defined
    // $FlowFixMe[unclear-type]
    errorCallback: (error: Object) => void,
  ) => void,
  +sendAccessibilityEvent: (node: Node, eventType: string) => void,
|};

const FabricUIManager: ?Spec = global.nativeFabricUIManager;

module.exports = FabricUIManager;
```

React应用初始化的时候，hybrid Binding#installFabricUIManager会将cpp层的FabricMountingManager与java侧的FabricUIManager绑定，也会将cpp层的UIManager与js侧的FabricUIManager绑定(通过 UIManagerBinding#createAndInstallIfNeeded进行绑定)。前者管理Android平台的View树，后者管理的是介于React元素树与View树之间的Shadow树。


## *自定义fabric ui component*
自定义fabric ui component自定义配置文件较多就不放出了，可以查看React Native官网核心设计的Fabric 组件章节，也可以查看我写的github 项目demo，使用的expo框架，代码有些地方与React Native有差异，但是一些核心的类配置相同,项目名[spacecraft-plan/spacecraft-rn][1]

## *react应用页面初次渲染*

<!-- ### *页面初始化*

```java
//ReactInstanceManager
    if (reactRoot.getUIManagerType() == FABRIC) {
      rootTag =
          uiManager.startSurface(
              reactRoot.getRootViewGroup(),
              reactRoot.getJSModuleName(),
              initialProperties == null
                  ? new WritableNativeMap()
                  : Arguments.fromBundle(initialProperties),
              reactRoot.getWidthMeasureSpec(),
              reactRoot.getHeightMeasureSpec());
      reactRoot.setShouldLogContentAppeared(true);
    } else {
      rootTag =
          uiManager.addRootView(
              reactRoot.getRootViewGroup(),
              initialProperties == null
                  ? new WritableNativeMap()
                  : Arguments.fromBundle(initialProperties),
              reactRoot.getInitialUITemplate());
      reactRoot.setRootViewTag(rootTag);
      reactRoot.runApplication();
    }
``` -->

### *渲染阶段*
渲染阶段会创建shadow节点，通过调用UIManagerBinding原生接口createNode,UIManagerBinding主要用来绑定js侧的FabricUIManager与cpp层的UIManager，所以紧接着就调用了UIManager的createNode函数。

```cpp
//UIManager
ShadowNode::Shared UIManager::createNode(
    Tag tag,
    std::string const &name,
    SurfaceId surfaceId,
    const RawProps &rawProps,
    SharedEventTarget eventTarget) const {
  ...
  auto &componentDescriptor = componentDescriptorRegistry_->at(name);
  auto fallbackDescriptor =
      componentDescriptorRegistry_->getFallbackComponentDescriptor();

  PropsParserContext propsParserContext{surfaceId, *contextContainer_.get()};

  auto const fragment = ShadowNodeFamilyFragment{tag, surfaceId, nullptr};
  auto family =
      componentDescriptor.createFamily(fragment, std::move(eventTarget));
  auto const props =
      componentDescriptor.cloneProps(propsParserContext, nullptr, rawProps);
  auto const state =
      componentDescriptor.createInitialState(ShadowNodeFragment{props}, family);

  auto shadowNode = componentDescriptor.createShadowNode(
      ShadowNodeFragment{
          /* .props = */
          fallbackDescriptor != nullptr &&
                  fallbackDescriptor->getComponentHandle() ==
                      componentDescriptor.getComponentHandle()
              ? componentDescriptor.cloneProps(
                    propsParserContext,
                    props,
                    RawProps(folly::dynamic::object("name", name)))
              : props,
          /* .children = */ ShadowNodeFragment::childrenPlaceholder(),
          /* .state = */ state,
      },
      family);

  if (delegate_ != nullptr) {
    delegate_->uiManagerDidCreateShadowNode(*shadowNode);
  }
  if (leakChecker_) {
    leakChecker_->uiManagerDidCreateShadowNodeFamily(family);
  }

  return shadowNode;
}
```
componentDescriptor对象是shadow node的工厂，提供构造shadow node的函数，在应用启动加载so时会将各个组件的ComponentDescriptor注册到ComponentDescriptorRegistry注册中心。创建完shadow node之后经过调用链`Scheduler#uiManagerDidCreateShadowNode-->Binding#schedulerDidRequestPreliminaryViewAllocation-->Binding#preallocateView-->FabricMountingManager#preallocateShadowView-->FabricUIManager#preallocateView-->MountItemDispatcher#addPreAllocateMountItem`最后会将rootTag(surfaceId)、reactTag、componentName、props、stateWrapper等参数构建PreAllocateViewMountItem并传给mPreMountItems队列，等到下一帧到来时再从队列取出数据进行处理，这块属于挂载阶段后面再剖开讲。

### *提交阶段*
渲染阶段负责创建shadow node并没有计算shadow node的布局尺寸，计算布局尺寸这块放在了提交阶段，js侧调用completeRoot原生接口触发了提交阶段的开始。

```cpp
//UIManager
void UIManager::completeSurface(
    SurfaceId surfaceId,
    ShadowNode::UnsharedListOfShared const &rootChildren,
    ShadowTree::CommitOptions commitOptions) const {
  SystraceSection s("UIManager::completeSurface");

  shadowTreeRegistry_.visit(surfaceId, [&](ShadowTree const &shadowTree) {
    shadowTree.commit(
        [&](RootShadowNode const &oldRootShadowNode) {
          return std::make_shared<RootShadowNode>(
              oldRootShadowNode,
              ShadowNodeFragment{
                  /* .props = */ ShadowNodeFragment::propsPlaceholder(),
                  /* .children = */ rootChildren,
              });
        },
        commitOptions);
  });
}
//ShadowTree
CommitStatus ShadowTree::commit(
    const ShadowTreeCommitTransaction &transaction,
    const CommitOptions &commitOptions) const {
  SystraceSection s("ShadowTree::commit");

  int attempts = 0;

  while (true) {
    attempts++;

    auto status = tryCommit(transaction, commitOptions);
    if (status != CommitStatus::Failed) {
      return status;
    }

    // After multiple attempts, we failed to commit the transaction.
    // Something internally went terribly wrong.
    react_native_assert(attempts < 1024);
  }
}
```
UIManagerBinding接收到js层的completeRoot函数调用后会在fabric_bg线程调用UIManager#completeSurface函数来完成异步布局。在页面初始化的时候会将RootView与其shadow node push到shadowTreeRegistry_注册中心,所以shadowTreeRegistry_调用visit函数主要是为了获取RootView的shadowTree，然后将新的shdow树提交到RootView的shadowTree。commit函数继续调用tryCommit函数，tryCommit主要有这么几步重要处理。

- RootShadowNode#layoutIfNeeded：计算布局的尺寸，主要依赖于yoga
- ShadowTree#emitLayoutEvents：将计算完的布局尺寸发送到js侧
- ShadowTree#mount: 调用链`UIManager#shadowTreeDidFinishTransaction-->Scheduler#uiManagerDidFinishTransaction-->Binding#schedulerDidFinishTransaction-->FabricUIManager#scheduleMountItem` ， 最后调到java侧的FabricUImanager将IntBufferBatchMountItem对象(参数rootTag, intBuffer, objBuffer, commitNumbe)push到mMountItems队列。IntBufferBatchMountItem被处理的前提是PreAllocateViewMountItem先被处理创建出ViewState,IntBufferBatchMountItem才能将计算后的布局尺寸传给ViewState.mView进行原生平台的测绘流程。

### *挂载阶段*

下一帧到来之后会依次处理PERF_MARKERS、DISPATCH_UI、NATIVE_ANIMATED_MODULE、TIMERS_EVENTS、IDLE_EVENT。

```java
  public enum CallbackType {
    //暂无
    /** For use by perf markers that need to happen immediately after draw */
    PERF_MARKERS(0),

    //FabricUIManager$mDispatchUIFrameCallback
    /** For use by {@link com.facebook.react.uimanager.UIManagerModule} */
    DISPATCH_UI(1),

    //NativeAnimatedModule#mAnimatedFrameCallback
    /** For use by {@link com.facebook.react.animated.NativeAnimatedModule} */
    NATIVE_ANIMATED_MODULE(2),

    //EventDispatcherImpl#mCurrentFrameCallback
    /** Events that make JS do things. */
    TIMERS_EVENTS(3),

    //SurfaceMountingManager#mRemoveDeleteTreeUIFrameCallback
    /**
     * Event used to trigger the idle callback. Called after all UI work has been dispatched to JS.
     */
    IDLE_EVENT(4),
    ;
  }
```

我们抓重点来看DISPATCH_UI的回调mDispatchUIFrameCallback。

```java
 private class DispatchUIFrameCallback extends GuardedFrameCallback {

    private volatile boolean mIsMountingEnabled = true;

    private DispatchUIFrameCallback(@NonNull ReactContext reactContext) {
      super(reactContext);
    }

    @AnyThread
    void stop() {
      mIsMountingEnabled = false;
    }

    @Override
    @UiThread
    @ThreadConfined(UI)
    public void doFrameGuarded(long frameTimeNanos) {
      ...
      try {
        mMountItemDispatcher.dispatchPreMountItems(frameTimeNanos);
        mMountItemDispatcher.tryDispatchMountItems();
      } catch (Exception ex) {
        ...
      } finally {
        ReactChoreographer.getInstance()
            .postFrameCallback(
                ReactChoreographer.CallbackType.DISPATCH_UI, mDispatchUIFrameCallback);
      }
    }
  }
```
- dispatchPreMountItems:for each mPreMountItems内部的PreAllocateViewMountItem对象，然后excute PreAllocateViewMountItem对象，最后会调用createViewUnsafe创建View并且保存到mTagToViewState
- tryDispatchMountItems：先处理mViewCommandMountItems队列(js view调用native命令) 再处理mMountItems队列(yogo计算后的布局尺寸传给原生平台测绘)


EventQueue
```
--> EventQueue#enqueueEvent(enqueueUniqueEvent)
--> BatchedEventQueue#onEnqueue
--> AsyncEventBeat#request
--> FabricUIManager#onRequestEventBeat
--> EventDispatcherImpl#dispatchAllEvents
--> ReactChoreographer#postFrameCallback(TIMERS_EVENTS,ScheduleDispatchFrameCallback)


--> EventQueue#enqueueEvent(enqueueUniqueEvent)
--> UnbatchedEventQueue#onEnqueue
--> AsyncEventBeat#request
--> AsyncEventBeat#induce
--> AsyncEventBeat#tick
--> EventQueue#eventBeat_
--> EventQueue#onBeat
--> EventQueue#flushStateUpdates
--> EventQueueProcessor#flushStateUpdates
--> Scheduler#statePipe
--> UIManager#updateState
--> ShadowTree#commit

--> EventQueue#enqueueEvent(enqueueUniqueEvent)
--> UnbatchedEventQueue#onEnqueue
--> AsyncEventBeat#request
--> AsyncEventBeat#induce
--> AsyncEventBeat#tick
--> EventQueue#eventBeat_
--> EventQueue#onBeat
--> EventQueue#flushEvents
--> EventQueueProcessor#flushEvents
--> Scheduler#eventPipe
--> UIManagerBinding#dispatchEvent
--> ReactFabric-dev#dispatchEvent
```

<!-- ## *react应用页面再次渲染* -->
## *参考资料*
[1]:https://github.com/spacecraft-plan/spacecraft-rn
[React as a UI Runtime](https://overreacted.io/react-as-a-ui-runtime/#renderers)
[在 Android 上启用 Fabric](https://reactnative.cn/docs/next/new-architecture-app-renderer-android)