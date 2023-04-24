---
layout: post
title: Android | Binder家族
description: 都是Binder惹的祸
tag:
- android
- process-thread
---
* TOC
{:toc}

这一篇我们来讲讲Binder，为什么Android提供给应用层的API大量使用Binder实现，知乎有讨论[看这里](https://www.zhihu.com/question/39440766)，基于binder实现的有AIDL、Messenger、ContentProvider。

# AIDL
首先我们来了解一下AIDL，它是一种DSL，用接口化的形式为我们省去了很多模板代码，举个例子。

IMyAidlInterface.aidl
{:.filename}
```java
interface IMyAidlInterface {
    /**
     * Demonstrates some basic types that you can use as parameters
     * and return values in AIDL.
     */
    int basicTypes(int anInt, long aLong, boolean aBoolean, float aFloat,
            double aDouble, String aString);
}
```
上面是用AIDL编写的代码，经过编译会自动为我们生成这么几个类IMyAidlInterface(接口声明类)、IMyAidlInterface.Stub(接口的实现类)、IMyAidlInterface.Stub.Proxy(接口实现类的代理类，用于远程代理，本地不用代理)或者自己手动抄一下作业实现这样的几个模板代码,  下面是我自己手写的Binder模板代码看起来比较简洁。

IMyAidlInterface.java
{:.filename}
```java
public interface IMyAidlInterface extends IInterface {
    public int basicTypes(int anInt, long aLong, boolean aBoolean, float aFloat, double aDouble, java.lang.String aString) throws RemoteException;
}
```
IMyAidlInterface类用来定义一系列rpc方法，供调用者使用，而具体的实现将交由BinderEntry，我们再来往下看看。

BinderEntry.java/BinderShadow.java
{:.filename}
```java
/*真正的Binder
*/
public class BinderEntry extends Binder implements IMyAidlInterface{

    @Override
    protected boolean onTransact(int code, @NonNull Parcel data, @Nullable Parcel reply, int flags) throws RemoteException {
        switch (code) {
            case TRANSACTION_basicTypes: {
                Log.d("cjf", "entry TRANSACTION_basicTypes");
                data.enforceInterface(DESCRIPTOR);
                int _arg0;
                _arg0 = data.readInt();
                long _arg1;
                _arg1 = data.readLong();
                boolean _arg2;
                _arg2 = (0 != data.readInt());
                float _arg3;
                _arg3 = data.readFloat();
                double _arg4;
                _arg4 = data.readDouble();
                java.lang.String _arg5;
                _arg5 = data.readString();
                int _result = this.basicTypes(_arg0, _arg1, _arg2, _arg3, _arg4, _arg5);
                reply.writeNoException();
                reply.writeInt(_result);
                return true;
            }
            default:
                Log.d("cjf", "entry code:" + code);
                break;


        }
        return super.onTransact(code, data, reply, flags);
    }

    public void basicTypes(int anInt, long aLong, boolean aBoolean, float aFloat, double aDouble, java.lang.String aString) {
        Log.d("cjf", "entry basicTypes:" + anInt + " " + aLong + " " + aBoolean + " " + aFloat + " " + aDouble + " " + aString);
    }
    @Override
    public IBinder asBinder() {
        return this;
    }
}
/*binder的代理类
*/
public class BinderShadow implements IMyAidlInterface {
    private IBinder mRemote;

    public BinderShadow(IBinder mRemote) {
        this.mRemote = mRemote;
    }

    public int basicTypes(int anInt, long aLong, boolean aBoolean, float aFloat, double aDouble, java.lang.String aString) throws RemoteException {
        Log.d("cjf", "shadow basicTypes:" + anInt + " " + aLong + " " + aBoolean + " " + aFloat + " " + aDouble + " " + aString);
        android.os.Parcel _data = android.os.Parcel.obtain();
        android.os.Parcel _reply = android.os.Parcel.obtain();
        int _result;
        try {
            _data.writeInterfaceToken(Constance.DESCRIPTOR);
            _data.writeInt(anInt);
            _data.writeLong(aLong);
            _data.writeInt(((aBoolean)?(1):(0)));
            _data.writeFloat(aFloat);
            _data.writeDouble(aDouble);
            _data.writeString(aString);
            boolean status = mRemote.transact(TRANSACTION_basicTypes, _data, _reply, 0);
            Log.d("cjf","shadow status:"+status);
            _reply.readException();
            _result = _reply.readInt();
        } finally {
            _reply.recycle();
            _data.recycle();
        }
        return _result;
    }
    @Override
    public IBinder asBinder() {
        return mRemote;
    }
}
```
当客户端调用本地服务取到的是BinderEntry，BinderEntry是basicTypes接口真正的实现类，直接调用调用接口的实现类。如果是调用远程服务取到的是BinderShadow(代理BinderEntry)，BinderShadow将负责数据写入到_data(Parcel对象)，从_reply(Parcel对象)读取数据，通过调用IBinder#transact方法将_data传到远程服务，远程服务会回调onTransact方法，将数据写入到_reply返回给客户端。

这里要说一下IBinder(实现类Binder)的queryLocalInterface方法，该方法可以查询到该Binder服务对应的IInterface，像AMS对应的IActivityManager，PMS对应的IPackageManager，可以通过hook该方法拿到IInterface对象，然后使用java动态代理接口，拦截客户端发往framework的数据，篡改framework返回的数据，做一些不能做的事情。

# Messenger

看完上面的代码我们就知道了，其实AIDL是用来声明rpc接口的代码，和Retrofit通过注解声明接口一样，不同的是Retrofit是通过接口的动态代理实现具体的远程调用，AIDL则是通过编译时期生成静态代理。了解AIDL，那么我们不禁会问有没有一种远程通信是基于事件的，可以被动调用，这就让我们引出了下面的主角Messenger信使。没用过的可以看这里的代码[StartActivity](https://github.com/electrolyteJ/Spacecraft/blob/master/components/template/src/main/java/com/hawksjamesf/template/StartActivity.java)、[MessengerService](https://github.com/electrolyteJ/Spacecraft/blob/master/components/template/src/main/java/com/hawksjamesf/template/MessengerService.java)，接下来我们讲讲其本质是什么。


```java
public final class Messenger implements Parcelable {
   private final IMessenger mTarget;
    ...
    public Messenger(Handler target) {
        mTarget = target.getIMessenger();
    }
    ...
}

public class Handler {
    ...
      final IMessenger getIMessenger() {
        synchronized (mQueue) {
            if (mMessenger != null) {
                return mMessenger;
            }
            mMessenger = new MessengerImpl();
            return mMessenger;
        }
    }
    ...
    private final class MessengerImpl extends IMessenger.Stub {
        public void send(Message msg) {
            msg.sendingUid = Binder.getCallingUid();
            Handler.this.sendMessage(msg);
        }
    }
    ...
}
```
首先我们需要在服务端初始化一个Messenger，在注入的Handler对象target中，间接初始化了一个服务Binder(IMessenger)，该服务接收来自客户端发送的message然后进入生产者消费者模型中。也就是说每个Messenger对象都会有一个属于自己的服务Binder(IMessenger),客户端会持有一个Messenger，服务端也会持有一个，当他们彼此拥有对方这样就能组成双通道通信,但是这里有个前提是使用`Messenger(Handler target)`构造器，而不是`Messenger(IBinder target)`构造器，`Messenger(IBinder target)`是为了让我们获取服务Binder而不是构造属于自己的Binder。
```java
public final class Messenger implements Parcelable {
    private final IMessenger mTarget;
    ...
    public IBinder getBinder() {
        return mTarget.asBinder();
    }
    ...
    public Messenger(IBinder target) {
        mTarget = IMessenger.Stub.asInterface(target);
    }
    ...
}
```

这里在总结一下，当客户端和服务端彼此“牵手”成功，客户端获取了服务Binder然后将自己的Messenger发送给对方，这样双方就能双向通信。

# Binder通信原理

binder通信开始于`IBinder#transact` 到达于 `Binder#onTransact`,中间经历了应用态到内核态的切换，在探究binder通信原理之前我们有必要知道caller如何获取到calle的binder。

在android framework层有一个重要角色，binder服务中心ServiceManager，ServiceManager是一个守护进程，随手机启动时启动，其提供了getService与addService接口。当Activity所在进程与Service所在进程创建连接，会将Service所在进程的binder对象传递给Activity所在进程，得到binder对象之后调用transact函数开始传递数据。

```java
BinderProxy#transactNative -> BpBinder#transact -> 
IPCThreadState#transact -> IPCThreadState#waitForResponse -> IPCThreadState#talkWithDriver -> IPCThreadState#executeCommand --BR_TRANSACTION-->  
BBinder#transact -> BBinder#onTransact ->
Binder#onTransact
```
在应用进程初始化时，会初始化binder线程池(最多15个)并且创建名为binder_1的binder线程，该线程永不停止，如果是mediaserver、servicemanager那么主线程就是binder线程。除此之外还会mmap 驱动文件/dev/binder，相比较于普通的io，mmap只需一次读写。

在talkWithDriver时，IPCThreadState通过ioctl系统调用将bwr.write_buffer数据写入kernel space，并且从bwr.read_buffer能读取到远程的数据，从而完成跨进程通讯。