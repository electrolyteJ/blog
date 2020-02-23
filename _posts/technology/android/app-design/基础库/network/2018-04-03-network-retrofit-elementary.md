---
layout: post
title: 网络 --- Retrofit的使用
description: 
author: 电解质
date: 2018-04-03 22:50:00
share: true
comments: true
tag: 
- app-design/network
published : false
---
* TOC
{:toc}
## *1.Summary*{:.header2-font}
&emsp;&emsp;Retrofit是由Square公司出品，基于OkHttp做的一层Restful API，关于什么是Restful API,请参考这一篇文章[理解RESTful架构](http://www.ruanyifeng.com/blog/2011/09/restful.html),闲话不多说，进入主题

## *2.Introduction*{:.header2-font}
### *Retrofit 注解类*{:.header3-font}
![network]({{site.baseurl}}/asset/2018-04-03/2018-04-03-retrofit-annotation.png)
#### 请求的方法
------
GET/HEAD POST/PUT/PATCH DELETE  OPTIONS   HTTP( custom method )

- GET:会放回数据
- HEAD:不会放回数据
- POST:不会在原有资源基础上进行更新，会重新生成资源
- PUT:会在原有资源基础上进行更新
- PATCH:局部更新
<br>

#### 请求header
-----
- Header、Headers:手动配置死了
- HeaderMap:比较灵活，可以通过代码配置
<br>

#### 请求body
----
- Body  
ps:Converter.Factory 和Converter用于转换被Body注解的对象，比如将对象转换成json；将对象转换成xml，将对象转换成字符串。除了处理请求body，还能处理响应的body以什么方式被读取。请求方法中最大的不同就在于它们的请求body了。

下面是请求方法的body讨论：
1. get的请求body
一般比较少用
2. post/put/patch的请求body
可以上传的数据类型有下列几种
   - 表单发送 FormUrlEncoded ( Field FieldMap )
   - 多部分发送 Multipart ( Part PartMap )
<br>

#### url相关
-----
Path Query QueryMap QueryName  Url

Streaming 采用分块传输的方式传输大文件，就是流模式取代缓存模式，通常在header中添加`Transfer-Encoding: chunked`信息，Http默认采用的是缓存模式，通常在header中添加`Content-Length: 3495`

### *Retrofit 转化器、适配器*{:.header3-font}

#### Converter
---------
```java
public interface Converter<F, T> {
  T convert(F value) throws IOException;

 
  abstract class Factory {
    
    //响应的body转换
    public @Nullable Converter<ResponseBody, ?> responseBodyConverter(Type type,
        Annotation[] annotations, Retrofit retrofit) {
      return null;
    }

    //请求的body转换
    public @Nullable Converter<?, RequestBody> requestBodyConverter(Type type,
        Annotation[] parameterAnnotations, Annotation[] methodAnnotations, Retrofit retrofit) {
      return null;
    }

    //用于处理url
    public @Nullable Converter<?, String> stringConverter(Type type, Annotation[] annotations,
        Retrofit retrofit) {
      return null;
    }

  }
}
```
&emsp;&emsp;利用工厂模式创建Converter，通过override Converter的convert方法，从而达到数据的类型的转换。
网络数据交互发展历史可以看下面
```
SOP:HTTP+XML(过去)
REST:HTTP+JSON(现在)
gRPC+protobuf(未来) ​​​​
```
服务端可以给我们传xml、json、protobuf等格式的数据，但是我们希望被映射成对象，更加的便于我们理解和操作对象。这个时候我们可以自己写一些convert，将xml/json/protobuf转换成对象。

来看个例子：
```java
interface Service {
    @POST("/") Call<AnImplementation> anImplementation(@Body AnImplementation impl);
    @POST("/") Call<AnInterface> anInterface(@Body AnInterface impl);
}

public final class GsonConverterFactory extends Converter.Factory {
  
 @Override
    public Converter<ResponseBody, ?> responseBodyConverter(Type type, Annotation[] annotations,
                                                            Retrofit retrofit) {
        TypeAdapter<?> adapter = gson.getAdapter(TypeToken.get(type));
        return new GsonResponseBodyConverter<>(gson, adapter);
    }
}
final class GsonResponseBodyConverter<T> implements Converter<ResponseBody, T> {
  private final Gson gson;
  private final TypeAdapter<T> adapter;

  GsonResponseBodyConverter(Gson gson, TypeAdapter<T> adapter) {
    this.gson = gson;
    this.adapter = adapter;
  }

  @Override public T convert(ResponseBody value) throws IOException {
    JsonReader jsonReader = gson.newJsonReader(value.charStream());
    try {
      return adapter.read(jsonReader);
    } finally {
      value.close();
    }
  }
}
```
当我们定义了Response的类型为AnImplementation/AnInterface时，通过Gson库将服务端返回的json数据转换成AnImplementation/AnInterface对象


```protobuf
package retrofit2.converter.protobuf;

option java_package = "retrofit2.converter.protobuf";
option java_outer_classname = "PhoneProtos";

message Phone {
  optional string number = 1;

  extensions 2;
}

extend Phone {
  optional bool voicemail = 2;
}

```

```java
 interface Service {
    @GET("/") Call<Phone> get();
    @POST("/") Call<Phone> post(@Body Phone impl);
    @GET("/") Call<String> wrongClass();
    @GET("/") Call<List<String>> wrongType();
  }
  interface ServiceWithRegistry {
    @GET("/") Call<Phone> get();
  }

public final class ProtoConverterFactory extends Converter.Factory {
    @Override
  public Converter<ResponseBody, ?> responseBodyConverter(Type type, Annotation[] annotations,
      Retrofit retrofit) {
    if (!(type instanceof Class<?>)) {
      return null;
    }
    Class<?> c = (Class<?>) type;
    if (!MessageLite.class.isAssignableFrom(c)) {
      return null;
    }

    Parser<MessageLite> parser;
    try {
      Method method = c.getDeclaredMethod("parser");
      //noinspection unchecked
      parser = (Parser<MessageLite>) method.invoke(null);
    } catch (InvocationTargetException e) {
      throw new RuntimeException(e.getCause());
    } catch (NoSuchMethodException | IllegalAccessException ignored) {
      // If the method is missing, fall back to original static field for pre-3.0 support.
      try {
        Field field = c.getDeclaredField("PARSER");
        //noinspection unchecked
        parser = (Parser<MessageLite>) field.get(null);
      } catch (NoSuchFieldException | IllegalAccessException e) {
        throw new IllegalArgumentException("Found a protobuf message but "
            + c.getName()
            + " had no parser() method or PARSER field.");
      }
    }
    return new ProtoResponseBodyConverter<>(parser, registry);
  }
}


final class ProtoResponseBodyConverter<T extends MessageLite>
    implements Converter<ResponseBody, T> {
  private final Parser<T> parser;
  private final @Nullable ExtensionRegistryLite registry;

  ProtoResponseBodyConverter(Parser<T> parser, @Nullable ExtensionRegistryLite registry) {
    this.parser = parser;
    this.registry = registry;
  }

  @Override public T convert(ResponseBody value) throws IOException {
    try {
      return parser.parseFrom(value.byteStream(), registry);
    } catch (InvalidProtocolBufferException e) {
      throw new RuntimeException(e); // Despite extending IOException, this is data mismatch.
    } finally {
      value.close();
    }
  }
}
```

#### Adapter
------
```java
public interface CallAdapter<R, T> {
 
  Type responseType();

  T adapt(Call<R> call);

  
  abstract class Factory {
    
    public abstract @Nullable CallAdapter<?, ?> get(Type returnType, Annotation[] annotations,
        Retrofit retrofit);
  }
}
```
通过抽象工程模式创建Adapter。然后将Call适配成其他类型。