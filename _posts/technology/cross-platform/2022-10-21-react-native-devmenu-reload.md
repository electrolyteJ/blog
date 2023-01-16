---
layout: post
title: React Native |  DevMenu开发者工具 reload
description: reload & fast refresh
date: 2022-10-21 22:50:00
share: false
comments: false
tag:
# - react native
- cross-platform
published : false
---
* TOC
{:toc}

![devMenu][1]

## reload & fast refresh

reload
- normal reload
- debugger reload

```
  @Override
  public void handleReloadJS() {
    ...
    // dismiss redbox if exists
    hideRedboxDialog();

    if (getDevSettings().isRemoteJSDebugEnabled()) {
      PrinterHolder.getPrinter()
          .logMessage(ReactDebugOverlayTags.RN_CORE, "RNCore: load from Proxy");
      showDevLoadingViewForRemoteJSEnabled();
      reloadJSInProxyMode();
    } else {
      PrinterHolder.getPrinter()
          .logMessage(ReactDebugOverlayTags.RN_CORE, "RNCore: load from Server");
      String bundleURL =
          getDevServerHelper()
              .getDevServerBundleURL(Assertions.assertNotNull(getJSAppBundleName()));
      reloadJSFromServer(bundleURL);
    }
  }
```

http://%s/%s.%s?platform=android&dev=%s&minify=%s&app=%s&modulesOnly=%s&runModule=%s%s

host
- metro host:从手机系统的属性表读取/system/bin/getprop，属性字段metro.host
- emulator localhost = '10.0.2.2' + 8081
- genymotion localhost = '10.0.3.2' + 8081
- device localhost = 'localhost' + 8081

mainModuleID
- android平台：index.android
- ios平台：index.ios
- 自定义路径ReactNativeHost#getJSMainModuleName

bundleType
- bundle
- map

开发环境下dev强制为true，minify强制为false，app为android应用的包名

modulesOnly为true使用分包，为false则为整包，runModule

如果使用Hermes引擎，还会追加runtimeBytecodeVersion = 引擎版本号


启动debugger-ui页面的请求：http://%s/launch-js-devtools host


与debugger服务建立连接请求：ws://%s/debugger-proxy?role=client"

fast refresh(hmr)


[1]:{{site.baseurl}}/asset/cross-platform/devMenu.png

[React Fast Refresh](https://juejin.cn/post/7064822847046156324)
[Fast Refresh](https://reactnative.dev/docs/fast-refresh#:~:text=Fast%20Refresh%20is%20a%20React,within%20a%20second%20or%20two.)