---
layout: post
title: React Native |  开发者工具
description: DevMenu
date: 2022-10-21 22:50:00
share: false
comments: false
tag:
# - react native
- cross-platform
# published : true 
---
* TOC
{:toc}


# 开发者工具项目结构

- metro : 打包器
    - metro:server
    - metro-inspector-proxy：chrome inspector代理
    - 其他
- react native cli(简称cli)：命令集
    - cli-debugger-ui: 与react native手机侧建立双向通信，且代理手机侧的js引擎执行js代码，提供debug、reload等能力
    - cli-plugin-metro:start与bundle命令
    - cli-server-api:start命令启动的server api
    - 其他命令..
- react native packagerconnection包/devsupport包: 与cli的server创建连接且通信相关, 还有react native开发工具功能的实现，包括reload、fast refresh、debug等功能

# DevMenu

![devMenu][1]


协议|client|server|url to processor|desc
|--|--|--|--|--
Http|PackagerStatusCheck|connect.Server|http://%s/status to statusPageMiddleware | react native start的服务状态有三种running 、not_running 、unrecognized
Http|DevServerHelper#openUrl|connect.Server,openURLMiddleware|http://%s/open-url to openURLMiddleware|浏览器打开url



## reload & fast refresh

协议|client|server|url |desc
|--|--|--|--|--
Http|HMRClient|MetroHmrServer|${serverScheme}://${serverHost}/hot|fast refresh功能
Http|BundleDownloader|MetroServer|http://%s/%s.%s?platform=android&dev=%s&minify=%s&app=%s&modulesOnly=%s&runModule=%s%s|全量包与分包下载功能
WS|JSPackagerClient/ReconnectingWebSocket|connect.Server(wss)|ws://%s/message?device=%s&app=%s&clientid=%s|cli server发送reload指令(显示devMenu dialog指令)等指令到手机
Http|XMLHttpRequest|connect.Server(wss)|${window.location.origin}/reload|debugger ui发送reload指令到cli server


## element inspector & debug

协议|client|server|url to processor |desc
|--|--|--|--|--
WS|JSDebuggerWebSocketClient|connect.Server(wss)|ws://%s/debugger-proxy?role=client to ({data}) => send(debuggerSocket, data)|手机JSDebuggerWebSocketClient与debugger ui通信，通过中间HttpService搭线
WS|debugger ui|connect.Server(wss)|ws://%s/debugger-proxy?role=debugger&name=Chrome to ({data}) => send(clientSocket, data)|debugger ui 与手机JSDebuggerWebSocketClient通信，通过中间HttpService搭线
WS|InspectorPackagerConnection|InspectorProxy(metro-inspector-proxy)|http://%s/inspector/device?name=%s&app=%s|inspector代理用来打开与通信chrome的devtools，打开url为devtools://devtools/bundled/js_app.html?experiments=true&v8only=true&ws
Http|DevServerHelper#launchJSDevtools|connect.Server|http://%s/launch-js-devtools to launchDevTools|打开debugger ui页面，debugger ui的地址http://${hostname}:${port}/debugger-ui${args}
Http|OpenStackFrameTask|connect.Server|http://%s/open-stack-frame to openStackFrameInEditorMiddleware|在ide中打开redbox 报错堆栈指定的文件



## perf monitor & sampling profiler
- perf monitor为fps view
- hermes 支持 samping profiler,jsc不支持


[1]:{{site.baseurl}}/asset/cross-platform/devMenu.png

