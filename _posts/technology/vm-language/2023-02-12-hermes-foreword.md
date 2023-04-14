---
layout: post
title: React Native |  Hermes前言
description:  javascript引擎：Quickjs 、 Hermes 、V8
tag:
- vm-language
- cross-platform
published : false 
---

# *Hermes工程结构*

- lib库
    - Parser:词法分析器、语法分析器、语义分析器
    - AST:抽象语法树
    - IR/IRGen:中间代码生成
    - Optimizer:优化
    - BCGen:目标代码生成
    - VM:hermes虚拟机
- tools：开发者工具程序
    - hermes:repl、编译js代码、执行js代码等功能
    - hermesc:js编译器程序
    - hvm:执行js字节码的虚拟机
    - hdb:调试器
    - hbcdump:反汇编


# *参考资料*

[quickjs](https://github.com/bellard/quickjs)

[j2v8](https://github.com/eclipsesource/J2V8)

[js引擎比较](https://segmentfault.com/a/1190000039288517)

[深入理解JSCore](https://tech.meituan.com/2018/08/23/deep-understanding-of-jscore.html)

[小而精之QuickJS JavaScript引擎及周边研究(I)](https://blog.csdn.net/Innost/article/details/98491709?spm=1001.2014.3001.5501)

[干货 | 加载速度提升15%，携程对RN新一代JS引擎Hermes的调研](https://mp.weixin.qq.com/s/BOeuLoZjCdi61P_MhaJT0g)

[美团 React Native 在 JS 引擎上的选型及演进](https://time.geekbang.org/qconplus/detail/100091371)