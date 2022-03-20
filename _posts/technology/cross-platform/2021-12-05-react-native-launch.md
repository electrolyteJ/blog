---
layout: post
title: React Native ---  启动流程
description: 启动一个React应用
date: 2021-12-05 22:50:00
share: false
comments: false
tag:
# - react native
- cross-platform
published : true 
---
* TOC
{:toc}
## *宿主应用的启动*{:.header2-font}
在宿主应用的Application中必须实现ReactApplication接口的getReactNativeHost方法，该方法对整个宿主应用提供ReactNativeHost对象，ReactNativeHost对象暴露了这么一些数据。
- React应用的入口(getJSMainModuleName)：e.g. "index.android"
- 要加载的js bundle的文件位置(getBundleAssetName/getJSBundleFile):e.g. "index.android.bundle"
- 自定义js执行器(getJavaScriptExecutorFactory)：有苹果的JavaScriptCore 还有 facebook自研Hermes
- Application对象
- 用来管理React应用的ReactInstanceManager对象
- ReactPackage集合(getPackages)：暴露给js使用的native api(NativeModule) 或者 native view

宿主应用的启动这里讲的主要是从点击应用启动图标到Application#onCreate这样一个流程，不包括splash启动页，因为对于有些react native应用ReactActivit就是启动页，这一块应该是属于React应用的启动。对于宿主应用的启动我们都比较熟悉就不展开，主要来讲讲React应用的启动。
## *React应用的启动*{:.header2-font}
React应用的入口类为ReactActivity类,由于ReactActivity的生命周期都委托给ReactActivityDelegate对象，所以主要分析ReactActivityDelegate

```java
public class ReactActivityDelegate {
  ...
  private final @Nullable Activity mActivity;
  private final @Nullable String mMainComponentName;
  private ReactDelegate mReactDelegate;
  ...
  public ReactActivityDelegate(ReactActivity activity, @Nullable String mainComponentName) {
    mActivity = activity;
    mMainComponentName = mainComponentName;
  }
  
  protected ReactRootView createRootView() {
    return new ReactRootView(getContext());
  }

  /**
  * 入口组件，在index.android中注册的组件 
  * e.g. AppRegistry.registerComponent('RNTesterApp', () => RNTesterApp);
  */
  public String getMainComponentName() {
    return mMainComponentName;
  }
  protected void onCreate(Bundle savedInstanceState) {
    String mainComponentName = getMainComponentName();
    mReactDelegate =
        new ReactDelegate(
            getPlainActivity(), getReactNativeHost(), mainComponentName, getLaunchOptions()) {
          @Override
          protected ReactRootView createRootView() {
            return ReactActivityDelegate.this.createRootView();
          }
        };
    if (mainComponentName != null) {
      loadApp(mainComponentName);
    }
  }
  
  protected void loadApp(String appKey) {
    mReactDelegate.loadApp(appKey);
    getPlainActivity().setContentView(mReactDelegate.getReactRootView());
  }
  
  protected void onPause() {
    mReactDelegate.onHostPause();
  }

  protected void onResume() {
    mReactDelegate.onHostResume();

    if (mPermissionsCallback != null) {
      mPermissionsCallback.invoke();
      mPermissionsCallback = null;
    }
  }

  protected void onDestroy() {
    mReactDelegate.onHostDestroy();
  }
  ...
  public void onWindowFocusChanged(boolean hasFocus) {
    if (getReactNativeHost().hasInstance()) {
      getReactNativeHost().getReactInstanceManager().onWindowFocusChange(hasFocus);
    }
  }
}

```
#### 1.onCreate
- 在onCreate中会yload React App，异步创建全局ReactApplicationContext 与 加载js bundle
- 将ReactRootView对象setContentView，等待js引擎加载完js bundle并且通过bridge将js组件对应的native组件add到ReactRootView，然后等待页面的渲染

##### java侧的load js bundle
------
接下来我们来看看load React App的关键过程

