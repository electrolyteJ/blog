---
layout: post
title: React Native ---  启动流程
description: 启动一个React应用
date: 2021-12-05 22:50:00
share: true
comments: true
tag:
# - react native
- cross-platform
published : true 
---
## *Introduction*{:.header2-font}

### 宿主应用的启动
在宿主应用的Application中必须实现ReactApplication接口的getReactNativeHost方法，该方法对整个宿主应用提供ReactNativeHost对象，ReactNativeHost对象暴露了这么一些数据。
- React应用的入口(getJSMainModuleName)：e.g. "index.android"
- 要加载的js bundle的文件位置(getBundleAssetName/getJSBundleFile):e.g. "index.android.bundle"
- 自定义js执行器(getJavaScriptExecutorFactory)：有苹果的JavaScriptCore 还有 facebook自研Hermes
- Application对象
- 用来管理React应用的ReactInstanceManager对象
- ReactPackage集合(getPackages)：暴露给js使用的native api(NativeModule) 或者 native view

### React应用的启动
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

ReactApplicationContext的创建比较简单就set一些对象比如全局的NativeModuleCallExceptionHandler处理器，CatalystInstance对象，我们主要关注的是有CatalystInstace负责的js bundle加载过程，这里我们需要说明一下，单单从CatalystInstace名字我们就能知道其职责，催生一个React应用实例，其是一个混合对象，一部分是有JVM堆分配的java对象，一部分是有操作系统分配的cpp对象。
```
CatalystInstanceImpl.java                      CatalystInstanceImpl.cpp 
 loadScriptFromAssets                           jniLoadScriptFromAssets
 loadScriptFromFile/loadSplitBundleFromFile     jniLoadScriptFromFile
```
CatalystInstanceImpl的cpp对象持有Instace的cpp对象，Instance对象是整个java 与 js 通信的关键点，其内部通过NativeToJsBridge对象(封装了js引擎)加载bundle，也能调用js的方法。

创建完ReactContext 与 加载完js bundle之后，就会执行setupReactContext方法，通知各个模块js实例初始化完毕。
## 2.onResume
执行生命周期ReactInstanceManager#onHostResume，ReactContext#onHostResume,没有什么重要的事情。

## 3.make visibilty
执行ReactRootView的绘制流程，在ReactRootView的onMeasure时会执行attachToReactInstanceManager，将ReactRootView注册到UIManagerModule，紧接着调用js的入口类AppRegistry的runApplication启动整个js框架，接着就是js组件的渲染，这个我们留给React Native渲染机制再讲

