---
layout: post
title: 颜色滤镜
description: 
author: 电解质
tag: 
- elementary/image
- android
---

ColorFilter(颜色滤镜)
- LightingColorFilter
```
 * R' = R * colorMultiply.R + colorAdd.R
 * G' = G * colorMultiply.G + colorAdd.G
 * B' = B * colorMultiply.B + colorAdd.B
 
  @ColorInt
    private int mMul;
    @ColorInt
    private int mAdd;
```
无法修改alpha值。通过mul和add值，改变光感效果。

- PorterDuffColorFilter(图形混合)
```
 //Alpha compositing modes start 
        PorterDuff.Mode.CLEAR
        PorterDuff.Mode.SRC
        PorterDuff.Mode.DST
        PorterDuff.Mode.SRC_OVER
        PorterDuff.Mode.DST_OVER
        PorterDuff.Mode.SRC_IN
        PorterDuff.Mode.DST_IN
        PorterDuff.Mode.SRC_OUT
        PorterDuff.Mode.DST_OUT
        PorterDuff.Mode.SRC_ATOP
        PorterDuff.Mode.DST_ATOP
        PorterDuff.Mode.XOR
        
//Alpha compositing modes end
//Blending modes start 
        PorterDuff.Mode.DARKEN  变暗
        PorterDuff.Mode.LIGHTEN   变亮
        PorterDuff.Mode.MULTIPLY  正片叠底
        PorterDuff.Mode.SCREEN  滤色   
        PorterDuff.Mode.ADD  饱和度相加
        PorterDuff.Mode.OVERLAY  叠加

//Blending modes end
```

porter-duff 使用场景
```
 Paint paint = new Paint();
 canvas.drawBitmap(destinationImage, 0, 0, paint);
 
 PorterDuff.Mode mode = // choose a mode
 paint.setXfermode(new PorterDuffXfermode(mode));
 
 canvas.drawBitmap(sourceImage, 0, 0, paint);
 ```
 
有注释的为颜色混合，其余的为图形混合

- ColorMatrixColorFilter
    - 单通道(红色通道/绿色通道/蓝色通道)
    - 变暗/变亮
    
通过矩阵改变整体颜色
