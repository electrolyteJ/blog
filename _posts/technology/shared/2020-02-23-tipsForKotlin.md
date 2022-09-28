---
layout: post
title: Tips for Kotlin
description: kotlin usage
author: 电解质
date: 2020-02-23 19:00:00
share: true
comments: false
tag: 
- 技术沙龙
published: true
---

> 代码质量从一丝一毫做起。


## 变量

- 可变变量var
- 不可变变量 val
- 常数const val
- 延迟初始化var lateinit:如果一个变量（全局变量或者类的成员变量）没有被初始化（init block被初始化或者直接初始化），则可以声明该关键字

```kotlin
class MainActivity :Activity{
    var lateinit btn:Button//使用lateinit 关键字可以避免大量btn初始化为null，从而导致大量使用时出现？
    var btn:Button?=null//我们都知道控件被赋值会在Activity的某个生命周期出现，所以btn初始化为null不是很有必要
    override fun onCreate(b:Bundle?){
      super.onCreate(savedInstanceState)
      btn = findViewbyId(R.id.btn)
    }
    
    override fun onStart(){
        btn.setText("btn")
        btn?.setText("btn")
    }
    override fun onResume(){
        btn.setTextColor(Color.White)
        btn?.setTextColor(Color.White)
    }
    
}
```

- val xxx by lazy{}:懒加载变量,有些控件是跟实验走，所以可以使用懒加载的形式做。

ps: by关键字除了配合lazy{}做懒加载还有其他的功效

```kotlin
class MainActivity :Activity{
    var lateinit btn:Button
    //1.可被观察变量
    val numberCounts by Delegates.observable("<no name>"){ prop, old, new ->
       println("$old -> $new")
    }
    
    val user = User(mapOf(
    "name" to "John Doe",
    "age"  to 25
    ))
    override fun onCreate(b:Bundle?){
      super.onCreate(savedInstanceState)
      btn = findViewbyId(R.id.btn)
    }
    
    override fun onStart(){
        btn.setText("btn")
        btn?.setText("btn")
    }
    override fun onResume(){
        btn.setTextColor(Color.White)
        btn?.setTextColor(Color.White)
    }
    
}

class User(val map: Map<String, Any?>) {
    val name: String by map//2.从map存储到model的变量
    val age: Int     by map
}
interface Base {
    fun print()
}

class BaseImpl(val x: Int) : Base {
    override fun print() { print(x) }
}
class Derived(b: Base) : Base by b//3.代理者模式
```

## 兼容互操作

当团队的成员既有使用java也有使用kotlin的时候，就要确保两者之间互调的合理性、可读性

- Companion（@JVMSTATICE）

```kotlin
class View(factory: ViewPort) :ViewPort by factory {
//    @get:JvmName("number")
    constructor():this(ViewFactory())
    var number=1
    @JvmField
    var number2=1
    companion object{
        const val CONSTANSE="CONSTANSE"
        @JvmStatic
        fun getA()="asdfasf"
        
        fun getB()="asdfasf"
    }
}
fun main(args: Array<String>) {
    View.getA()
}
```
```java
public class Main {
    public static void main(String[] args) {
       //为了使getA方法在被java调用和被kotlin调用表现方式一样，推荐使用注解JvmStatic
        View.getA();
        View.Companion.getB();//不推荐使用
    }
}
```

- @file:JvmName  @JvmMultifileClass:存在多个同包名同文件名的kotlin文件时，通过JvmMultifileClass可以进行合并成一个文件
- @get:JvmName/@set:JvmName：修改get/set方法的名
- lambda/匿名内部类Function0/Function1...

```kotlin
@file:JvmName("MainUtil")
fun main(args: Array<String>) {
    "asdf".jf{
        println(this)
    }
    View.getA()
}
fun String.jf(block:String.()->Unit){
        block.invoke(this)
}
```
```java
public class Main {
    public static void main(String[] args) {
        //kotlin的扩展函数中常常会使用lambda，其在java中对应的是匿名内部类FunctionX，X表示其参数。
        MainUtil.jf("1234", new Function1<String, Unit>() {
            @Override
            public Unit invoke(String s) {
                System.out.println(s);
                return null;
            }
        });
    }
}
```

# To Be Continue...
