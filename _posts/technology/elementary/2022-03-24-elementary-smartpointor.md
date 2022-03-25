---
layout: post
title: 智能指针
description: 及时释放指针
published: true
date: 2022-03-24 22:50:00

tags: 
- elementary/language
# toc: true
# permalink: 

---
* TOC
{:toc}
## *Introduction*{:.header2-font}
我们都知道cpp的内存是要自己管理的，不像java这种有gc自动回收，如果手动管理内存很容易出现内存泄漏，典型的例子就是指针。那么没有好的方案来管理？答案在STL库中已经给出。


### *官方版 cpp智能指针*{:.header3-font}
STL库提供了三种智能指针
```
- weak_ptr:weak_ptr可以解决shared_ptr循环引用问题，导致内存泄漏问题。
- shared_ptr:共享式指针，只有引用计数没有限制，可以多个shared_ptr对象指向同一块内存。
- unique_ptr:独占式指针，引用计数只能为1，只能一个unique_ptr对象指向一块内存。当unique_ptr对象 a 赋值到 unique_ptr对象 b时，内存被 unique_ptr对象 b指向。
```

如何实现智能指针？
```cpp
#include <iostream>

using namespace std;

class SpObj {
public:
    template<typename T>
    void a(T t) {
        cout << "a:" << t << endl;
    }
};


template<typename T>
class sp_wrapper {
public:
    sp_wrapper(T *mPtr) : m_ptr(mPtr) {}
    virtual ~sp_wrapper() {
        //计数器
    }

    T *operator->() {
        return m_ptr;
    }
    T &operator*() {
        return *m_ptr;
    }
private:
    T *m_ptr;
};

template<typename T>
sp_wrapper<T> make() {
    sp_wrapper<T> p(new T());
    return p;
}

int main() {
    sp_wrapper<SpObj> p = make<SpObj>();
    p->a<int>(1);
    return 0;
}


```
cpp通过包装类shared_ptr来操作、检查、管理指针,在shared_ptr类中可以设置一个计数器counter，如果发生拷贝、移动拷贝、赋值，就计数器+1，当shared_ptr被析构时就检查计数器，如果为0就释放内存。

### *android版 cpp智能指针*{:.header3-font}

cpp官方是在c++11中推出智能指针比android系统晚出来，所以android系统自己设计了一套智能指针sp、wp

```cpp
- sp:通过引用计数实现，与shared_ptr<T>相同
- wp:用来解决指针相互引用，计数器满足不了自动管理内存的问题。与weak_ptr功能定位相同

class AndroidSpObj : public android::RefBase {
public:
    template<typename T>
    void a(T t) {
        cout << "AndroidSpObj 引用计数:" << t << endl;
    }
};
int main() {
    android::wp<AndroidSpObj> androidWp;
    {
        android::sp<AndroidSpObj> androidSp(new AndroidSpObj());
        androidSp->a(androidSp->getStrongCount());
        androidWp = androidSp;
        {
            android::sp<AndroidSpObj> androidSp2(androidSp);
            android::sp<AndroidSpObj> androidSp3 = androidSp;
            android::sp<AndroidSpObj> androidSp4 = androidWp.promote();
            androidSp->a(androidSp->getStrongCount());

        }
        androidSp->a(androidSp->getStrongCount());
    }
    android::sp<AndroidSpObj> androidSp5 = androidWp.promote();
    if (androidSp5 == nullptr) {
        cout << " 空指针" << endl;
    }
    return 0;
}
```

### *jni智能引用*{:.header3-font}

JNI提供了两种引用JNILocalReference与JNIGlobalReference，在jni中env->NewXxx(NewGlobalRef、NewWeakGlobalRef) 的对象，需要手动DeleteLocalRef(DeleteGlobalRef、DeleteWeakGlobalRef)

fbjni分装
```
- alias_ref：non-owning reference, like a bare pointer。常常用户函数的形参
- local_ref：引用计数指针。常常用户函数体内部应用，return 到java侧自动释放
- global_ref:引用计数指针.常常用于类成员变量，return到java侧并不会自动释放
```

## *Reference*{:.header2-font}

[jni引用](https://segmentfault.com/a/1190000022859674)

[C++11学习](http://blog.csdn.net/innost/article/details/52583732)

[Chromium和WebKit的智能指针实现原理分析](http://blog.csdn.net/luoshengyang/article/details/46598223)

[Android智能指针RefBase、sp、wp解析](https://www.jianshu.com/p/08f8ea71e698)