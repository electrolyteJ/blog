---
layout: post
title: React Native ---  Fabric渲染器
description: 船新渲染器
date: 2022-09-22 22:50:00
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
Fabric从2018年到2021年，历时4年正式启用，关于Fabric初衷和收益看[这篇文章](https://reactnative.dev/architecture/fabric-renderer), 这里我们将几个重构的地方，在React Native的渲染流水线中存在三棵树，其中shadow树由原来的平台各自实现下沉代码到cpp层实现，从而使得各个平台的差异变小，除了shadow树还有布局逻辑、视图拍平算法，这些属于yoga，也就是变相的去掉了jni for yoga，直接在cpp层使用yoga。

RendererImplementation模块的renderElement函数调用React Native的渲染器开始渲染，让我们从ReactFabric的render函数开始讲起。
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
ReactFabric渲染的过程分别会调用FabricUIManager的createNode

react应用初始化的时候，hybrid Binding#installFabricUIManager会将cpp层的FabricMountingManager与java侧的FabricUIManager绑定，也会将cpp层的UIManager与js侧的FabricUIManager绑定(通过 UIManagerBinding#createAndInstallIfNeeded进行绑定)。前者对应Android平台的View树，后者则是介于React元素树与View树之间的Shadow树。
### *1.react应用页面初次渲染*{:.header3-font}

### *2.react应用页面再次渲染*{:.header3-font}
## *Reference*{:.header2-font}
[React as a UI Runtime](https://overreacted.io/react-as-a-ui-runtime/#renderers)
[在 Android 上启用 Fabric](https://reactnative.cn/docs/next/new-architecture-app-renderer-android)