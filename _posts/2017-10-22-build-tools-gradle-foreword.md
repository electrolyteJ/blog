---
layout: post
title:  构建工具Gradle
description: 
date: 2017-10-22
share: true
comments: true
tag:
- Build Tools
# - AOSP(APP)
---
## *1.Summary*{:.header2-font}
&emsp;&emsp;从Android团队开始宣布放弃Eclipse转投Android Studio时，构建工具Gradle进入了Android开发者的视野。而随着热修复、插件化、编译时注解的流行，深入了解Gradle就变得很有必要了。那么什么是Gradle ？
## *2.About*{:.header2-font}
&emsp;&emsp;Gradle是一个基于Ant构建工具，用Groovy DSL描述依赖关系的jar包。我们都知道早期的Android开发使用的是Eclipse,而Eclipse的构建工具使用的是Ant，用XML描述依赖关系，而XML存在太多的弊端，不如动态语言。所以动态语言Groovy代替了XML，最后集成为Gradle。而Groovy的诞生正是由于Java在后端某些地方不足，对于配置信息处理比较差，所以Apache开发了这门语言并且开源了代码。各家公司也对其进行了大量使用，其中LinkedIn公司开源了许多的gradle插件，有兴趣的可以下载源码看看。gradle的使用场景也很多，单元测试，自动化集成，依赖库管理等。既然说到了Java在后端的应用，必然要说道Android端的Java，与之搭配的就是最近很火的Kotlin，Kotlin也是一门动态语言，而且Kotlin和Groovy一样也可以写build.gradle文件，它们都是基于JVM的动态语言，都可以使用DSL去描述项目依赖关系。在说个题外话scala也是JVM语言，JVM的生态让我不服不行。

## *3.Intoduction*{:.header2-font}
&emsp;&emsp;

