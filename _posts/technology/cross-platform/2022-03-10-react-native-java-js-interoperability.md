---
layout: post
title: React Native |  Java和JavaScript互操作
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
# *java 与 javascript 互操作原理*

## *1.java 与 cpp 通信*

   java    | jni     | 内存分配|描述
   |---|---|---|---|
   boolean(1bit) | jboolean| 1byte  |无符号8位整型 uint8_t
   byte    | jbyte   | 1byte  |有符号8位整型 int8_t
   char    | jchar   | 2bytes |无符号16位整型 uint16_t
   short   | jshort  | 2bytes |有符号8位整型 int16_t
   int     | jint    | 4bytes |有符号32位整型 int32_t
   long    | jlong   | 8bytes |有符号64位整型 int64_t
   float   | jfloat  | 4bytes |32位浮点型    float
   double  | jdouble | 8bytes |64位浮点型    double
   Object  | jobject
   Class   | jclass
   String  | jstring
   Object[]| jobjectArray
   boolean[]|jbooleanArray
   byte[]   |jbyteArray
   char[]   |jcharArray
   short[]  |jshortArray
   int[]    |jintArray
   long[]   |jlongArray
   float[]  |jfloatArray
   double[] |jdoubleArray
   void     | void

java访问cpp函数通过jni将java的native函数与cpp的函数进行映射,cpp访问java函数可以通过反射。

   java    | fbjni
   |---|---
   T | JavaClass\<T\>
  
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
}
```
在cpp堆中创建java类对象，通过智能指针管理生命周期。

cpp标准库的智能指针与fbjni的智能引用
```
cpp
- weak_ptr:weak_ptr可以解决shared_ptr循环引用问题，导致内存泄漏问题
- shared_ptr:只有引用计数为0才会释放指针
- unique_ptr:引用计数只能为1

jni
- alias_ref：non-owning reference, like a bare pointer。用于函数的形参
- local_ref：引用计数指针。用于函数体内部应用，return 到java侧自动释放
- global_ref:引用计数指针。用于类成员变量，return到java侧并不会自动释放
```

## *2.javascript 与 cpp 通信*

   javascript    | jsi 
   |---|---
   js的对象 | host object
   js的函数 | host functioin

javascript调用cpp接口通过jsi， cpp调用javascript接口也是通过jsi

```javascript
//TurboModuleRegistry.js
const turboModuleProxy = global.__turboModuleProxy;
function requireModule<T: TurboModule>(name: string): ?T {
  ...

  if (turboModuleProxy != null) {
    const module: ?T = turboModuleProxy(name);
    return module;
  }

  return null;
}
...
//TurboModuleBinding.cpp
void TurboModuleBinding::install(
    jsi::Runtime &runtime,
    const TurboModuleProviderFunctionType &&moduleProvider,
    TurboModuleBindingMode bindingMode,
    std::shared_ptr<LongLivedObjectCollection> longLivedObjectCollection) {
  runtime.global().setProperty(
      runtime,
      "__turboModuleProxy",
      jsi::Function::createFromHostFunction(
          runtime,
          jsi::PropNameID::forAscii(runtime, "__turboModuleProxy"),
          1,
          [binding = TurboModuleBinding(
               std::move(moduleProvider),
               bindingMode,
               std::move(longLivedObjectCollection))](
              jsi::Runtime &rt,
              const jsi::Value &thisVal,
              const jsi::Value *args,
              size_t count) mutable {
            return binding.getModule(rt, thisVal, args, count);
          }));
}
```
js函数__turboModuleProxy为global对象的成员属性，在react native初始化的时候cpp层通过createFromHostFunction函数将入host function注入到global对象。

createFromHostFunction函数参数如下
- runtime：js引擎
- name：函数名
- paramCount：函数参数个数
- func：函数体


在react native中使用了jsi技术将cpp层的函数映射js侧的函数，就能相互调用.

## *3.java 与 javascript 通信*
react native的java与javascript通信是基于前面两种融合实现的，前者使用jni后者使用jsi，cpp层作为了两者的桥梁。
![arch]({{site.baseurl}}/asset/cross-platform/react-native-arch.jpeg)


# *javascript调用java接口*
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

## *1.获取native module*

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

## *2.调用native module的函数*
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
    auto result = env->Call#METHOD#MethodA(module.get(), method_, args); \
    throwPendingJniExceptionAsCppException();                              \
    return folly::dynamic(result);                                         \
  }

#define PRIMITIVE_CASE_CASTING(METHOD, RESULT_TYPE)                        \
  {                                                                        \
    auto result = env->Call#METHOD#MethodA(module.get(), method_, args); \
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
---> JavaNativeModule#invoke(切到mqt_native_modules线程)
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


## *3.升级版turbo*

2022年react native架构进行了升级，提出了一种turbo package，使用turbo方式编写的模块使用懒加载，需要实现TurboReactPackage包与TurboModule模块。下面是一个sample的代码。

SampleTurboModule js
```javascript
TurboModuleExample.js
const React = require('react');
const SampleTurboModuleExample = require('./SampleTurboModuleExample');

