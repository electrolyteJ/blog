---
layout: post
title:  Android | Xml、View、RenderNode三棵树
description: 第一棵树到第二棵树, 第二棵树到第三棵树
tag:
- android
- renderer-ui
---
* TOC
{:toc}


# Xml Tree to View Tree

在android中开发者通过xml树描述ui，而android系统通过LayoutInflater类读取xml资源文件，并且将其转换为View树，View树最后会被测量布局绘制到屏幕。读取xml资源文件使用的是XmlResourceParser类，采用流式读取节点。

```java
   public View inflate(XmlPullParser parser, @Nullable ViewGroup root, boolean attachToRoot) {
        synchronized (mConstructorArgs) {
            Trace.traceBegin(Trace.TRACE_TAG_VIEW, "inflate");

            final Context inflaterContext = mContext;
            final AttributeSet attrs = Xml.asAttributeSet(parser);
            Context lastContext = (Context) mConstructorArgs[0];
            mConstructorArgs[0] = inflaterContext;
            View result = root;

            try {
                // Look for the root node.
                int type;
                while ((type = parser.next()) != XmlPullParser.START_TAG &&
                        type != XmlPullParser.END_DOCUMENT) {
                    // Empty
                }

                ...

                final String name = parser.getName();
                ...
                //带着merge标签
                if (TAG_MERGE.equals(name)) {
                    if (root == null || !attachToRoot) {
                        throw new InflateException("<merge /> can be used only with a valid "
                                + "ViewGroup root and attachToRoot=true");
                    }

                    rInflate(parser, root, inflaterContext, attrs, false);
                } else {
                    // Temp is the root view that was found in the xml
                    final View temp = createViewFromTag(root, name, inflaterContext, attrs);

                    ViewGroup.LayoutParams params = null;

                    if (root != null) {
                        ...
                        // Create layout params that match root, if supplied
                        params = root.generateLayoutParams(attrs);
                        if (!attachToRoot) {
                            // Set the layout params for temp if we are not
                            // attaching. (If we are, we use addView, below)
                            temp.setLayoutParams(params);
                        }
                    }

                    ...

                    // Inflate all children under temp against its context.
                    rInflateChildren(parser, temp, attrs, true);

                    ....

                    // We are supposed to attach all the views we found (int temp)
                    // to root. Do that now.
                    if (root != null && attachToRoot) {
                        root.addView(temp, params);
                    }

                    // Decide whether to return the root that was passed in or the
                    // top view found in xml.
                    if (root == null || !attachToRoot) {
                        result = temp;
                    }
                }

            } catch (XmlPullParserException e) {
              ...
            } catch (Exception e) {
                ...
            } finally {
                // Don't retain static reference on context.
                mConstructorArgs[0] = lastContext;
                mConstructorArgs[1] = null;

                Trace.traceEnd(Trace.TRACE_TAG_VIEW);
            }

            return result;
        }
    }
```
先从根部解析，如果是merge标签，就执行rInflate方法；如果不是就createViewFromTag（该方法里面核心操作就是通过工厂模式创建了View，Factory兼容版本实现、Factory2新版本实现、FactoryMerger 有与Activity只是实现了Factory2所以自动适配），紧接着调用rInflateChildren解析child，最后都将控件从xml解析出来之后，就add进container。

在这里分析一下，rInflate和rInflateChildren两个方法。

```java
final void rInflateChildren(XmlPullParser parser, View parent, AttributeSet attrs,
            boolean finishInflate) throws XmlPullParserException, IOException {
        rInflate(parser, parent, parent.getContext(), attrs, finishInflate);
    }
...
void rInflate(XmlPullParser parser, View parent, Context context,
            AttributeSet attrs, boolean finishInflate) throws XmlPullParserException, IOException {

        final int depth = parser.getDepth();
        int type;
        boolean pendingRequestFocus = false;

        while (((type = parser.next()) != XmlPullParser.END_TAG ||
                parser.getDepth() > depth) && type != XmlPullParser.END_DOCUMENT) {

            if (type != XmlPullParser.START_TAG) {
                continue;
            }

            final String name = parser.getName();

            if (TAG_REQUEST_FOCUS.equals(name)) {
                pendingRequestFocus = true;
                consumeChildElements(parser);
            } else if (TAG_TAG.equals(name)) {
                parseViewTag(parser, parent, attrs);
            } else if (TAG_INCLUDE.equals(name)) {
                if (parser.getDepth() == 0) {
                    throw new InflateException("<include /> cannot be the root element");
                }
                parseInclude(parser, context, parent, attrs);
            } else if (TAG_MERGE.equals(name)) {
                throw new InflateException("<merge /> must be the root element");
            } else {
                final View view = createViewFromTag(parent, name, context, attrs);
                final ViewGroup viewGroup = (ViewGroup) parent;
                final ViewGroup.LayoutParams params = viewGroup.generateLayoutParams(attrs);
                rInflateChildren(parser, view, attrs, true);
                viewGroup.addView(view, params);
            }
        }

        if (pendingRequestFocus) {
            parent.restoreDefaultFocus();
        }

        if (finishInflate) {
            parent.onFinishInflate();
        }
    }
```
rInflate方法会遍历整个xml树，其中解析到include、merge等标签，当解析到view标签时要么递归继续遍历子view，要么创建当前view，创建View主要依赖于多种Factory类。

创建View的策略
```java
 View createViewFromTag(View parent, String name, Context context, AttributeSet attrs,
            boolean ignoreThemeAttr) {
            ...
            View view;
            if (mFactory2 != null) {
                view = mFactory2.onCreateView(parent, name, context, attrs);
            } else if (mFactory != null) {
                view = mFactory.onCreateView(name, context, attrs);
            } else {
                view = null;
            }

            if (view == null && mPrivateFactory != null) {
                view = mPrivateFactory.onCreateView(parent, name, context, attrs);
            }

            if (view == null) {
                final Object lastContext = mConstructorArgs[0];
                mConstructorArgs[0] = context;
                try {
                    if (-1 == name.indexOf('.')) {
                        view = onCreateView(parent, name, attrs);
                    } else {
                        view = createView(name, null, attrs);
                    }
                } finally {
                    mConstructorArgs[0] = lastContext;
                }
            }
            ...
}
```
1. 尝试使用Factory2生产的View
2. 方案一不行，尝试使用Factory生产的View
3. 方案二不行，尝试使用系统提供android.view包下的View
4. 方案三不行，classloader加载view然后再反射构造View(createView)

从上面的逻辑我们能定义一个自己的Factory，来决定View的构造，基于此逻辑我们可以实现资源动态换肤。

解析完xml树我们就得到了整棵View树，接下来就是基于View树进行测量布局绘制，在软件绘制直接使用skia进行光栅化，而硬件绘制却需要将View树转为DisplayList树给opengl进行光栅化。