---
layout: post
title: 性能优化 --- 前言
description: 性能优化
author: 电解质
date: 2022-06-15 22:50:00
share: true
comments: true
tag: 
- android-app-design
published : false
---
> 不是优化手段少，而是专挑效果明显的方案来

## *构建优化*{:.header2-font}
- 组件化/插件化:[bundles-assembler](https://github.com/electrolyteJ/bundles-assembler)框架是构建优化的大头，能提升近%60，在快应用项目中使用。
- transform/apt/kcp增量编译 ，秒级编译进阶毫秒级
- [优化构建速度](https://developer.android.com/studio/build/optimize-your-build?hl=zh-cn)，分包分时构建


## *启动优化*{:.header2-font}
- aar延迟加载/按需加载(插件化)，[bundles-assembler](https://github.com/electrolyteJ/bundles-assembler)框架提供了按需加载的能力
- 启动任务延迟加载/按需加载 ： [tasklist-composer](https://github.com/electrolyteJ/spacecraft-android/blob/master/vivian/viopt/tasklist-composer/build.gradle)


## *包体积优化*{:.header2-font}
pass