```java
public class ReactRootView extends SizeMonitoringFrameLayout
    implements RootView, MeasureSpecProvider {
...
  public void startReactApplication(
      ReactInstanceManager reactInstanceManager,
      String moduleName,
      @Nullable Bundle initialProperties,
      @Nullable String initialUITemplate) {
    ...
    try {
      ...

      mReactInstanceManager = reactInstanceManager;
      mJSModuleName = moduleName;
      mAppProperties = initialProperties;
      mInitialUITemplate = initialUITemplate;

      mReactInstanceManager.createReactContextInBackground();
      ....
    } finally {
      ...
    }
  }
...
}
```

createReactContextInBackground的调用链路：
createReactContextInBackground--->recreateReactContextInBackgroundInner--->recreateReactContextInBackgroundFromBundleLoader--->recreateReactContextInBackground--->runCreateReactContextOnNewThread--[loop]-->runCreateReactContextOnNewThread

```java
public class ReactInstanceManager {
 ....
 private void runCreateReactContextOnNewThread(final ReactContextInitParams initParams) {
     ...
    mCreateReactContextThread =
        new Thread(
            null,
            new Runnable() {
              @Override
              public void run() {
                ...  

                try {
                  ...
                  final ReactApplicationContext reactApplicationContext =
                      createReactContext(
                          initParams.getJsExecutorFactory().create(),
                          initParams.getJsBundleLoader());

                  mCreateReactContextThread = null;
                  ReactMarker.logMarker(PRE_SETUP_REACT_CONTEXT_START);
                  final Runnable maybeRecreateReactContextRunnable =
                      new Runnable() {
                        @Override
                        public void run() {
                          if (mPendingReactContextInitParams != null) {
                            runCreateReactContextOnNewThread(mPendingReactContextInitParams);
                            mPendingReactContextInitParams = null;
                          }
                        }
                      };
                  Runnable setupReactContextRunnable =
                      new Runnable() {
                        @Override
                        public void run() {
                          try {
                            setupReactContext(reactApplicationContext);
                          } catch (Exception e) {
                            // TODO T62192299: remove this after investigation
                            FLog.e(
                                ReactConstants.TAG,
                                "ReactInstanceManager caught exception in setupReactContext",
                                e);

                            mDevSupportManager.handleException(e);
                          }
                        }
                      };

                  reactApplicationContext.runOnNativeModulesQueueThread(setupReactContextRunnable);
                  UiThreadUtil.runOnUiThread(maybeRecreateReactContextRunnable);
                } catch (Exception e) {
                  mDevSupportManager.handleException(e);
                }
              }
            },
            "create_react_context");
    ReactMarker.logMarker(REACT_CONTEXT_THREAD_START);
    mCreateReactContextThread.start();
  }
  ...
}  
```
在创建ReactContext链路中runCreateReactContextOnNewThread是主要方法,该方法主要会有下面的核心步骤
- createReactContext:会启动一个线程创建ReactApplicationContext 与 加载js bundle。
- setupReactContext:监听来自native模块队列的消息，并且告知各个native模块js初始化完毕

ReactApplicationContext的创建比较简单就set一些对象比如全局的NativeModuleCallExceptionHandler处理器，CatalystInstance对象，我们主要关注的是有CatalystInstace负责的js bundle加载过程，这里我们需要说明一下，单单从CatalystInstace名字我们就能知道其职责，催生一个React应用实例，其是一个混合对象，一部分是由JVM堆分配的java对象，一部分是由操作系统分配的cpp对象。
```
CatalystInstanceImpl.java                      CatalystInstanceImpl.cpp 
 loadScriptFromAssets                           jniLoadScriptFromAssets
 loadScriptFromFile/loadSplitBundleFromFile     jniLoadScriptFromFile
```
CatalystInstanceImpl的cpp对象持有Instace的cpp对象，Instance对象是整个java 与 js 通信的关键点，其内部通过NativeToJsBridge对象(封装了js引擎)加载bundle，也能调用js的方法。

创建完ReactContext 与 加载完js bundle之后，就会执行setupReactContext方法，通知各个模块js实例初始化完毕。

