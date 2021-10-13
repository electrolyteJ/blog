---
layout: post
title: TextView的图文混排
description: 
author: 电解质
date: 2021-10-12
share: true
comments: true
tag:
- app-design/ui
published : true
---
## *1.Introduction*{:.header2-font}
### **{:.header3-font}
首先得知道什么是Span？简单来说它是一种标记(mark up),比如整段字符串中出现部分高亮(@功能)，这部分高亮就可以理解为是一种标记。它们的颜色不同于其他字符；可点击；大小不同于其他的字符，简单来说他足够骚，吸引眼球，用它可以实现markdown语法，聊天信息中的图文混排。
 
## 1.用java代码编写span
 <p>
 能用来显示span的字符串有三种
 <p>
 
 Class	          |  Mutable text|	Mutable markup|Data structure|
 ---|---|---|---
 SpannedString	      |  No	          |  No	 |       Linear array
 SpannableString	   |     No	       |     Yes	 |       Linear array
 SpannableStringBuilder |	Yes	        |    Yes	  |      Interval tree
 
 ```
 String        线程安全
 StringBuilder 线程不安全
 StringBuffer 线程安全
 ```
 
 span有20种（在android.text.style包下）：
 
 ### CharacterStyle的子类
 text appearance affecting spans or text metrics affecting spans(character affection spans)
 

 1.主要是appearance这块
 - BackgroundColorSpan,背景色
 - ForegroundColorSpan,前景色
 - MaskFilterSpan,
      - EmbossMaskFilter 浮雕效果
      - BlurMaskFilter 模糊字体效果
 - StrikethroughSpan, 删除线
 - UnderlineSpan 下划线
 - TypefaceSpan,字体样式family，楷书，行书
 - StyleSpan,

 2.主要是处理metrics这块
 - MetricAffectingSpan,
    - RelativeSizeSpan
    - AbsoluteSizeSpan,
    - LocaleSpan, 本地化字符
    - SuperscriptSpan, 上标
    - SubscriptSpan, 下标
    - ScaleXSpan,字符横向拉伸

 - TextAppearanceSpan,包括color、size、style、typeface
 
 3.其他
 - ReplacementSpan,
      - DynamicDrawableSpan,
          - ImageSpan 支持四种Bitmap/Drawable/Uri/resourceId动态加载图片的方式
      - EmojiSpan
        -TypefaceEmojiSpan

 - SuggestionSpan,

 - ClickableSpan, 可点击
     - URLSpan
     - TextLinkSpan,
 <p>

### ParagraphStyle的子类
paragraph affecting spans
 - AlignmentSpan,
      - AlignmentSpan.Standard,文字对其方式
 - TabStopSpan,
      - TabStopSpan.Standard,每行距离左边的距离
 - LeadingMarginSpan.LeadingMarginSpan2,
 - LeadingMarginSpan,
      - LeadingMarginSpan.Standard, 首行缩进
      - DrawableMarginSpan,插入Drawable对象
      - IconMarginSpan,插入Bitmap对象
 - LineHeightSpan,
      - LineHeightSpan.WithDensity
 - QuoteSpan,在行首标识段落为引用

 - BulletSpan,每行的小原点

### 自定义span

Scenario|	Class or interface
--|---
Your span affects text at the character level.|	CharacterStyle
Your span affects text at the paragraph level.|	ParagraphStyle
Your span affects text appearance.	|UpdateAppearance
Your span affects text metrics.	|UpdateLayout

## 2.Html代码
通过fromHtml方法
   
## 3.compound drawable
简单的图文混排方案Textview#setCompoundDrawables



