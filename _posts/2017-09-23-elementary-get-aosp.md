---
layout: post
title: 用正确的姿势下载和编译AOSP
description: 如果有兴趣在自己的Mac电脑下载和编译一套Android源码的话，可以查看这一篇文章，帮助你跳过一些坑
date: 2017-09-23
share: true
comments: true
tag:
- 基础知识
# - AOSP(SYS)
---



## *1.Summary*{:.header2-font}
&emsp;&emsp;在获取和编译AOSP代码遇到了一些坑，所以特意来写个文章记录一下，不然回头又忘记当初怎么解决坑的。健忘真是程序员的专长，今天出门之前提醒自己要带伞，结果出了门才发现没带。

## *2.About*{:.header2-font}
&emsp;&emsp;其实AOSP官方已经有详细的教程不过针对的是Linux（Ubuntu版本），MacOS并没有。所以本文针对的是在macOS环境下获取和编译AOSP。可是在Linux和macOS中获取和编译AOSP操作步骤是一样的，只是存在一些库版本或者库类型问题。这里推荐AOSP官网的["Downloading and Building"](https://source.android.com/source/requirements)文章供初学者学习，需要自带梯子。外面的世界还是不错的，有一些只能通过肢体语言来表达情感的内容还是值得一看的。如果看不懂英文，没关系，我这里在推荐几个中文的网站，如：[中科大](https://lug.ustc.edu.cn/wiki/mirrors/help/aosp)、[清华](https://mirrors.tuna.tsinghua.edu.cn/help/AOSP/)。我用的是中科大的镜像。知道怎么获取和编译AOSP之后，接下来就开始分析会遇到有哪些坑吧。说个提问话，如果不知道什么是repo的话可以看看这一篇文章[Android源码解析之repo仓库]({{site.baseurl}}/2017-04/study-repo)
## *3.Intoduction*{:.header2-font}
&emsp;&emsp;通过观看了上面提供的的资料之后，我们终于知道了怎么来获取和编译AOSP。下面主要从两方面入手：获取AOSP的过程和编译AOSP的过程

配置环境：
```
系统：macOS Sierra Version 10.12.6
macOS SDK：10.12
build: Android 8.0 r1
java version：java 1.8.0_144
python version：python 2.7.10
```

### *获取AOSP的过程*{:.header3-font}

### repo sync被莫名终止
&emsp;&emsp;使用repo工具过程中可能由于网络不稳定或者其他原因导致repo sync终止，其实大可不用担心，重新repo sync即可，并且会在断掉的地方继续获取AOSP源码。这里说个题外话。获取代码的顺序是从.repo/manifest.xml文件来的(.repo/manifest.xml是.repo/manifests/default.xml的符号链接,任意修改任何一处都会使得两个文件有变化，Linux下的符号链接存在的意义可以理解为Windows下的快捷方式，但是功能不同于Windows下的快捷方式)，仔细观察可以发现manifest.xml文件中目录的排序规则就是按照字母表顺序来的，所以当拉取源码到tools目录时，我们就知道快要完事了。

### *编译AOSP的过程*{:.header3-font}

### 需要使用设置AOSP目录的文件系统
&emsp;&emsp;主要是AOSP文件系统区分大小写，于是创建一块区分大小的分区供AOSP使用。

```bash
hdiutil create -type SPARSE -fs 'Case-sensitive Journaled HFS+' -size 70g ~/android.dmg
hdiutil attach ~/android.dmg.sparseimage -mountpoint /Volumes/android;
```

由于网上有人推荐70g(android 6.0),但是没想到在编译Android 8.0(Pixel XL)时，分区大小不足，这时候可以使用这条命令来修改分区大小`hdiutil resize -size <new-size-you-want>g ~/android.dmg.sparseimage`,修改分区的时候记得先detach镜像，在重新attach，如果detach失败就到finder应用中detach。编译Android 8.0（Pixel XL）时需要用到109g的分区，所以我创建了115g的分区。

### macOS SDK的版本
&emsp;&emsp;编译过程中由于找不到macOS SDK 10.10、10.11、10.12这三个版本中其中一个导致编译失败，最后定位到了x86_darwin_host.go文件才知道原因所在。Android 8.0使用了soong和blueprint编译工具，详细可以观看AOSP中[build/soong/README.md的解释](https://android.googlesource.com/platform/build/soong/)，如果不能接受英文的话可以看看中文翻译[Android源码解析之AOSP新的构建系统]({{site.baseurl}}/blog/2017-09-23/2017-09-23-translate-blueprint-soong)。x86_darwin_host.go文件表明了当前的AOSP编译系统支持三个sdk版本.

build/soong/cc/config/x86_darwin_host.go
```go
 88         darwinSupportedSdkVersions = []string{
 89                 "10.10",
 90                 "10.11",
 91                 "10.12",
 92         //        "10.13",
 93         }
```
但是我自作聪明添加了一个目前系统自带的版本（10.13），结果可想而知当然是不能使用了。所以我们要在macOS系统中添加darwinSupportedSdkVersions列表中的某一个。从这个网站下载你需要的sdk：https://github.com/phracker/MacOSX-SDKs ,如果你下载的是tar.xz格式的文件，可以使用`tar -vxjf 文件名`命令行解压tar.xz格式的文件。将解压后的文件添加到/macOS_SDK/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/或者/Library/Developer/CommandLineTools/SDKs/MacOSX，都可以，前者是后者的符号链接。对了，只要添加进去就可以，不用做其他处理，编译过程中会自动去查询10.12这个macOS SDK。如果报错，最好检查一下sdk的路径文件，使用brew doctor。如果有报错信息，使用`sudo xcode-select -switch /`。

### curl版本
macOS使用的curl是基于SecureTransport，而jack使用的curl是基于OpenSSL，所以使用brew安装之后要在~/.profile文件添加`export PATH=$(brew --prefix curl)/bin:$PATH`,并source ~/.profile，或者直接在终端执行`export PATH=$(brew --prefix curl)/bin:$PATH`。两者使用差异自行google。
```bash
brew install curl --with-openssl
export PATH=$(brew --prefix curl)/bin:$PATH
```

### 安装xz
```
brew install xz
```
如果期间是由于缺少像xz这种工具性的东西，安装一下继续编译就行。

### jack报错
编译时会在~/目录下生成两个重要的配置文件：~/.jack-server/config.properties文件和~/.jack-settings文件。其中~/.jack-server/config.properties文件会在~/.jack-settings文件之后生成，而且会出现编译报错。报错我们大可不必理会，检查一下两个文件的端口号一致的话，继续编译就行。

如果后续还有问题在继续写，continue。。。

### *其他*{:.header3-font}
如果编译完成，想使用Android Studio阅读源码可以观看这一篇文章[使用Android Studio阅读AOSP源码]({{site.baseurl}}/2017-04-29/elementary-using-AS-reading-code)




## *4.Reference*{:.header2-font}
[在 OS X 上编译 AOSP 源码](weibo.com/u/1785464290/home?wvr=5)

[在Mac 10.11编译最新的Android 6.0](http://blog.zhaiyifan.cn/2015/11/24/BuildAndroid6OnMacElCapitan/)