##### cpp层的load js bundle
------
当CatalystInstanceImpl类被加载到classloader，就会调用其静态代码块的逻辑,`ReactBridge.staticInit();`开始load so。load的过程主要是将java侧的native方法与cpp层的方法进行映射.
```cpp
extern "C" JNIEXPORT jint JNI_OnLoad(JavaVM *vm, void *reserved) {
  return initialize(vm, [] {
    gloginit::initialize();
    FLAGS_minloglevel = 0;
    ProxyJavaScriptExecutorHolder::registerNatives();
    CatalystInstanceImpl::registerNatives();
    CxxModuleWrapperBase::registerNatives();
    CxxModuleWrapper::registerNatives();
    JCxxCallbackImpl::registerNatives();
    NativeArray::registerNatives();
    ReadableNativeArray::registerNatives();
    WritableNativeArray::registerNatives();
    NativeMap::registerNatives();
    ReadableNativeMap::registerNatives();
    WritableNativeMap::registerNatives();

#ifdef WITH_INSPECTOR
    JInspector::registerNatives();
#endif
  });
}
```
当实例化一个CatalystInstanceImpl对象之后，会在构造器中，初始化native到js的桥，在这条桥上游两条消息通道，一条通往js，一条通往模块调用
```cpp
void Instance::initializeBridge(
    std::unique_ptr<InstanceCallback> callback,
    std::shared_ptr<JSExecutorFactory> jsef,
    std::shared_ptr<MessageQueueThread> jsQueue,
    std::shared_ptr<ModuleRegistry> moduleRegistry) {
  callback_ = std::move(callback);
  moduleRegistry_ = std::move(moduleRegistry);
  jsQueue->runOnQueueSync([this, &jsef, jsQueue]() mutable {
    nativeToJsBridge_ = std::make_shared<NativeToJsBridge>(
        jsef.get(), moduleRegistry_, jsQueue, callback_);

    nativeToJsBridge_->initializeRuntime();

    /**
     * After NativeToJsBridge is created, the jsi::Runtime should exist.
     * Also, the JS message queue thread exists. So, it's safe to
     * schedule all queued up js Calls.
     */
    jsCallInvoker_->setNativeToJsBridgeAndFlushCalls(nativeToJsBridge_);

    std::lock_guard<std::mutex> lock(m_syncMutex);
    m_syncReady = true;
    m_syncCV.notify_all();
  });

  CHECK(nativeToJsBridge_);
}
```
当做完这些初始化工作之后，cpp层接到java侧调用加载接口就会将控制权接手过来，其加载过程都是用cpp实现的。加载js bundle按照加载的源分为从assets加载、从远程调试器加载、从网络加载等，其抽象接口为JSBundleLoader，我们从assets加载来分析，主要入口是jniLoadScriptFromAssets

