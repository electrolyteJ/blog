---
layout: post
title: 信息流设计：ListView 之滚动
description: 
author: 电解质
tag:
- android
- renderer-ui
---

fling:手指离开(up)屏幕的速度大于系统给的(getScaledMinimumFlingVelocity、getScaledMaximumFlingVelocity),会继续滑行一段路程
- TOUCH_MODE_SCROLL
- TOUCH_MODE_FLING
- TOUCH_MODE_OVERFLING

scroll：在move的速度大于系统（getScaledTouchSlop）给的，会滚动内容


- smoothScrollBy（endFling、startScroll）
- fling（start）
- onTouchUp（start、endFling、startOverfling、startSpringback）
- onTouchDown（endFling、flywheelTouch）
- onTouchCancel（startSpringback）



OverScroller Scroller PositionScroller

onOverScrolled/overScrollBy


在手势类GestureDetector中定义了scroll、fling、single tap up、 double tap、long press，而在ListView中定义了scroll 、 over scroll、fling、over fling、tap
