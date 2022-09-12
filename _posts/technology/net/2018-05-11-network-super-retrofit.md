---
layout: post
title: 网络|Super Retrofit
description: 能否在Retrofit做更多的事？
author: 电解质
date: 2018-05-11 22:50:00
share: true
comments: false
tag: 
- elementary/network
published : true
---
## *1.Introduction*{:.header2-font}
为什么要阅读Retrofit源码，因为其确实优秀，不仅叫我们如何使用设计模式提高可扩展性，还留下了很多想象的空间。如何不太熟练Retrofit的皮，那么就来重新回味一下，关于如何入门Retrofit看这一片文章[网络 --- Retrofit的使用]({{site.baseurl}}/2018-04-03/network-retrofit-elementary)

对于开发者来说主要使用注解的形式为自己的网络api声明，后面的发送请求的事情就自动交给了Retrofit，彻底的解放双手构建并发送请求。那么Retrofit是如何实现这么一项代理发送请求的功能，让我们往下看。

Retrofit库通过动态代理生成具体的实现类。每一个java interface类的方法声明信息都会被ServiceMethod类解析。

ServiceMethod/HttpServiceMethod
{:.filename}
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
ServiceMethod类是一个抽象类，其parseAnnotations方法会解析http协议相关的注解信息然后生成RequestFactory，HttpServiceMethod的工程方法parseAnnotations会构建CallAdapted并且将RequestFactory对象、CallAdapter对象、Converter对象注入。

HttpServiceMethod
{:.filename}
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
上面就是HttpServiceMethod构建CallAdapted的工程方法parseAnnotations,解析完注解提供的信息并构建ServiceMethod对象，然后会调用invoke方法发送请求。得到的Retrofit Call对象能被适配成各种对象，比如RxJava中的观察者对象,Rxjava的观察者对象通过链式调用操作各种操作符从而完成任务处理。对于这里使用的OkhttpCall是封装了Okhttp的网络请求，如果我们使用了UrlConnection，那么也可以封装成UrlConnectionCall，或者对于现在的很多公司都会基于tcp自定义协议，比如阿里mtop，携程sotp，也可以封装其Call。有兴趣的可以阅读我改造的这个项目[super-retrofit](https://github.com/electrolyteJ/super-retrofit)，就是实现这样一种逻辑。

```java
  @Override
  final @Nullable ReturnT invoke(Object[] args) {
      Call<ResponseT> call = null;
      try {
          call = callFactory.newCall(requestFactory.create(args), responseConverter);
      } catch (IOException e) {
          throw new RuntimeException("Unable to create request.", e);
      }
      return adapt(call, args);
  }
```
通过外部提供的CallFactory，构建了自己的Call，然后在自己的Call类中实现Retrofit Call提供的抽象接口。
