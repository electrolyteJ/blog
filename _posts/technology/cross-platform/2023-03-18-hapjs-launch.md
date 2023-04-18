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
在启动的过程中，我们可以看到Launcher#select方法调用，Launcher用来查找包名对应的进程信息LauncherInfo，它的内部有一张LauncherTable数据表存储着启动过进程的信息，比如Launcher$0 中0，进程pid，进程创建时间，进程是否还活跃activeAt等。知道了进程信息和将要启动的的LauncherClient为LauncherActivity$Client，那么接下来就行直接执行启动Activity。
```java
public class LauncherActivity extends RuntimeActivity {
    ...
        protected static class Client implements LauncherManager.LauncherClient {
        ...
        @Override
        public void launch(Context context, Intent intent) {
            Bundle options;
            if (context instanceof Activity) {
                String launchPackage = ActivityUtils.getCallingPackage((Activity) context);
                // use calling package name as default source
                if (TextUtils.isEmpty(intent.getStringExtra(EXTRA_SOURCE))) {
                    Source source = new Source();
                    source.setPackageName(launchPackage);
                    intent.putExtra(EXTRA_SOURCE, source.toJson().toString());
                }
                options = null;
                if (intent.getBooleanExtra(RuntimeActivity.EXTRA_ENABLE_DEBUG, false)
                        && !TextUtils.equals(launchPackage, context.getPackageName())) {
                    Log.e(TAG, launchPackage + " has no permission to access debug mode!");
                    return;
                }
            } else {
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                options =
                        ActivityOptionsCompat.makeCustomAnimation(
                                context, R.anim.activity_open_enter, R.anim.activity_open_exit)
                                .toBundle();
            }

            String pkg = intent.getStringExtra(RuntimeActivity.EXTRA_APP);
            String path = intent.getStringExtra(RuntimeActivity.EXTRA_PATH);
            Source source = Source.fromJson(intent.getStringExtra(RuntimeActivity.EXTRA_SOURCE));
            SystemController.getInstance().config(context, intent);

            Cache cache = CacheStorage.getInstance(context).getCache(pkg);
            if (cache.ready()) {
                AppInfo appInfo = cache.getAppInfo(); // load manifest.json
                if (appInfo != null && appInfo.getDisplayInfo() != null) {
                    intent.putExtra(EXTRA_THEME_MODE, appInfo.getDisplayInfo().getThemeMode());
                }
            }

            DistributionManager distributionManager = DistributionManager.getInstance();
            int status = distributionManager.getAppStatus(pkg);
            if (status != DistributionManager.APP_STATUS_READY) {
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK);
                distributionManager.scheduleInstall(pkg, path, source);
            }
            intent.putExtra(EXTRA_SESSION, LogHelper.getSession(pkg));
            intent.putExtra(EXTRA_SESSION_EXPIRE_TIME,
                    System.currentTimeMillis() + SESSION_EXPIRE_SPAN);
            PlatformLogManager.getDefault().logAppPreLaunch(pkg, path, status, source);
            context.startActivity(intent, options);
        }
    ...
    }
    ...
}
```