exports.displayName = (undefined: ?string);
exports.title = 'TurboModule';
exports.category = 'Basic';
exports.description = 'Usage of TurboModule';
exports.examples = [
  {
    title: 'SampleTurboModule',
    render: function (): React.Element<any> {
      return <SampleTurboModuleExample />;
    },
  },
];


NativeSampleTurboModule.js
...
export interface Spec extends TurboModule {
  // Exported methods.
  +getConstants: () => {|
    const1: boolean,
    const2: number,
    const3: string,
  |};
  +voidFunc: () => void;
  +getBool: (arg: boolean) => boolean;
  +getNumber: (arg: number) => number;
  +getString: (arg: string) => string;
  +getArray: (arg: Array<any>) => Array<any>;
  +getObject: (arg: Object) => Object;
  +getUnsafeObject: (arg: UnsafeObject) => UnsafeObject;
  +getRootTag: (arg: RootTag) => RootTag;
  +getValue: (x: number, y: string, z: Object) => Object;
  +getValueWithCallback: (callback: (value: string) => void) => void;
  +getValueWithPromise: (error: boolean) => Promise<string>;
}

export default (TurboModuleRegistry.getEnforcing<Spec>(
  'SampleTurboModule',
): Spec);

```


SampleTurboModule java

```java
//export的接口声明
public abstract class NativeSampleTurboModuleSpec extends ReactContextBaseJavaModule implements ReactModuleWithSpec, TurboModule {
  public NativeSampleTurboModuleSpec(ReactApplicationContext reactContext) {
    super(reactContext);
  }
  ...
  @ReactMethod(isBlockingSynchronousMethod = true)
  public abstract double getNumber(double arg);
  ...
}
//export的接口实现
@ReactModule(name = SampleTurboModule.NAME)
public class SampleTurboModule extends NativeSampleTurboModuleSpec {
    @DoNotStrip
  @SuppressWarnings("unused")
  @Override
  public double getNumber(double arg) {
    log("getNumber", arg, arg);
    return arg;
  }
}

```
SampleTurboModule cpp
```cpp
//cpp header
namespace facebook {
namespace react {

/**
 * C++ class for module 'SampleTurboModule'
 */
class JSI_EXPORT NativeSampleTurboModuleSpecJSI : public JavaTurboModule {
 public:
  NativeSampleTurboModuleSpecJSI(const JavaTurboModule::InitParams &params);
};

std::shared_ptr<TurboModule> SampleTurboModuleSpec_ModuleProvider(
    const std::string &moduleName,
    const JavaTurboModule::InitParams &params);

} // namespace react
} // namespace facebook