CatalystInstanceImpl.cpp
```cpp
void CatalystInstanceImpl::jniLoadScriptFromAssets(
    jni::alias_ref<JAssetManager::javaobject> assetManager,
    const std::string &assetURL,
    bool loadSynchronously) {
  const int kAssetsLength = 9; // strlen("assets://");
  auto sourceURL = assetURL.substr(kAssetsLength);

  auto manager = extractAssetManager(assetManager);
  auto script = loadScriptFromAssets(manager, sourceURL);
  if (JniJSModulesUnbundle::isUnbundle(manager, sourceURL)) {
    auto bundle = JniJSModulesUnbundle::fromEntryFile(manager, sourceURL);
    auto registry = RAMBundleRegistry::singleBundleRegistry(std::move(bundle));
    instance_->loadRAMBundle(
        std::move(registry), std::move(script), sourceURL, loadSynchronously);
    return;
  } else if (Instance::isIndexedRAMBundle(&script)) {
    instance_->loadRAMBundleFromString(std::move(script), sourceURL);
  } else {
    instance_->loadScriptFromString(
        std::move(script), sourceURL, loadSynchronously);
  }
}
```
react native将bundle分为三种plain bundle、ram bundle、hbc bundle(hemers引擎支持)，在android中ram bundle的实现为file ram bundle(JniJSModulesUnbundle类)，也支持indexed ram bundle(JSIndexedRAMBundle类)，ios的实现则为indexed ram bundle,具体看[这文章](https://blog.csdn.net/gg_ios/article/details/100663016)，所以在选择哪种加载时，我们能看到对于ram bundle的判断有两种`JniJSModulesUnbundle::isUnbundle`与`Instance::isIndexedRAMBundle`

```cpp
    1. file ram bundle加载流程
    auto bundle = JniJSModulesUnbundle::fromEntryFile(manager, sourceURL);
    auto registry = RAMBundleRegistry::singleBundleRegistry(std::move(bundle));
    instance_->loadRAMBundle(
        std::move(registry), std::move(script), sourceURL, loadSynchronously);

    2. indexed ram bundle加载流程
    void Instance::loadRAMBundleFromString(
        std::unique_ptr<const JSBigString> script,
        const std::string &sourceURL) {
      auto bundle = std::make_unique<JSIndexedRAMBundle>(std::move(script));
      auto startupScript = bundle->getStartupCode();
      auto registry = RAMBundleRegistry::singleBundleRegistry(std::move(bundle));
      loadRAMBundle(std::move(registry), std::move(startupScript), sourceURL, true);
    }
```
比较两种加载方式，我们就会发现他们都会调用loadRAMBundle函数，该函数有三个形参
1.bundleRegistry：ram bundle的注册中心
2.startupScript：入口脚本的内容
3.startupScriptSourceURL：入口脚本的地址
4.loadSynchronously：加载方式，同步或者异步

loadRAMBundle函数会调用NativeToJsBridge同步或者异步的load ram bundle，采用哪种方式主要看传入的参数loadSynchronously。

```cpp
//同步
void NativeToJsBridge::loadBundleSync(
    std::unique_ptr<RAMBundleRegistry> bundleRegistry,
    std::unique_ptr<const JSBigString> startupScript,
    std::string startupScriptSourceURL) {
  if (bundleRegistry) {
    m_executor->setBundleRegistry(std::move(bundleRegistry));
  }
  try {
    m_executor->loadBundle(
        std::move(startupScript), std::move(startupScriptSourceURL));
  } catch (...) {
    m_applicationScriptHasFailure = true;
    throw;
  }
}
//异步
void NativeToJsBridge::loadBundle(
    std::unique_ptr<RAMBundleRegistry> bundleRegistry,
    std::unique_ptr<const JSBigString> startupScript,
    std::string startupScriptSourceURL) {
  runOnExecutorQueue(
      [this,
       bundleRegistryWrap = folly::makeMoveWrapper(std::move(bundleRegistry)),
       startupScript = folly::makeMoveWrapper(std::move(startupScript)),
       startupScriptSourceURL =
           std::move(startupScriptSourceURL)](JSExecutor *executor) mutable {
        auto bundleRegistry = bundleRegistryWrap.move();
        if (bundleRegistry) {
          executor->setBundleRegistry(std::move(bundleRegistry));
        }
        try {
          executor->loadBundle(
              std::move(*startupScript), std::move(startupScriptSourceURL));
        } catch (...) {
          m_applicationScriptHasFailure = true;
          throw;
        }
      });
}
```
对比两个函数的调用链都一样，唯一不同的是异步加载通过消息队列异步完成调用链。接下来就到了很关键的地方，通过JSExecutor#loadBundle方法可以完成加载。对于react native的JSExecutor衍生类有三种，HermesExecutor、JSCExecutor、ProxyExecutor。他们分别封装了hermes runtime 、 jsc runtime，而ProxyExecutor主要用于远程调试使用，他代理其余两个真正的执行器。那么我们就挑选JSCExecutor接下去往下读。
```cpp
class JSCExecutorFactory : public JSExecutorFactory {
 public:
  std::unique_ptr<JSExecutor> createJSExecutor(
      std::shared_ptr<ExecutorDelegate> delegate,
      std::shared_ptr<MessageQueueThread> jsQueue) override {
    auto installBindings = [](jsi::Runtime &runtime) {
      react::Logger androidLogger =
          static_cast<void (*)(const std::string &, unsigned int)>(
              &reactAndroidLoggingHook);
      react::bindNativeLogger(runtime, androidLogger);

      react::PerformanceNow androidNativePerformanceNow =
          static_cast<double (*)()>(&reactAndroidNativePerformanceNowHook);
      react::bindNativePerformanceNow(runtime, androidNativePerformanceNow);
    };
    return std::make_unique<JSIExecutor>(
        jsc::makeJSCRuntime(),
        delegate,
        JSIExecutor::defaultTimeoutInvoker,
        installBindings);
  }
};

void JSIExecutor::loadBundle(
    std::unique_ptr<const JSBigString> script,
    std::string sourceURL) {
  SystraceSection s("JSIExecutor::loadBundle");

  bool hasLogger(ReactMarker::logTaggedMarker);
  std::string scriptName = simpleBasename(sourceURL);
  if (hasLogger) {
    ReactMarker::logTaggedMarker(
        ReactMarker::RUN_JS_BUNDLE_START, scriptName.c_str());
  }
  runtime_->evaluateJavaScript(
      std::make_unique<BigStringBuffer>(std::move(script)), sourceURL);
  flush();
  if (hasLogger) {
    ReactMarker::logTaggedMarker(
        ReactMarker::RUN_JS_BUNDLE_STOP, scriptName.c_str());
  }
}
```
JSCExecutor是java对象，JSExecutor真正的衍生类为JSIExecutor，注入的runtime是jsc，所以当就会将js bundle内容注入到jsc 的evaluateJavaScript方法，jsc引擎开始渲染页面


##### javascript层的load js bundle
------
一个简单的react native项目结构
```
android/
ios/
...
App.js
index.js
package.json
...
```
当js bundle被加载到内存中，index.js入口文件中的`AppRegistry.registerComponent(appName, () => App);`会被执行，通过appName与ComponentProvider函数类型的对象注册到AppRegistry中。
AppRegistry.js
```javascript
  registerComponent(
    appKey: string,
    componentProvider: ComponentProvider,
    section?: boolean,
  ): string {
    let scopedPerformanceLogger = createPerformanceLogger();
    runnables[appKey] = {
      componentProvider,
      run: (appParameters, displayMode) => {
        const concurrentRootEnabled =
          appParameters.initialProps?.concurrentRoot ||
          appParameters.concurrentRoot;
        renderApplication(
          componentProviderInstrumentationHook(
            componentProvider,
            scopedPerformanceLogger,
          ),
          appParameters.initialProps,
          appParameters.rootTag,
          wrapperComponentProvider && wrapperComponentProvider(appParameters),
          appParameters.fabric,
          showArchitectureIndicator,
          scopedPerformanceLogger,
          appKey === 'LogBox',
          appKey,
          coerceDisplayMode(displayMode),
          concurrentRootEnabled,
        );
      },
    };
    if (section) {
      sections[appKey] = runnables[appKey];
    }
    return appKey;
  },
```
AppRegistery通过注册表runnables存储以appName为key，类对象为value。当java侧想要运行App，就可以通过appName到AppRegistery查询并且运行。

### 2.onResume
执行生命周期ReactInstanceManager#onHostResume，ReactContext#onHostResume,没有什么重要的事情。

### 3.make visibilty
##### java侧的run application
------
执行ReactRootView的绘制流程，在ReactRootView的onMeasure时会执行attachToReactInstanceManager，将ReactRootView注册到UIManagerModule，紧接着调用AppRegistry的runApplication启动整个js框架，接着就是js组件的渲染，这个我们留给React Native渲染机制再讲.
```java
public interface AppRegistry extends JavaScriptModule {

  void runApplication(String appKey, WritableMap appParameters);

  void unmountApplicationComponentAtRootTag(int rootNodeTag);

  void startHeadlessTask(int taskId, String taskKey, WritableMap data);
}
```
##### javascript层的run application
------
调用js接口主要采用了java的动态代理，JavaScriptModuleRegistry#getJavaScriptModule方法，返回一个AppRegistry的代理类。当调用runApplication方法，就会执行CatalystInstance#jniCallJSFunction,最后会执行JSIExecutor$callFunction方法，执行js的runApplication接口
AppRegistry.js
```javascript
  //启动app
  runApplication(
    appKey: string,
    appParameters: any,
    displayMode?: number,
  ): void {
    if (appKey !== 'LogBox') {
      const logParams = __DEV__
        ? '" with ' + JSON.stringify(appParameters)
        : '';
      const msg = 'Running "' + appKey + logParams;
      infoLog(msg);
      BugReporting.addSource(
        'AppRegistry.runApplication' + runCount++,
        () => msg,
      );
    }
    invariant(
      runnables[appKey] && runnables[appKey].run,
      `"${appKey}" has not been registered. This can happen if:\n` +
        '* Metro (the local dev server) is run from the wrong folder. ' +
        'Check if Metro is running, stop it and restart it in the current project.\n' +
        "* A module failed to load due to an error and `AppRegistry.registerComponent` wasn't called.",
    );

    SceneTracker.setActiveScene({name: appKey});
    runnables[appKey].run(appParameters, displayMode);
  },
```
通过caller传递的appName，运行对应的App，而run函数体中会调用`renderApplication`接口进行组件的渲染。

```javascript
function renderApplication<Props: Object>(
  RootComponent: React.ComponentType<Props>,
  initialProps: Props,
  rootTag: any,
  WrapperComponent?: ?React.ComponentType<any>,
  fabric?: boolean,
  showArchitectureIndicator?: boolean,
  scopedPerformanceLogger?: IPerformanceLogger,
  isLogBox?: boolean,
  debugName?: string,
  displayMode?: ?DisplayModeType,
  useConcurrentRoot?: boolean,
) {
  ...
  let renderable = (
    <PerformanceLoggerContext.Provider value={performanceLogger}>
      <AppContainer
        rootTag={rootTag}
        fabric={fabric}
        showArchitectureIndicator={showArchitectureIndicator}
        WrapperComponent={WrapperComponent}
        initialProps={initialProps ?? Object.freeze({})}
        internal_excludeLogBox={isLogBox}>
        <RootComponent {...initialProps} rootTag={rootTag} />
      </AppContainer>
    </PerformanceLoggerContext.Provider>
  );

  if (__DEV__ && debugName) {
    const RootComponentWithMeaningfulName = getCachedComponentWithDebugName(
      `${debugName}(RootComponent)`,
    );
    renderable = (
      <RootComponentWithMeaningfulName>
        {renderable}
      </RootComponentWithMeaningfulName>
    );
  }
  ...
  if (fabric) {
    require('../Renderer/shims/ReactFabric').render(
      renderable,
      rootTag,
      null,
      useConcurrentRoot,
    );
  } else {
    require('../Renderer/shims/ReactNative').render(renderable, rootTag);
  }
  ...
}
```
上面我们可以看到PerformanceLoggerContext.Provider 、AppContainer 、 RootComponent，这是三个重要的类,其中的、AppContainer主要封装了Inspector, RootComponen为react应用的树根。react native为了优化渲染系统引入了fabric，这里我们先不对其进行分析，先来看看在正式环境下面非fabric的逻辑代码,也就是`require('../Renderer/shims/ReactNative').render(renderable, rootTag);`。在正式环境下require导入的是ReactNativeRenderer-prod.js文件，其中export的接口类如下。
```javascript
export type ReactNativeType = {
  findHostInstance_DEPRECATED<TElementType: ElementType>(
    componentOrHandle: ?(ElementRef<TElementType> | number),
  ): ?ElementRef<HostComponent<mixed>>,
  findNodeHandle<TElementType: ElementType>(
    componentOrHandle: ?(ElementRef<TElementType> | number),
  ): ?number,
  dispatchCommand(
    handle: ElementRef<HostComponent<mixed>>,
    command: string,
    args: Array<mixed>,
  ): void,
  sendAccessibilityEvent(
    handle: ElementRef<HostComponent<mixed>>,
    eventType: string,
  ): void,
  render(
    element: Element<ElementType>,
    containerTag: number,
    callback: ?() => void,
  ): ?ElementRef<ElementType>,
  unmountComponentAtNode(containerTag: number): void,
  unmountComponentAtNodeAndRemoveContainer(containerTag: number): void,
  unstable_batchedUpdates: <T>(fn: (T) => void, bookkeeping: T) => void,
  __SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED: SecretInternalsType,
  ...
};
```
导出的ReactNativeType#render函数接下来就开始了渲染逻辑。其中传入的实参rootTag为java侧的ReactRootView,React会根据rootTag构造出一个js侧的根节点FiberRootNode，来与Java侧的ReactRootView一一对应。当组件从`PerformanceLoggerContext.Provider ---> AppContainer ---> RootComponent`，一层一层往下渲染到App，真正的页面渲染才开始。React Native如何渲染，让我们来一一剖析一下[React Native ---  渲染机制]({{site.baseurl}}/2022-03-20/react-native-render)
