---
layout: post
title: 网络 | 改造Retrofit
description: 
author: 电解质
date: 2018-04-03 22:50:00
share: true
comments: false
tag: 
- network
- android
---
* TOC
{:toc}

# *Retrofit 名词解释*
Retrofit是由Square公司出品，基于OkHttp做的一层Restful API封装，关于什么是Restful API,请参考这一篇文章[理解RESTful架构](http://www.ruanyifeng.com/blog/2011/09/restful.html),闲话不多说，进入主题

支持的请求方法：
![network]({{site.baseurl}}/asset/network/retrofit-annotation.png)

Adapter：通过抽象工程模式创建Adapter，然后将Call适配成其他类型。eg. Call ---> RxJava

Converter：转换response的流数据为其他数据格式。eg. response data stream --->  json

# *Retrofit 设计原理*

对于开发者来说主要使用注解的形式为自己的网络api声明，后面的发送请求的事情就自动交给了Retrofit，彻底的解放双手。那么Retrofit是如何实现这么一项代理发送请求的功能，让我们往下看。

Retrofit库通过动态代理生成具体的实现类，每一个java interface类的方法声明信息都会被ServiceMethod类解析。

ServiceMethod/HttpServiceMethod
```java
abstract class ServiceMethod<T> {
  static <T> ServiceMethod<T> parseAnnotations(Retrofit retrofit, Method method) {
    RequestFactory requestFactory = RequestFactory.parseAnnotations(retrofit, method);
    ...
    return HttpServiceMethod.parseAnnotations(retrofit, method, requestFactory);
  }

  abstract @Nullable T invoke(Object[] args);
}
abstract class HttpServiceMethod<ResponseT, ReturnT> extends ServiceMethod<ReturnT> {
    ...
    static final class CallAdapted<ResponseT, ReturnT> extends HttpServiceMethod<ResponseT, ReturnT> {
        private final CallAdapter<ResponseT, ReturnT> callAdapter;
    
        CallAdapted(RequestFactory requestFactory, okhttp3.Call.Factory callFactory,
            Converter<ResponseBody, ResponseT> responseConverter,
            CallAdapter<ResponseT, ReturnT> callAdapter) {
          super(requestFactory, callFactory, responseConverter);
          this.callAdapter = callAdapter;
        }
    
        @Override protected ReturnT adapt(Call<ResponseT> call, Object[] args) {
          return callAdapter.adapt(call);
        }
      }
}
```
ServiceMethod类是一个抽象类，其parseAnnotations方法会解析http协议相关的注解信息然后生成RequestFactory，HttpServiceMethod的parseAnnotations会构建CallAdapted并且注入RequestFactory对象、CallAdapter对象、Converter对象。

HttpServiceMethod
```java
  static <ResponseT, ReturnT> HttpServiceMethod<ResponseT, ReturnT> parseAnnotations(
      Retrofit retrofit, Method method, RequestFactory requestFactory) {
    ...
    Annotation[] annotations = method.getAnnotations();
    Type adapterType;
    if (isKotlinSuspendFunction) {
        ...
    } else {
      adapterType = method.getGenericReturnType();
    }

    CallAdapter<ResponseT, ReturnT> callAdapter =
        createCallAdapter(retrofit, method, adapterType, annotations);
    Type responseType = callAdapter.responseType();
    ...
    Converter<ResponseBody, ResponseT> responseConverter =
        createResponseConverter(retrofit, method, responseType);
    okhttp3.Call.Factory callFactory = retrofit.callFactory;
    if (!isKotlinSuspendFunction) {
      return new CallAdapted<>(requestFactory, callFactory, responseConverter, callAdapter);
    } else if (continuationWantsResponse) {
        ...
    } else {
        ...
    }
  }
  
  @Override final @Nullable ReturnT invoke(Object[] args) {
  Call<ResponseT> call = new OkHttpCall<>(requestFactory, args, callFactory, responseConverter);
    return adapt(call, args);
  }
```
上面就是HttpServiceMethod构建CallAdapted的parseAnnotations,解析完注解提供的信息并构建ServiceMethod对象，然后会调用HttpServiceMethod的invoke方法发送请求。Call对象能被适配成各种对象，比如RxJava中的观察者对象,Rxjava的观察者对象通过链式调用各种操作符从而完成任务处理。

retrofit api调用链路:
`ServiceMethod#parseAnnotations(生成RequestFactory) -> HttpServiceMethod#parseAnnotations(解析注解生成call 的adapter) -> HttpServiceMethod#invoke -> CallAdapter(RetrofitCall → Rxjava/Guava)`

# *Retrofit 改造*

OkhttpCall实现了Retrofit Call且封装了Okhttp的网络请求，如果我们使用了UrlConnection，那么也可以封装成UrlConnectionCall，或者对于现在的很多公司都会基于tcp自定义协议，比如阿里mtop，携程sotp，也可以封装其Call。有兴趣的可以阅读我改造的这个项目[super-retrofit][1]，就是实现这样一种逻辑。

```java
   @Override
  final @Nullable ReturnT invoke(Object[] args) {
    Call<ResponseT> call = callFactory.newCall(requestFactory,args,responseConverter);
    return adapt(call, args);
  }
```
通过外部提供的CallFactory，构建了自己的Call，然后在自己的Call类中实现Retrofit Call提供的抽象接口。


[1]:https://github.com/electrolyteJ/super-retrofit