//cpp source
//该函数对应SampleTurboModule文件的getNumber
static facebook::jsi::Value
__hostFunction_NativeSampleTurboModuleSpecJSI_getNumber(
    facebook::jsi::Runtime &rt,
    TurboModule &turboModule,
    const facebook::jsi::Value *args,
    size_t count) {
  return static_cast<JavaTurboModule &>(turboModule)
      .invokeJavaMethod(rt, NumberKind, "getNumber", "(D)D", args, count);
}
...
NativeSampleTurboModuleSpecJSI::NativeSampleTurboModuleSpecJSI(
    const JavaTurboModule::InitParams &params)
    : JavaTurboModule(params) {
  methodMap_["voidFunc"] =
      MethodMetadata{0, __hostFunction_NativeSampleTurboModuleSpecJSI_voidFunc};

  methodMap_["getBool"] =
      MethodMetadata{1, __hostFunction_NativeSampleTurboModuleSpecJSI_getBool};

  methodMap_["getNumber"] = MethodMetadata{
      1, __hostFunction_NativeSampleTurboModuleSpecJSI_getNumber};

  methodMap_["getString"] = MethodMetadata{
      1, __hostFunction_NativeSampleTurboModuleSpecJSI_getString};

  methodMap_["getArray"] =
      MethodMetadata{1, __hostFunction_NativeSampleTurboModuleSpecJSI_getArray};

  methodMap_["getObject"] = MethodMetadata{
      1, __hostFunction_NativeSampleTurboModuleSpecJSI_getObject};

  methodMap_["getRootTag"] = MethodMetadata{
      1, __hostFunction_NativeSampleTurboModuleSpecJSI_getRootTag};

  methodMap_["getValue"] =
      MethodMetadata{3, __hostFunction_NativeSampleTurboModuleSpecJSI_getValue};

  methodMap_["getValueWithCallback"] = MethodMetadata{
      1, __hostFunction_NativeSampleTurboModuleSpecJSI_getValueWithCallback};

  methodMap_["getValueWithPromise"] = MethodMetadata{
      1, __hostFunction_NativeSampleTurboModuleSpecJSI_getValueWithPromise};

  methodMap_["getConstants"] = MethodMetadata{
      0, __hostFunction_NativeSampleTurboModuleSpecJSI_getConstants};
}

std::shared_ptr<TurboModule> SampleTurboModuleSpec_ModuleProvider(
    const std::string &moduleName,
    const JavaTurboModule::InitParams &params) {
  if (moduleName == "SampleTurboModule") {
    return std::make_shared<NativeSampleTurboModuleSpecJSI>(params);
  }
  return nullptr;
}
```
上面的sample代码，我们可以看到在cpp层会将java侧的SampleTurboModule.java的函数元数据信息注册到methodMap_，注册的时机为jni load时。


```cpp
//js:global.__turboModuleProxy --> cpp:TurboModuleBinding
jsi::Value TurboModuleBinding::getModule(
    jsi::Runtime &runtime,
    const jsi::Value &thisVal,
    const jsi::Value *args,
    size_t count) {
  if (count < 1) {
    throw std::invalid_argument(
        "__turboModuleProxy must be called with at least 1 argument");
  }
  std::string moduleName = args[0].getString(runtime).utf8(runtime);

  std::shared_ptr<TurboModule> module;
  {
    SystraceSection s(
        "TurboModuleBinding::moduleProvider", "module", moduleName);
    module = moduleProvider_(moduleName);
  }
  if (module) {
    // Default behaviour
    if (bindingMode_ == TurboModuleBindingMode::HostObject) {
      return jsi::Object::createFromHostObject(runtime, std::move(module));
    }

    auto &jsRepresentation = module->jsRepresentation_;
    if (!jsRepresentation) {
      jsRepresentation = std::make_unique<jsi::Object>(runtime);
      if (bindingMode_ == TurboModuleBindingMode::Prototype) {
        // Option 1: create plain object, with it's prototype mapped back to the
        // hostobject. Any properties accessed are stored on the plain object
        auto hostObject =
            jsi::Object::createFromHostObject(runtime, std::move(module));
        jsRepresentation->setProperty(
            runtime, "__proto__", std::move(hostObject));
      } else {
        // Option 2: eagerly install all hostfunctions at this point, avoids
        // prototype
        for (auto &propName : module->getPropertyNames(runtime)) {
          module->get(runtime, propName);
        }
      }
    }
    return jsi::Value(runtime, *jsRepresentation);
  } else {
    return jsi::Value::null();
  }
}
TurboModuleProviderFunctionType moduleProvider_;
```
与global.nativeModuleProxy相比turbo也有一个proxy(global.__turboModuleProxy)，通过TurboModuleBinding类将js侧的global.__turboModuleProxy与cpp层的某个host function绑定。那么调用global.__turboModuleProxy(moduleName)就可直接调用TurboModuleBinding#getModule函数获取模块。

通过codegen会自动生成cpp与java的turbo接口代码，java侧的TurboModule的接口签名信息与函数地址会被存储在cpp层的TurboModule#methodMap_中.

获取某个函数地址时会从methodMap_中获取，当调用函数会执行MethodMetadata.invokder.
```cpp
  //获取函数地址
  virtual facebook::jsi::Value get(
      facebook::jsi::Runtime &runtime,
      const facebook::jsi::PropNameID &propName) override {
    std::string propNameUtf8 = propName.utf8(runtime);
    auto p = methodMap_.find(propNameUtf8);
    if (p == methodMap_.end()) {
      // Method was not found, let JS decide what to do.
      return jsi::Value::undefined();
    }
    MethodMetadata meta = p->second;
    return jsi::Function::createFromHostFunction(
        runtime,
        propName,
        static_cast<unsigned int>(meta.argCount),
        //调用某个函数时
        [this, meta](
            facebook::jsi::Runtime &rt,
            const facebook::jsi::Value &thisVal,
            const facebook::jsi::Value *args,
            size_t count) { return meta.invoker(rt, *this, args, count); });
  }
