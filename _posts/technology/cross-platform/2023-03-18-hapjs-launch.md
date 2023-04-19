---
layout: post
title:  快应用 | 快应用启动
description: 快应用启动
tag:
- cross-platform
---
* TOC
{:toc}

快应用的启动开始可能是来源于deeplink的跳转或者是桌面的启动，当进行deeplink跳转，会被DispatcherActivity解析，然后启动具体的Activity进程，而一个进程的启动最先开始是从Application类，接下来我们一步步看一下快应用如何启动。

# 宿主应用启动

当RuntimeApplication#onCreate启动过程会初始化Runtime类吗，该类就会初始化各个功能模块，比如fresco
```
public class RuntimeApplication extends Application {
    @Override
    protected void attachBaseContext(Context base) {
        super.attachBaseContext(base);
        Runtime.getInstance().onPreCreate(base);
    }

    @Override
    public void onCreate() {
        super.onCreate();
        Runtime.getInstance().onCreate(this);
    }
}
```

# 快应用启动
DispatcherActivity解析完Intent信息之后，调用LauncherManager#launch启动快应用。

```java
    public static void launch(Context context, Intent intent) {
        LauncherClient launcherClient = getLauncherClient(intent);
        if (launcherClient == null) {
            Log.w(TAG, "Fail to find responsible LauncherClient");
            return;
        }

        String pkg = launcherClient.getPackage(intent);
        if (pkg == null || pkg.isEmpty()) {
            Log.w(TAG, "Package can't be empty");
            return;
        }

        if (launcherClient.needLauncherId()) {
            Launcher.LauncherInfo launcherInfo = Launcher.select(context, pkg);
            if (launcherInfo == null) {
                throw new RuntimeException("Fail to select launcherInfo");
            }
            if (!launcherInfo.isAlive) {
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK);
            }
            intent.setClassName(context, launcherClient.getClassName(launcherInfo.id));
        } else {
            intent.setClassName(context, launcherClient.getClassName(-1));
        }
        launcherClient.launch(context, intent);
    }
```
在启动的过程中，我们可以看到Launcher#select方法调用，Launcher用来查找包名对应的进程信息LauncherInfo，它的内部有一张LauncherTable数据表存储着启动过进程的信息，比如Launcher$0 中0，进程pid，进程创建时间，进程是否还活跃activeAt等。知道了进程信息和将要启动的的LauncherClient为LauncherActivity$Client，那么接下来就行直接执行启动Activity。在Activity#onCreate中会开始load快应用基础包和快应用业务包,load过程存在这样两种场景，rpk包已经下载且安装，rpk包没有安装。如果安装要么重新刷新页面，要么重启rpk包。load启动方式有这么几种LOAD_MODE_STANDARD、LOAD_MODE_CLEAR、LOAD_MODE_HISTORY，我们来看看LOAD_MODE_STANDARD这一种，在LOAD_MODE_STANDARD中会调用RootView#load方法。

接下来会创建JsThread并且读取rpk包的js脚本，先加载基础包，然后执行infras.js脚本，然后加载业务包，执行app.js脚本。在创建JSThread并且加载基础包的时候，java侧会注册三个方法:readResource、getFrameworkJscPath、callNative，callNative接收js发送过来的dom节点信息，dom节点信息在RenderWorker线程解析并且保存到mRenderActionPackagesBuffer队列，当vsync刷新屏幕处理message时，在主线程从mRenderActionPackagesBuffer读取dom节点信息，并且让平台渲染。
