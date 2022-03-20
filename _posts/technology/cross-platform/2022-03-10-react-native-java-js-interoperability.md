---
layout: post
title: React Native ---  Java和JavaScript通信机制
description: Java <--> JavaScript
date: 2022-03-10 22:50:00
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

### *java 与 javascript 通信原理*{:.header3-font}

1.java 与 cpp 通信
java访问cpp函数通过jni将java的native函数与cpp的函数进行映射,cpp访问java函数可以通过反射。
为了使其使用简单、易扩展、强鲁棒性，facebook封装了自己的库[fbjni](https://github.com/facebookincubator/fbjni),其中的java与cpp混合对象内存管理利用了虚可达。

- 不可达：一个对象没有被有效的引用所指向，且指向该对象的PhantomReference（如果有的话）也成了垃圾
- 虚可达：一个对象虽然没有被有效的引用所指向，但被PhantomReference引用所关联，且关联它的PhantomReference对象被其他有效引用指到了（不算垃圾了）

HybridData.java
```java
public class HybridData {

  static {
    NativeLoader.loadLibrary("fbjni");
  }

  @DoNotStrip private Destructor mDestructor = new Destructor(this);
  public synchronized void resetNative() {
    mDestructor.destruct();
  }
  public boolean isValid() {
    return mDestructor.mNativePointer != 0;
  }

  public static class Destructor extends DestructorThread.Destructor {

    // Private C++ instance
    @DoNotStrip private volatile long mNativePointer;

    Destructor(Object referent) {
      super(referent);
    }

    @Override
    protected final void destruct() {
      deleteNative(mNativePointer);
      mNativePointer = 0;
    }

    static native void deleteNative(long pointer);
  }
}
```
当java侧的对象没有被引用，jvm触发回收时，fbjni就会在Destructor#destruct，释放c++对象，从而避免内存泄漏等内存问题。


JavaClass.cpp
```cpp
struct DocTests : JavaClass<DocTests> {
  static constexpr auto kJavaDescriptor = "Lcom/facebook/jni/DocTests;";
```
在cpp堆中创建java类对象，通过智能指针管理生命周期。

cpp标准库的智能指针与fbjni的智能引用
```
cpp
- weak_ptr:weak_ptr可以解决shared_ptr循环引用问题，导致内存泄漏问题
- shared_ptr:只有引用计数为0才会释放指针
- unique_ptr:引用计数只能为1

jni
- alias_ref：non-owning reference, like a bare pointer。常常用户函数的形参
- local_ref：引用计数指针。常常用户函数体内部应用，return 到java侧自动释放
- global_ref:引用计数指针.常常用于类成员变量，return到java侧并不会自动释放
```

2.javascript 与 cpp 通信

在react native中使用了jsi技术将cpp层的函数映射js侧的函数，就能相互调用.


react native的java与javascript通信是基于前面两种融合实现的，前者使用jni后者使用jsi，cpp层作为了两者的桥梁。

### *javascript调用java接口*{:.header3-font}
这里我们来案例分析一个例子，js如何调用java的接口。

在native模块接口实现
```java
//native module
public class CalendarModule extends ReactContextBaseJavaModule {
   CalendarModule(ReactApplicationContext context) {
       super(context);
   }
   @Override
    public String getName() {
       return "CalendarModule";
    }
    @ReactMethod
    public void createCalendarEvent(String name, String location) {
    }
}
//包
public class MyAppPackage implements ReactPackage {

   @Override
   public List<ViewManager> createViewManagers(ReactApplicationContext reactContext) {
       return Collections.emptyList();
   }

   @Override
   public List<NativeModule> createNativeModules(
           ReactApplicationContext reactContext) {
       List<NativeModule> modules = new ArrayList<>();

       modules.add(new CalendarModule(reactContext));

       return modules;
   }
}
//app
public class MainApplication{
    @Override
  protected List<ReactPackage> getPackages() {
    @SuppressWarnings("UnnecessaryLocalVariable")
    List<ReactPackage> packages = new PackageList(this).getPackages();
    // below MyAppPackage is added to the list of packages returned
    packages.add(new MyAppPackage());
    return packages;
  }
}
```
在js中调用接口
```javascript
import React from 'react';
import { NativeModules, Button } from 'react-native';

const NewModuleButton = () => {
  const onPress = () => {
  const { CalendarModule } = NativeModules;
  //CalendarModule类的静态方法
   CalendarModule.createCalendarEvent('testName', 'testLocation');
    console.log('We will invoke the native module here!');
  };

  return (
    <Button
      title="Click to invoke your native module!"
      color="#841584"
      onPress={onPress}
    />
  );
};

export default NewModuleButton;
```

这里有两处关键逻辑
- 查找到对于的native模块
- 调用native模块中的函数

#### *1.获取native module*{:.header3-font}
---

当NativeModules被import之后，NativeModules.js模块会被初始化，由于使用了jsi接口架构，NativeModule就是全局对象global的nativeModuleProxy
```typescript
let NativeModules: {[moduleName: string]: $FlowFixMe, ...} = {};
if (global.nativeModuleProxy) {
  NativeModules = global.nativeModuleProxy;
} else if (!global.nativeExtensions) {
  const bridgeConfig = global.__fbBatchedBridgeConfig;
  invariant(
    bridgeConfig,
    '__fbBatchedBridgeConfig is not set, cannot invoke native modules',
  );

  const defineLazyObjectProperty = require('../Utilities/defineLazyObjectProperty');
  (bridgeConfig.remoteModuleConfig || []).forEach(
    (config: ModuleConfig, moduleID: number) => {
      // Initially this config will only contain the module name when running in JSC. The actual
      // configuration of the module will be lazily loaded.
      const info = genModule(config, moduleID);
      if (!info) {
        return;
      }

      if (info.module) {
        NativeModules[info.name] = info.module;
      }
      // If there's no module config, define a lazy getter
      else {
        defineLazyObjectProperty(NativeModules, info.name, {
          get: () => loadModule(info.name, moduleID),
        });
      }
    },
  );
}

module.exports = NativeModules;
```

当`const {CalendarModule} = NativeModules;` 进行NativeModules解构时，会调用cpp层的NativeModuleProxy#get函数，因为NativeModuleProxy是JSINativeModules的代理类,所以真正查找模块还得看JSINativeModules,其调用链为`JSINativeModules#getModule ---> ModuleRegistry#getConfig ---> m_genNativeModuleJS#call(js侧的函数global.__fbGenNativeModule)`
ModuleRegistry为模块的注册中心，所以我们需要知道模块什么时候注册到ModuleRegistry，这里就不继续追踪了直接给答案。在createReactContext时，会解析所有的ReactPackage得到全部的native模块并且存放在java侧的NativeModuleRegistry(存放ModuleHolder)中，然后在CatalystInstanceImpl#initializeBridge时，会将所有的native module传递到cpp层的ModuleRegistry(存放NativeModule)进行注册，方便js侧查询且使用。

通过ModuleRegistry获取到函数的元数据，然后将这些数据传给m_genNativeModuleJS，调用js侧global.__fbGenNativeModule(指向genModule函数)生成模块以及内部的函数,返回给cpp层的对象为这样的数据结构
```javascript
{
  name: string,
  module?: {...},
  ...
} 
//本质上就是NativeModules类型
let NativeModules: {[moduleName: string]: $FlowFixMe, ...} = {};
```
cpp层的JSINativeModules得到生成的模块之后会先缓存一份再给js侧解构之后的变量。

#### *2.调用native module的函数*{:.header3-font}
当js侧执行`CalendarModule.createCalendarEvent('testName', 'testLocation');`指令时，就会调用之前在生成模块与函数时埋下的回调。
```javascript
function genMethod(moduleID: number, methodID: number, type: MethodType) {
  let fn = null;
  if (type === 'promise') {
      ...
  } else {
    fn = function nonPromiseMethodWrapper(...args: Array<mixed>) {
      const lastArg = args.length > 0 ? args[args.length - 1] : null;
      const secondLastArg = args.length > 1 ? args[args.length - 2] : null;
      const hasSuccessCallback = typeof lastArg === 'function';
      const hasErrorCallback = typeof secondLastArg === 'function';
      ...
      // $FlowFixMe[incompatible-type]
      const onSuccess: ?(mixed) => void = hasSuccessCallback ? lastArg : null;
      // $FlowFixMe[incompatible-type]
      const onFail: ?(mixed) => void = hasErrorCallback ? secondLastArg : null;
      const callbackCount = hasSuccessCallback + hasErrorCallback;
      const newArgs = args.slice(0, args.length - callbackCount);
      if (type === 'sync') {
        return BatchedBridge.callNativeSyncHook(
          moduleID,
          methodID,
          newArgs,
          onFail,
          onSuccess,
        );
      } else {
        BatchedBridge.enqueueNativeCall(
          moduleID,
          methodID,
          newArgs,
          onFail,
          onSuccess,
        );
      }
    };
  }
  fn.type = type;
  return fn;
}
```
这里我们可以看到函数的类型分为promise、async/await、sync，对于同步函数来说执行BatchedBridge.callNativeSyncHook(BatchedBridge为MessageQueue类实例化的对象)调用。
其调用链为
```
---> MessageQueue#callNativeSyncHook 
---> global.nativeCallSyncHook 
---> JSIExecutor#nativeCallSyncHook(cpp层)
---> JsToNativeBridge#callSerializableNativeHook 
---> ModuleRegistry#callSerializableNativeHook 
---> JavaNativeModule#callSerializableNativeHook 
---> MethodInvoker#invoke
```

```cpp
MethodCallResult MethodInvoker::invoke(
    std::weak_ptr<Instance> &instance,
    alias_ref<JBaseJavaModule::javaobject> module,
    const folly::dynamic &params) {
#ifdef WITH_FBSYSTRACE
  fbsystrace::FbSystraceSection s(
      TRACE_TAG_REACT_CXX_BRIDGE,
      isSync_ ? "callJavaSyncHook" : "callJavaModuleMethod",
      "method",
      traceName_);
#endif
  ...
  auto env = Environment::current();
  auto argCount = signature_.size() - 2;
  JniLocalScope scope(env, argCount);
  jvalue args[argCount];
  std::transform(
      signature_.begin() + 2,
      signature_.end(),
      args,
      [&instance, it = params.begin(), end = params.end()](char type) mutable {
        return extract(instance, type, it, end);
      });

#define PRIMITIVE_CASE(METHOD)                                             \
  {                                                                        \
    auto result = env->Call##METHOD##MethodA(module.get(), method_, args); \
    throwPendingJniExceptionAsCppException();                              \
    return folly::dynamic(result);                                         \
  }

#define PRIMITIVE_CASE_CASTING(METHOD, RESULT_TYPE)                        \
  {                                                                        \
    auto result = env->Call##METHOD##MethodA(module.get(), method_, args); \
    throwPendingJniExceptionAsCppException();                              \
    return folly::dynamic(static_cast<RESULT_TYPE>(result));               \
  }

#define OBJECT_CASE(JNI_CLASS, ACTIONS)                                     \
  {                                                                         \
    auto jobject = env->CallObjectMethodA(module.get(), method_, args);     \
    throwPendingJniExceptionAsCppException();                               \
    if (!jobject) {                                                         \
      return folly::dynamic(nullptr);                                       \
    }                                                                       \
    auto result = adopt_local(static_cast<JNI_CLASS::javaobject>(jobject)); \
    return folly::dynamic(result->ACTIONS());                               \
  }

#define OBJECT_CASE_CASTING(JNI_CLASS, ACTIONS, RESULT_TYPE)                \
  {                                                                         \
    auto jobject = env->CallObjectMethodA(module.get(), method_, args);     \
    throwPendingJniExceptionAsCppException();                               \
    if (!jobject) {                                                         \
      return folly::dynamic(nullptr);                                       \
    }                                                                       \
    auto result = adopt_local(static_cast<JNI_CLASS::javaobject>(jobject)); \
    return folly::dynamic(static_cast<RESULT_TYPE>(result->ACTIONS()));     \
  }

  char returnType = signature_.at(0);
  switch (returnType) {
    case 'v':
      env->CallVoidMethodA(module.get(), method_, args);
      throwPendingJniExceptionAsCppException();
      return folly::none;

    case 'z':
      PRIMITIVE_CASE_CASTING(Boolean, bool)
    case 'Z':
      OBJECT_CASE_CASTING(JBoolean, value, bool)
    case 'i':
      PRIMITIVE_CASE(Int)
    case 'I':
      OBJECT_CASE(JInteger, value)
    case 'd':
      PRIMITIVE_CASE(Double)
    case 'D':
      OBJECT_CASE(JDouble, value)
    case 'f':
      PRIMITIVE_CASE(Float)
    case 'F':
      OBJECT_CASE(JFloat, value)

    case 'S':
      OBJECT_CASE(JString, toStdString)
    case 'M':
      OBJECT_CASE(WritableNativeMap, cthis()->consume)
    case 'A':
      OBJECT_CASE(WritableNativeArray, cthis()->consume)

    default:
      LOG(FATAL) << "Unknown return type: " << returnType;
      return folly::none;
  }
}
```
从这里我们就能够知道最后通过jvm反射的方式调用模块的函数，在调用链的最后一环，完成到达java侧的逻辑。这个调用链都是在js线程完成的，也就是会阻塞js线程，如果不想阻塞js线程，可以采用异步的方式，promise或者async/await，异步的方式会将模块与函数的信息存到queue，flush到cpp层(global.nativeFlushQueueImmediate)，flush间隔不能小于5ms。
调用链
```
---> global.nativeFlushQueueImmediate 
---> JSIExecutor#callNativeModules 
---> JsToNativeBridge#callNativeModules 
---> ModuleRegistry#callNativeMethod
---> JavaNativeModule#invoke(切到mqt_native_bridge线程)
```
这样就完成了异步操作。

那么如何回调？方法执行完成之后，JavaMethodWrapper#ARGUMENT_EXTRACTOR_CALLBACK的callback将数据放回给js侧,
```
---> CallbackImpl#invoke 
---> CatalystInstanceImpl#invokeCallback(CatalystInstanceImpl为JSInstance类的实现化对象) 
---> CatalystInstanceImpl#jniCallJSCallback 
---> Instance::callJSCallback 
---> NativeToJsBridge#invokeCallback(切换到mqt_js线程) 
---> ... ---> MessageQueue#invokeCallbackAndReturnFlushedQueue
```

### *java调用javascript接口*{:.header3-font}
那么java如何调用javascript接口呢？
javascript接口实现
```javascript
const AppRegistry = {
    ...
    runApplication(
        appKey: string,
        appParameters: any,
        displayMode?: number,
    ): void {
    ...
    },
    ...
    unmountApplicationComponentAtRootTag(rootTag: RootTag): void {
    // NOTE: RootTag type
    // $FlowFixMe[incompatible-call] RootTag: RootTag is incompatible with number, needs an updated synced version of the ReactNativeTypes.js file
    ReactNative.unmountComponentAtNodeAndRemoveContainer(rootTag);
    },
    ...
    startHeadlessTask(taskId: number, taskKey: string, data: any): void {
        ...
    }
  ...
}
```
java接口调用
```java
public interface AppRegistry extends JavaScriptModule {

  void runApplication(String appKey, WritableMap appParameters);

  void unmountApplicationComponentAtRootTag(int rootNodeTag);

  void startHeadlessTask(int taskId, String taskKey, WritableMap data);
}


catalystInstance.getJSModule(AppRegistry.class).runApplication(jsAppModuleName, appParams);
```
JavaScriptModuleRegistry#getJavaScriptModule通过动态代理创建一个AppRegistry代理类
```java
  private static class JavaScriptModuleInvocationHandler implements InvocationHandler {
    private final CatalystInstance mCatalystInstance;
    private final Class<? extends JavaScriptModule> mModuleInterface;
    private @Nullable String mName;
    ...
    private String getJSModuleName() {
      if (mName == null) {
        // Getting the class name every call is expensive, so cache it
        mName = JavaScriptModuleRegistry.getJSModuleName(mModuleInterface);
      }
      return mName;
    }

    @Override
    public @Nullable Object invoke(Object proxy, Method method, @Nullable Object[] args)
        throws Throwable {
      NativeArray jsArgs = args != null ? Arguments.fromJavaArgs(args) : new WritableNativeArray();
      mCatalystInstance.callFunction(getJSModuleName(), method.getName(), jsArgs);
      return null;
    }
  }
```
继续调用

```
---> CatalystInstance#callFunction
---> PendingJSCall#call
---> CatalystInstance#jniCallJSFunction
---> Instant#callJSFunction
---> NativeToJsBridge#callFunction(切到js线程)
---> JSIExecutor#callFunction
---> callFunctionReturnFlushedQueue_#call
---> MessageQueue#callFunctionReturnFlushedQueue(回调js接口) 
---> cpp层得到callFunctionReturnFlushedQueue返回的queue，如果还有数据就继续执行JSIExecutor#callNativeModules
```
整个链路到最后通过js引擎调用js接口,再把值通过JsToNativeBridge返回给java调用者，为了保证js接口安全，NativeToJsBridge在处理时会切换到了mqt_js线程。

MessageQueue|NativeToJsBridge|desc
|---|---|---
callFunctionReturnFlushedQueue|callFunction|回调时都会切换到mqt_js线程
invokeCallbackAndReturnFlushedQueue|invokeCallback|回调时都会切换到mqt_js线程

## *Reference*{:.header2-font}
[Java中PhantomReference和ReferenceQueue的使用方法和工作机制](https://www.greetingtech.com/articles/1572710400000)

[C++11学习](http://blog.csdn.net/innost/article/details/52583732)

[Chromium和WebKit的智能指针实现原理分析](http://blog.csdn.net/luoshengyang/article/details/46598223)