### *Groovy DSL*{:.header3-font}
&emsp;&emsp;首先Groovy语言的基本知识我们不进行探讨，网上与之相关的资料有很多。我们来讲讲它的DSL，因为Gradle提供的build.gradle配置文件就是用DSL来写的。那么什么是DSL？[维基百科](https://en.wikipedia.org/wiki/Domain-specific_language)里面描述的很清楚，但是具体到代码有哪些呢?就像Android里面的AIDL（Java DSL）、HIDL，前端的JQUERY（JavaScript DSL）。由于DSL是一种为解决某种问题的领域指定语言，而不像Java这种通用性计算机语言有语法解析器，所以Android团队写了解析AIDL的语法解析器，Gradle团队写了解析Groovy DSL的语法解析器。如果想要开发针对自己公司业务的DSL，那么可以自行到网上查找相关的学习资料。不过对于中小公司都是使用成熟的DSL框架，而不是重零开始，我们只要学会使用某个DSL框架就可以了，就比如Gradle框架,只要理解框架中插件的创建，任务的定义就可以了。

&emsp;&emsp;说了这么多不如来个代码感受一下。

```groovy
apply plugin: 'com.android.application'

android {
    compileSdkVersion 23
    buildToolsVersion "27.0.0"
    defaultConfig {
        applicationId "com.hawksjamesf.myapplication"
        minSdkVersion 14
        targetSdkVersion 26
        versionCode 1
        versionName "1.0"
        testInstrumentationRunner "android.support.test.runner.AndroidJUnitRunner"
    }
    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }
}

dependencies {
    implementation fileTree(include: ['*.jar'], dir: 'libs')
    implementation 'com.android.support:appcompat-v7:23.0.0'
    implementation 'com.android.support.constraint:constraint-layout:1.0.2'
//    testImplementation 'junit:junit:4.12'
    androidTestImplementation 'com.android.support.test:runner:1.0.1'
    androidTestImplementation 'com.android.support.test.espresso:espresso-core:3.0.1'
}
```


&emsp;&emsp;如果你是第一次接触Gradle的话，你一定表示看不懂这门语言，但是如果把它看成配置文件，是不是就能理解了。gradle使用了大量的闭包和lamda，这样简洁的语法来表示配置信息，而且gradle中很多地方做了省略。比如去掉分号，去掉方法括号等等，力求做到精简。
&emsp;&emsp;如果你想要配置一些简单的属性，可以通过API查看。
```groovy
buildTypes {
    debug{
        println 'haha'
    }
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }

```
&emsp;&emsp;一般DSL形成的框架都要有足够完整的API，应为其专业性太强了，就是所谓的行话，一般人看不懂，要通过查百科才能明白。
&emsp;&emsp;如果你想要根据公司的业务添加一些代码的话，光查API是不能满足需求的。需要我们自己定义任务或者插件。这就需要我们学习Gradle框架和Groovy语言了。


### *Gradle框架*{:.header3-font}
&emsp;&emsp;我们都知道Gradle的生命流程要经历三个部分：初始化、配置、执行。
- 初始化阶段：settings.gradle
在初始化阶段，gradle会为每个项目创建Project对象（每个项目项目都会有一个build.gradle），那么系统是如何知道有哪些项目的，通过settings.gradle。
- 配置阶段：build.gradle
在配置阶段，gradle会解析已经创建Project对象的项目的build.gradle文件，Project包含多个task，这些task被串在一起，存在相互依赖的关系。
- 执行阶段：task
最后就是执行这些task了。

&emsp;&emsp;基于这个流程Android团队提供了自己的插件去适配Android项目，并且提供了DSL文档[Android Plugin DSL Reference](https://google.github.io/android-gradle-dsl/current/)。如果想要看看Gradle官方提供的DSL可以看看这个文档[Gradle Build Language Reference](https://docs.gradle.org/current/dsl/index.html)。这些API还提供了hook流程的API。
我在自己的项目[SimpleWeather](https://github.com/HawksJamesf/SimpleWeather)中添加如下log。

SimpleWeather/settings.gradle
```groovy
println("settings start")
include ':app', ':location'
println("settings end")

//include ':viewpagerindicator_library'
```

SimpleWeather/build.gradle
```groovy
// Top-level build file where you can add configuration options common to all sub-projects/modules.
println("root project start")
buildscript {
    repositories {
        jcenter()
        google()



        }
    dependencies {
        classpath 'com.android.tools.build:gradle:3.0.1'
//
        // NOTE: Do not place your application dependencies here; they belong
        // in the individual module build.gradle files
    }
}

allprojects {
    repositories {
        jcenter()
        google()
    }
}

task clean(type: Delete) {
    delete rootProject.buildDir
}

ext{
    compileSdkVersion=26
    buildToolsVersion ='27.0.0'
    minSdkVersion =17
    targetSdkVersion =26
    versionCode=2
    versionName="2.0"
}

println("root project end")
```

SimpleWeather/app/build.gradle
```groovy
println("app start")
apply plugin: 'com.android.application'
android {
    compileSdkVersion rootProject.ext.compileSdkVersion
    buildToolsVersion rootProject.ext.buildToolsVersion
    defaultConfig {
        minSdkVersion rootProject.ext.minSdkVersion
        targetSdkVersion rootProject.ext.targetSdkVersion
        versionCode rootProject.ext.versionCode
        versionName rootProject.ext.versionName


        multiDexEnabled = true
        applicationId "com.hawksjamesf.simpleweather"
        testInstrumentationRunner "android.support.test.runner.AndroidJUnitRunner"
        ndk {
//             设置支持的SO库架构
            abiFilters 'x86_64'
            abiFilters 'x86'
            abiFilters 'armeabi-v7a'
            abiFilters 'arm64-v8a'
        }
    }
    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
            buildConfigField("String", "BASE_URL", '"https://weatherapi.market.xiaomi.com"')
        }
        debug {
//            buildConfigField ("String","BASE_URL",'"https://api.caiyunapp.com/"')
            buildConfigField("String", "BASE_URL", '"https://weatherapi.market.xiaomi.com"')
        }
    }
    lintOptions {
//        abortOnError false
    }

    productFlavors {

    }
}

dependencies {
    implementation fileTree(include: ['*.jar'], dir: 'libs')
    //    implementation project(':viewpagerindicator_library')
    implementation 'com.jakewharton:butterknife:8.8.1'
    annotationProcessor 'com.jakewharton:butterknife-compiler:8.8.1'
    implementation 'com.google.dagger:dagger:2.11'
    annotationProcessor 'com.google.dagger:dagger-compiler:2.11'
    implementation 'com.squareup.retrofit2:retrofit:2.3.0'
    implementation 'com.squareup.retrofit2:retrofit-converters:2.3.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.3.0'
    implementation 'com.squareup.retrofit2:adapter-rxjava2:2.+'
    implementation 'com.squareup.okhttp3:okhttp:3.8.1'
    implementation 'com.squareup.okhttp3:logging-interceptor:3.4.1'
    //    implementation 'com.jakewharton.timber:timber:4.5.1'
    implementation 'com.orhanobut:logger:2.1.1'
    implementation 'com.google.code.gson:gson:2.8.2'
    implementation 'org.greenrobot:eventbus:3.0.0'
    implementation 'io.reactivex.rxjava2:rxjava:2.+'
    implementation 'com.tencent.bugly:crashreport:2.6.6.1'
    implementation 'com.tencent.bugly:nativecrashreport:3.3.1'
    // Test helpers for Room
    testImplementation 'android.arch.persistence.room:testing:1.0.0'
    // Room (use 1.1.0-alpha1 for latest alpha)
    implementation 'android.arch.persistence.room:runtime:1.0.0'
    annotationProcessor "android.arch.persistence.room:compiler:1.0.0"
    // RxJava support for Room
    implementation 'android.arch.persistence.room:rxjava2:1.+'
    //    implementation "com.android.support:multidex:1.0.1"
    //noinspection GradleCompatible
    implementation 'com.android.support:appcompat-v7:26.1.0'
    implementation 'com.android.support:design:26.1.0'
    implementation 'com.android.support:recyclerview-v7:26.1.0'
    compile project(path: ':location')
}
println("app end")

```

SimpleWeather/location/build.gradle
```groovy
println("lib location start")
apply plugin: 'com.android.library'

android {
    compileSdkVersion rootProject.ext.compileSdkVersion
    buildToolsVersion rootProject.ext.buildToolsVersion
    defaultConfig {
        minSdkVersion rootProject.ext.minSdkVersion
        targetSdkVersion rootProject.ext.targetSdkVersion
        versionCode rootProject.ext.versionCode
        versionName rootProject.ext.versionName

        testInstrumentationRunner "android.support.test.runner.AndroidJUnitRunner"

    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }

}

dependencies {
    implementation fileTree(dir: 'libs', include: ['*.jar'])

    implementation 'com.android.support:appcompat-v7:26.1.0'
    testImplementation 'junit:junit:4.12'
    androidTestImplementation 'com.android.support.test:runner:1.0.1'
    androidTestImplementation 'com.android.support.test.espresso:espresso-core:3.0.1'
}
println("lib location end")
```

我们可以清醒的看到初始化阶段和配置阶段。
```
[0] % ./gradlew clean
Starting a Gradle Daemon, 1 incompatible Daemon could not be reused, use --status for details
settings start
settings end

> Configure project :
root project start
root project end

> Configure project :app
app start
Configuration 'compile' in project ':app' is deprecated. Use 'implementation' instead.
app end

> Configure project :location
lib location start
lib location end
```


### *Gradle任务*{:.header3-font}


[全面理解Gradle - 定义Task](http://blog.csdn.net/singwhatiwanna/article/details/78898113)

### *Gradle插件*{:.header3-font}

Android 团队写的gradle插件源码[Build Overview](http://tools.android.com/build)

## *4.Reference*{:.header2-font}

[Groovy官网](http://www.groovy-lang.org/learn.html)
[使用 Groovy 构建 DSL](https://www.ibm.com/developerworks/cn/java/j-eaed15.html)
[DSL编程技术的介绍](https://www.jianshu.com/p/17266c5b8d1c)
[CREATING YOUR OWN DSL IN KOTLIN](https://blog.simon-wirtz.de/creating-dsl-with-kotlin-introducing-a-tlslibrary/)


[Gradle的官网](https://gradle.org/)
[Kotlin Meets Gradle](https://blog.gradle.org/kotlin-meets-gradle)
[深入理解Android之Gradle](http://blog.csdn.net/innost/article/details/48228651)


