---
layout: post
title:  快应用 | Java和JavaScript互操作
description: Java <--> JavaScript
tag:
- build-tools
- cross-platform
---
* TOC
{:toc}

[快应用][1]中java与javascript互相调用主要依赖开源库[J2V8][2],该库基于v8引擎封装了jni的方法供java方法调用，基于此我们也可以使用java jni方法封装quickjs、javascriptcore、hermes。所以java与javascript互相调用的原理就这两个方法callVoidFuncation、registerJavaMethod。调用`callVoidFuncation`方法java将调用js，而`registerJavaMethod`方法将执行js调用java。


# javascript 调用 java

当JsThread线程初始化时会调用ExtensionManager#onRuntimeInit注册所有的feature模块到js引擎且还会绑定js的invoke函数，invoke函数代表了js 调用java函数的通道，所有调用多会走invoke函数。其中parameters参数是java方法元数据包括方法的类名，方法名，方法参数 ， parameters[0] 为feature名字，parameters[1]为action，parameters[2]为rawParams，parameters[3]为回调或者说返回值，parameters[4]为instanceId。

js调用invoke函数就会触发`JavaCallback#invoke --> JsInterface#invoke --> ExtensionManager#invoke --> ExtensionManager#onInvoke`调用链路，onInvoke方法实现了查询具体的feature并且执行其方法，那么如何查询到想要的feature ？ 

```java
@FeatureExtensionAnnotation(
        name = Pay.FEATURE_NAME,
        actions = {
                @ActionAnnotation(name = Pay.ACTION_PAY, mode = FeatureExtension.Mode.ASYNC),
                @ActionAnnotation(name = Pay.ACTION_GET_PROVIDER, mode = FeatureExtension.Mode.SYNC)
        })
public class Pay extends FeatureExtension {
    ...
}
```

在构建的过程中，使用gradle transform收集各个feature、widget、module的元数据到MetaDataSetImpl类，MetaDataSetImpl就像一个注册中心，外部想要找到哪个具体的feature类信息就可以通过它查询

```java
public final class MetaDataSetImpl
    extends MetaDataSet
{
    ...
    private static java.util.Map<java.lang.String, ExtensionMetaData> initFeatureMetaData() {
        ...
        extension = new ExtensionMetaData("service.pay", "org.hapjs.features.service.pay.Pay");
        extension.addMethod("pay", false, Mode.ASYNC, Type.FUNCTION, Access.NONE, Normalize.JSON, Multiple.SINGLE, "", null, null);
        extension.addMethod("getProvider", false, Mode.SYNC, Type.FUNCTION, Access.NONE, Normalize.JSON, Multiple.SINGLE, "", null, null);
        extension.validate();
        map.put("service.pay", extension);
        ...
    }
...
}
```
快应用通过FeatureBridge类实现MetaDataSetImpl的享元模式，懒加载需要使用的feature。在这里我们看到快应用的模块注册与React Native有较大差别，React Native由于其跨端的特点，模块注册中心是用cpp实现，注册模块的方式也不同，快应用使用gradle transform采集并且注册，老版React Natvie 使用for each package注册，新版React Native也是在编译采集元数据并且注册，不过并不是使用gradle transform采集，而是用babel/parser，解析js声明的接口类，像下面这样

```javascript
export interface Spec extends TurboModule {
  // Exported methods.
  +getConstants: () => {|
    const1: boolean,
    const2: number,
    const3: string,
  |};
  +voidFunc: () => void;
  +getBool: (arg: boolean) => boolean;
  +getEnum?: (arg: EnumInt) => EnumInt;
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
```

[1]:https://github.com/hapjs-platform/hapjs
[2]:https://github.com/eclipsesource/J2V8