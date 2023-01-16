---
layout: post
title:  React Native | Metro打包利器
description: 专为react native定制的打包器
date: 2022-11-26 22:50:00
tag:
- build-tools
- cross-platform
published : true 
---
* TOC
{:toc}

对于前端的打包工具有webpack(大而全，图片代码打包)，rollup(专攻代码打包,框架场景常见)等，既然有这些打包工具为什么还要在移动端搞一个metro，其中一个原因为ram bundle，iOS采用indexed ram bundle读取一个文件效率更高,Android采用file ram bundle。

那么接下来了解一下metro。

## *Metro生命周期*
metro的bundling有三个阶段：
1. 解析(Resolution): 解析所有模块并且构建成图，有点类似于Gradle在配置阶段会将所有相互依赖的任务构建成图。
2. 转换(Transformation)：转换阶段会将模块转换成目标平台能识别的格式，这一阶段执行了js编译，主流常用的js编译器为babel
3. 序列化(Serialization)：最后一个阶段序列化，会将所有转换之后的模块打包成一个或者多个bundle.

### 解析(Resolution)
在Gradle的配置阶段我们常看到assets、aidl、res、java的配置。
```gradle
android{
    ...
    sourceSets {
        main {
            java.excludes = [
                    '**/build/**',
            ]
            srcDirs.forEach {
                assets.srcDirs += "$projectDir/$it/main/assets"
                aidl.srcDirs += "$projectDir/$it/main/aidl"
                res.srcDirs += "$projectDir/$it/main/res-frame-animation"
                res.srcDirs += "$projectDir/$it/main/res"
                java.srcDirs += "$projectDir/$it/main/java"
            }
        }
    }
    ...
}
```
metro与之对应项为assetExts、sourceExts。


### 转换(Transformation)
在ram bundle的启动优化中，通过getTransformOptions可以实现模块预加载，而其他的模块按需加载从而提高启动速度。

```typescript
function getTransformOptions(
  entryPoints: $ReadOnlyArray<string>,
  options: {
    dev: boolean,
    hot: boolean,
    platform: ?string,
  },
  getDependenciesOf: (path: string) => Promise<Array<string>>,
): Promise<ExtraTransformOptions> {
  // ...
}

type ExtraTransformOptions = {
  preloadedModules?: {[path: string]: true} | false,
  ramGroups?: Array<string>,
  transform?: {
    inlineRequires?: {blockList: {[string]: true}} | boolean,
    nonInlinedRequires?: $ReadOnlyArray<string>,
  },
};
```
在preloadedModules中配置的模块为预加载模块，而其他的模块在ram bundle按需加载，这一块有点类似于Android multidex，Android5.0之前可以将部分类指明到主dex，其他被分配到辅dex。在Android App的构建流程中，编译完之后还会对字节码进行混淆，这块metro也有minifierPath(默认使用metro-minify-terser)、minifierConfig.在混淆这块除了terser,metro还提供了metro-minify-uglify。


### 序列化(Serialization)
在序列化的阶段模块需要有id以便于require导入，创建模块id的函数为createModuleIdFactory，而processModuleFilter决定了过滤掉哪些模块不进入bundle，所以通过createModuleIdFactory与processModuleFilter两个函数可以实现分包。


## HMR Server

Hot React:[Hot Module Replacement](https://webpack.js.org/guides/hot-module-replacement/) --> [react-hot-loader](https://github.com/gaearon/react-hot-loader) --> [react refresh](https://github.com/facebook/react/tree/main/packages/react-refresh)

随着react-refresh、react-reconciler相继出现，react hot loader逐渐被替代，react refresh的实现与平台无关，React 、React Native等实现react-reconciler的自定义渲染器都能使用，而且react refresh能hot的颗粒度更小。在Web平台使用react refresh ,目前第三方开发者pmmmwh的项目[react-refresh-webpack-plugin](https://github.com/pmmmwh/react-refresh-webpack-plugin)。移动平台则是React Native团队自己实现且内置到了metro打包器取名[fast-refresh](https://reactnative.cn/docs/fast-refresh)。


## *参考资料*
[干货 | 减少50%空间，携程机票React Native Bundle 分析与优化](https://mp.weixin.qq.com/s/aajdqmpCLKvGaokL4Qp1tg)

[2020-06-02 React Native 打包工具Metro原理探究](https://www.jianshu.com/p/b02f719d6107)

[ctripcorp/moles-packer](https://github.com/ctripcorp/moles-packer)

[google/diff-match-patch](https://github.com/google/diff-match-patch)

[react-native-multibundler](https://github.com/smallnew/react-native-multibundler)

[React Native 拆包及实践「iOS&Android」](https://juejin.cn/post/6844903855805693965#heading-4)

[How should we set up apps for HMR now that Fast Refresh replaces react-hot-loader?](https://github.com/facebook/react/issues/16604)

[Fast Refresh原理剖析](http://www.ayqy.net/blog/fast-refresh-under-the-hood/)

[webpack HMR](http://www.ayqy.net/blog/hot-module-replacement/)