```
由于cpp层的JTurboModule对象与java侧的TurboModule对象是混合对象，所以执行MethodMetadata.invokder之后就会调用TurboModule#getNumber函数
JavaTurboModule.h
```cpp
struct JTurboModule : jni::JavaClass<JTurboModule> {
  static auto constexpr kJavaDescriptor =
      "Lcom/facebook/react/turbomodule/core/interfaces/TurboModule;";
};
```

# *java调用javascript接口*
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
---> java侧：CatalystInstance#callFunction
---> java侧：PendingJSCall#call
---> cpp层：CatalystInstance#jniCallJSFunction
---> cpp层：Instant#callJSFunction
---> cpp层：NativeToJsBridge#callFunction(切到mqt_js线程)
---> cpp层：JSIExecutor#callFunction
---> cpp层：调用callFunctionReturnFlushedQueue_#call
---> javascript侧：MessageQueue#callFunctionReturnFlushedQueue(回调js接口) 
---> javascript侧：...
---> javascript侧：AppRegistry#runApplication 创建react元素树 与 shadow树
---> javascript侧：MessageQueue#flushedQueue 数据通过queue传给cpp层
---> cpp层：得到callFunctionReturnFlushedQueue_#call的返回结果
---> cpp层：JsToNativeBridge#callNativeModules , isEndOfBatch的值为true时，会调用onBatchComplete函数
---> java侧：ReactCallback#onBatchComplete
---> java侧：NativeModuleRegistry#onBatchComplete
---> java侧：UIManagerModule#onBatchComplete 开始异步计算shadow树的布局
```  
整个链路到最后通过js引擎调用js接口,再把值通过JsToNativeBridge返回给java调用者，为了保证js接口安全，NativeToJsBridge在处理时会切换到了mqt_js线程。

MessageQueue|NativeToJsBridge|desc
|---|---|---
callFunctionReturnFlushedQueue|callFunction|回调时都会切换到mqt_js线程
invokeCallbackAndReturnFlushedQueue|invokeCallback|回调时都会切换到mqt_js线程

# *参考资料*
[Java中PhantomReference和ReferenceQueue的使用方法和工作机制](https://www.greetingtech.com/articles/1572710400000)

[C++11学习](http://blog.csdn.net/innost/article/details/52583732)

[Chromium和WebKit的智能指针实现原理分析](http://blog.csdn.net/luoshengyang/article/details/46598223)
