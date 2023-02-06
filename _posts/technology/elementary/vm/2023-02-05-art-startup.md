---
layout: post
title: Android ART 启动
description:  Android Runtime
tag:
- elementary/vm
---

* TOC
{:toc}

## 预先知识

art工程结构

- runtime:执行机器码(oat文件)或者字节码(dex文件)的虚拟机，支持AOT编译与JIT编译
- dex2oat: 字节码转机器码
- oatdump/dexdump：oat(elf格式)与dex文件的dump
- libexfile/libelffile:操作dex文件与elf文件的库
- ...

### framework层的一些角色

AppRuntime/AndroidRuntime 、zygote进程(app_main)

### art的一些角色

Runtime/RuntimeCallbacks、Instrumentation、Thread

ClassRoot映射表

 java类 | cpp类 | 
 --- | --- | 
 "Ljava/lang/ClassLoader;" |mirror::ClassLoader  
 "Ljava/lang/Class;" |mirror::Class  |
 "[Ljava/lang/Class;"|mirror::ObjectArray\<mirror::Class\>
 "Ljava/lang/DexCache;"|mirror::DexCache
 "Ljava/lang/reflect/Field;"|mirror::Field
 "Ljava/lang/reflect/Method;"|mirror::Method
 "Ljava/lang/ClassLoader;"|mirror::ClassLoader
 ...|...
 
 
### oat文件读取流程

dex class --index--> oat class -->oat method/oat field --(begin_+code_offset_)--> native code
1. ClassAccessor:从dexfile文件读class成员数据ClassAccessor::Method与 ClassAccessor::Field
2. OatFile OatHeader OatClass  OatMethod
3. ClassLinker、ArtMethod(java类成员函数)、ArtField(java类成员变量)


## AppRuntime预热

app_main.cpp
```
class AppRuntime : public AndroidRuntime{
    ...
public:
    virtual void onVmCreated(JNIEnv* env){
    ...
    }
    virtual void onStarted(){
    ...
    }
    virtual void onZygoteInit(){
    ...
    }
    virtual void onExit(int code){
    ...
    }
}

int main(int argc, char* const argv[])
{
    ...
    AppRuntime runtime(argv[0], computeArgBlockSize(argc, argv));
    ...
    (zygote) {
        runtime.start("com.android.internal.os.ZygoteInit", args, zygote);
    } else if (className) {
        runtime.start("com.android.internal.os.RuntimeInit", args, zygote);
    } else {
        ...
    }
    ...
}
```
zygote进程启动时会预加载AppRuntime/AndroidRuntime，这样确保了应用进程启动时资源提前加载(由于应用进程被父进程zygote fork出来，所以资源会继承到子进程)。AppRuntime的onVmCreated、onStarted、onZygoteInit、onExit分别是其生命周期。

AndroidRuntime#start方法
1. 先startVm
2. 然后回调AndroidRuntime生命周期onVmCreated
3. 最后启动java类(RuntimeInit或者ZygoteInit)入口函数main并且回调其他生命周期函数(onStarted或者onZygoteInit)

```
    ...
    /* start the virtual machine */
    JniInvocation jni_invocation;
    jni_invocation.Init(NULL);
    JNIEnv* env;
    if (startVm(&mJavaVM, &env, zygote) != 0) {
        return;
    }
    onVmCreated(env);
    ...
    //启动入口函数main
    jmethodID startMeth = env->GetStaticMethodID(startClass, "main",
    ...
```

如果启动的是应用进程则会触发RuntimeInit.java类的mian入口函数执行，且回调生命周期onStarted；如果启动的是zygote进程且预热AppRuntime则会触发ZygoteInit.java类的main入口函数执行，且回调生命周期onZygoteInit。

## 1. AndroidRuntime#startVm
1. 资源预加载：系统属性加载
2. 类预加载:JDK加载
3. 创建vm(JNI_CreateJavaVM):创建并且启动Runtime，然后调用GetJniEnv与GetJavaVM获取jni env指针与java vm指针且保存到全局p_env与p_vm。

libandroid_runtime.so中的AndroidRuntime通过dlopen/dlsym函数调用libart.so的导出函数JNI_CreateJavaVM。使用这种动态调用的方式将虚拟机的libart.so/libdex.so与框架解耦，且能自由切换art与dalvik。除此之外虚拟机还有两个导出行数JNI_GetCreatedJavaVMs、JNI_GetDefaultJavaVMInitArgs。

让我们来看看JNI_CreateJavaVM函数。

runtime/jni/java_vm_ext.cc
```
extern "C" jint JNI_CreateJavaVM(JavaVM** p_vm, JNIEnv** p_env, void* vm_args) {
  ...
//1. 构造Runtime对象
  bool ignore_unrecognized = args->ignoreUnrecognized;
  if (!Runtime::Create(options, ignore_unrecognized)) {
    return JNI_ERR;
  }

  // Initialize native loader. This step makes sure we have
  // everything set up before we start using JNI.
  android::InitializeNativeLoader();
//2. 启动Runtime
  Runtime* runtime = Runtime::Current();
  bool started = runtime->Start();
  if (!started) {
    delete Thread::Current()->GetJniEnv();
    delete runtime->GetJavaVM();
    LOG(WARNING) << "CreateJavaVM failed";
    return JNI_ERR;
  }
//3. jni env指针 与java vm
  *p_env = Thread::Current()->GetJniEnv();
  *p_vm = runtime->GetJavaVM();
  return JNI_OK;
}
```
JNI_CreateJavaVM代码很简单，创建并启动Runtime且将jni运行环境与vm实例全局保存。

### Runtime#Create and Start

创建Runtime对象时，调用其构造器会初始化大量成员变量，其中有heap_(gc::Heap对象)，java_vm_(JavaVMExt::Create对象,外部调用者使用GetJavaVM函数即可获取到java_vm_)等。

## 2. Java主线程的入口方法：ZygoteInit#main

```cpp
1.找启动类 slashClassName为com.android.internal.os.ZygoteInit.java
jclass startClass = env->FindClass(slashClassName);
2.找启动入口
jmethodID startMeth = env->GetStaticMethodID(startClass, "main","([Ljava/lang/String;)V");
3.调用启动入口
env->CallStaticVoidMethod(startClass, startMeth, strArray);
4. java代码执行完成之后虚拟机detach当前线程(cpp startVm、startReg代码的线程，cpp主线程) 与 销毁虚拟机
mJavaVM->DetachCurrentThread()
mJavaVM->DestroyJavaVM()
```
从上面启动java主线程入口方法，流程中关键函数为FindClass、GetStaticMethodID、CallStaticVoidMethod，其为JNIEnvExt类的成员函数,这些函数是JNIEnvExt继承其基类JNIEnv类，JNIEnv像一个jni函数的代理者，代理了JNINativeInterface。

libnativehelper/include_jni/jni.h
```cpp
...
typedef _JNIEnv JNIEnv;
...
struct _JNIEnv {
    /* do not rename this; it does not seem to be entirely opaque */
    const struct JNINativeInterface* functions;
    ...
    jclass FindClass(const char* name)
    { return functions->FindClass(this, name); }
    ...

}
```
JNINativeInterface对象指针在JNIEnvExt构造对象的时候被初始化，其实现在art/runtime/jni/jni_internal.cc中。
```cpp
template <bool kEnableIndexIds>
class JNI {
  static jclass FindClass(JNIEnv* env, const char* name) {
    CHECK_NON_NULL_ARGUMENT(name);
    Runtime* runtime = Runtime::Current();
    ClassLinker* class_linker = runtime->GetClassLinker();
    std::string descriptor(NormalizeJniClassDescriptor(name));
    ScopedObjectAccess soa(env);
    ObjPtr<mirror::Class> c = nullptr;
    if (runtime->IsStarted()) {
      StackHandleScope<1> hs(soa.Self());
      Handle<mirror::ClassLoader> class_loader(hs.NewHandle(GetClassLoader<kEnableIndexIds>(soa)));
      c = class_linker->FindClass(soa.Self(), descriptor.c_str(), class_loader);
    } else {
      c = class_linker->FindSystemClass(soa.Self(), descriptor.c_str());
    }
    return soa.AddLocalReference<jclass>(c);
  }
  ...
}
...
template<bool kEnableIndexIds>
struct JniNativeInterfaceFunctions {
  using JNIImpl = JNI<kEnableIndexIds>;
  static constexpr JNINativeInterface gJniNativeInterface = {
    ...
     JNIImpl::FindClass,
    ...
  }
}
```
从分析上面调用流程我们能知道jni.h导出函数的实现类在art/runtime/jni/jni_internal.cc文件中的JNI类。

接下来我们就展开看看这几个函数的执行。

### 找启动类:FindClass

```cpp
class JNI {
 public:
    ...
  static jclass FindClass(JNIEnv* env, const char* name) {
    CHECK_NON_NULL_ARGUMENT(name);
    Runtime* runtime = Runtime::Current();
    ClassLinker* class_linker = runtime->GetClassLinker();
    std::string descriptor(NormalizeJniClassDescriptor(name));
    ScopedObjectAccess soa(env);
    ObjPtr<mirror::Class> c = nullptr;
    if (runtime->IsStarted()) {
      StackHandleScope<1> hs(soa.Self());
      Handle<mirror::ClassLoader> class_loader(hs.NewHandle(GetClassLoader<kEnableIndexIds>(soa)));
      c = class_linker->FindClass(soa.Self(), descriptor.c_str(), class_loader);
    } else {
      c = class_linker->FindSystemClass(soa.Self(), descriptor.c_str());
    }
    return soa.AddLocalReference<jclass>(c);
  }
  ...
 }
```
Runtime对象中ClassLinker对象是在构造Runtime对象时初始化的
```cpp
  if (UNLIKELY(IsAotCompiler())) {
    class_linker_ = new AotClassLinker(intern_table_);
  } else {
    class_linker_ = new ClassLinker(
        intern_table_,
        runtime_options.GetOrDefault(Opt::FastClassNotFoundException));
  } 
```
IsAotCompiler表示当前使用dex2oat完成AOT编译，通常是在PMS进行apk安装时使用的编译，如果启动的进程为zygote进程或者应用进程，运行时仅可采用jit编译，所以我们继续分析ClassLinker类的FindClass函数。

art/runtime/class_linker.cc
```cpp
ObjPtr<mirror::Class> ClassLinker::FindClass(Thread* self,
                                             const char* descriptor,
                                             Handle<mirror::ClassLoader> class_loader) {
  ...
  self->AssertNoPendingException();
  self->PoisonObjectPointers();  // For DefineClass, CreateArrayClass, etc...
  //基本类型
  if (descriptor[1] == '\0') {
    // only the descriptors of primitive types should be 1 character long, also avoid class lookup
    // for primitive classes that aren't backed by dex files.
    return FindPrimitiveClass(descriptor[0]);
  }
  const size_t hash = ComputeModifiedUtf8Hash(descriptor);
  // Find the class in the loaded classes table.
  ObjPtr<mirror::Class> klass = LookupClass(self, descriptor, hash, class_loader.Get());
  //已经被load过的类
  if (klass != nullptr) {
    return EnsureResolved(self, descriptor, klass);
  }
  //加载对象，从boot class loader
  // Class is not yet loaded.
  if (descriptor[0] != '[' && class_loader == nullptr) {
    // Non-array class and the boot class loader, search the boot class path.
    ClassPathEntry pair = FindInClassPath(descriptor, hash, boot_class_path_);
    if (pair.second != nullptr) {
      return DefineClass(self,
                         descriptor,
                         hash,
                         ScopedNullHandle<mirror::ClassLoader>(),
                         *pair.first,
                         *pair.second);
    } else {
      ...
      //加载失败
      return nullptr;
    }
  }
  ObjPtr<mirror::Class> result_ptr;
  bool descriptor_equals;
  //加载数组
  if (descriptor[0] == '[') {
    result_ptr = CreateArrayClass(self, descriptor, hash, class_loader);
    ...
    descriptor_equals = true;
  } else {
    ScopedObjectAccessUnchecked soa(self);
    //从base dex class loader加载
    bool known_hierarchy =
        FindClassInBaseDexClassLoader(soa, self, descriptor, hash, class_loader, &result_ptr);
    if (result_ptr != nullptr) {
      ...
      descriptor_equals = true;
    } else if (!self->IsExceptionPending()) {
      ...
    } else {
      DCHECK(!MatchesDexFileCaughtExceptions(self->GetException(), this));
    }
  }
  ...

  // Try to insert the class to the class table, checking for mismatch.
  ObjPtr<mirror::Class> old;
  {
    WriterMutexLock mu(self, *Locks::classlinker_classes_lock_);
    ClassTable* const class_table = InsertClassTableForClassLoader(class_loader.Get());
    old = class_table->Lookup(descriptor, hash);
    if (old == nullptr) {
      old = result_ptr;  // For the comparison below, after releasing the lock.
      if (descriptor_equals) {
        class_table->InsertWithHash(result_ptr, hash);
        WriteBarrier::ForEveryFieldWrite(class_loader.Get());
      }  // else throw below, after releasing the lock.
    }
  }
  if (UNLIKELY(old != result_ptr)) {
    // Return `old` (even if `!descriptor_equals`) to mimic the RI behavior for parallel
    // capable class loaders.  (All class loaders are considered parallel capable on Android.)
    ObjPtr<mirror::Class> loader_class = class_loader->GetClass();
    ...
    return EnsureResolved(self, descriptor, old);
  }
  ...
  // Success.
  return result_ptr;
}
```
FindClass函数查找类路径
- 基本类型
- 已经被load过类的缓冲区
- 加载对象，从boot class loader
- 加载数组
- 从base dex class loader加载


我们从boot class loader加载的路径进一步分析DefineClass函数。

```cpp
ObjPtr<mirror::Class> ClassLinker::DefineClass(Thread* self,
                                               const char* descriptor,
                                               size_t hash,
                                               Handle<mirror::ClassLoader> class_loader,
                                               const DexFile& dex_file,
                                               const dex::ClassDef& dex_class_def) {
  ScopedDefiningClass sdc(self);
  StackHandleScope<3> hs(self);
  metrics::AutoTimer timer{GetMetrics()->ClassLoadingTotalTime()};
  auto klass = hs.NewHandle<mirror::Class>(nullptr);

  // Load the class from the dex file.
  if (UNLIKELY(!init_done_)) {
    // finish up init of hand crafted class_roots_
    if (strcmp(descriptor, "Ljava/lang/Object;") == 0) {
      klass.Assign(GetClassRoot<mirror::Object>(this));
    } else if (strcmp(descriptor, "Ljava/lang/Class;") == 0) {
      klass.Assign(GetClassRoot<mirror::Class>(this));
    } else if (strcmp(descriptor, "Ljava/lang/String;") == 0) {
      klass.Assign(GetClassRoot<mirror::String>(this));
    } else if (strcmp(descriptor, "Ljava/lang/ref/Reference;") == 0) {
      klass.Assign(GetClassRoot<mirror::Reference>(this));
    } else if (strcmp(descriptor, "Ljava/lang/DexCache;") == 0) {
      klass.Assign(GetClassRoot<mirror::DexCache>(this));
    } else if (strcmp(descriptor, "Ldalvik/system/ClassExt;") == 0) {
      klass.Assign(GetClassRoot<mirror::ClassExt>(this));
    }
  }
  ...

  // Get the real dex file. This will return the input if there aren't any callbacks or they do
  // nothing.
  DexFile const* new_dex_file = nullptr;
  dex::ClassDef const* new_class_def = nullptr;
  // TODO We should ideally figure out some way to move this after we get a lock on the klass so it
  // will only be called once.
  Runtime::Current()->GetRuntimeCallbacks()->ClassPreDefine(descriptor,
                                                            klass,
                                                            class_loader,
                                                            dex_file,
                                                            dex_class_def,
                                                            &new_dex_file,
                                                            &new_class_def);
  ...
  klass->SetDexCache(dex_cache);
  SetupClass(*new_dex_file, *new_class_def, klass, class_loader.Get());

  ...

  ObjectLock<mirror::Class> lock(self, klass);
  klass->SetClinitThreadId(self->GetTid());
  // Make sure we have a valid empty iftable even if there are errors.
  klass->SetIfTable(GetClassRoot<mirror::Object>(this)->GetIfTable());

  // Add the newly loaded class to the loaded classes table.
  ObjPtr<mirror::Class> existing = InsertClass(descriptor, klass.Get(), hash);
  if (existing != nullptr) {
    // We failed to insert because we raced with another thread. Calling EnsureResolved may cause
    // this thread to block.
    return sdc.Finish(EnsureResolved(self, descriptor, existing));
  }
  // Load the fields and other things after we are inserted in the table. This is so that we don't
  // end up allocating unfree-able linear alloc resources and then lose the race condition. The
  // other reason is that the field roots are only visited from the class table. So we need to be
  // inserted before we allocate / fill in these fields.
  LoadClass(self, *new_dex_file, *new_class_def, klass);
  ...
  // Finish loading (if necessary) by finding parents
  CHECK(!klass->IsLoaded());
  if (!LoadSuperAndInterfaces(klass, *new_dex_file)) {
    // Loading failed.
    if (!klass->IsErroneous()) {
      mirror::Class::SetStatus(klass, ClassStatus::kErrorUnresolved, self);
    }
    return sdc.Finish(nullptr);
  }
  CHECK(klass->IsLoaded());

  // At this point the class is loaded. Publish a ClassLoad event.
  // Note: this may be a temporary class. It is a listener's responsibility to handle this.
  Runtime::Current()->GetRuntimeCallbacks()->ClassLoad(klass);

  // Link the class (if necessary)
  CHECK(!klass->IsResolved());
  // TODO: Use fast jobjects?
  auto interfaces = hs.NewHandle<mirror::ObjectArray<mirror::Class>>(nullptr);

  MutableHandle<mirror::Class> h_new_class = hs.NewHandle<mirror::Class>(nullptr);
  if (!LinkClass(self, descriptor, klass, interfaces, &h_new_class)) {
    // Linking failed.
    if (!klass->IsErroneous()) {
      mirror::Class::SetStatus(klass, ClassStatus::kErrorUnresolved, self);
    }
    return sdc.Finish(nullptr);
  }
  self->AssertNoPendingException();
  CHECK(h_new_class != nullptr) << descriptor;
  CHECK(h_new_class->IsResolved()) << descriptor << " " << h_new_class->GetStatus();

  // Instrumentation may have updated entrypoints for all methods of all
  // classes. However it could not update methods of this class while we
  // were loading it. Now the class is resolved, we can update entrypoints
  // as required by instrumentation.
  if (Runtime::Current()->GetInstrumentation()->AreExitStubsInstalled()) {
    // We must be in the kRunnable state to prevent instrumentation from
    // suspending all threads to update entrypoints while we are doing it
    // for this class.
    DCHECK_EQ(self->GetState(), ThreadState::kRunnable);
    Runtime::Current()->GetInstrumentation()->InstallStubsForClass(h_new_class.Get());
  }

  /*
   * We send CLASS_PREPARE events to the debugger from here.  The
   * definition of "preparation" is creating the static fields for a
   * class and initializing them to the standard default values, but not
   * executing any code (that comes later, during "initialization").
   *
   * We did the static preparation in LinkClass.
   *
   * The class has been prepared and resolved but possibly not yet verified
   * at this point.
   */
  Runtime::Current()->GetRuntimeCallbacks()->ClassPrepare(klass, h_new_class);

  // Notify native debugger of the new class and its layout.
  jit::Jit::NewTypeLoadedIfUsingJit(h_new_class.Get());

  return sdc.Finish(h_new_class);
}
```

- LoadClass: 从dex file加载class成员数据method、field
- LinkClass: 链接class

### 找启动入口:GetStaticMethodID

`JNIEnv::CallStaticVoidMethod --> FindMethodID --> FindMethodJNI  --> Class::FindClassMethod`

### 调用启动入口:CallStaticVoidMethod

函数调用链
`JNIEnv::CallStaticVoidMethod --> JNIImpl::CallStaticVoidMethod -->InvokeWithVarArgs --> ArtMethod::Invoke`

art/runtime/art_method.cc
```cpp
void ArtMethod::Invoke(Thread* self, uint32_t* args, uint32_t args_size, JValue* result,
                       const char* shorty) {
  ...

  // Push a transition back into managed code onto the linked list in thread.
  ManagedStack fragment;
  self->PushManagedStackFragment(&fragment);

  Runtime* runtime = Runtime::Current();
  // Call the invoke stub, passing everything as arguments.
  // If the runtime is not yet started or it is required by the debugger, then perform the
  // Invocation by the interpreter, explicitly forcing interpretation over JIT to prevent
  // cycling around the various JIT/Interpreter methods that handle method invocation.
  if (UNLIKELY(!runtime->IsStarted() ||
               (self->IsForceInterpreter() && !IsNative() && !IsProxyMethod() && IsInvokable()))) {
    //解释器执行
    if (IsStatic()) {
      art::interpreter::EnterInterpreterFromInvoke(
          self, this, nullptr, args, result, /*stay_in_interpreter=*/ true);
    } else {
      mirror::Object* receiver =
          reinterpret_cast<StackReference<mirror::Object>*>(&args[0])->AsMirrorPtr();
      art::interpreter::EnterInterpreterFromInvoke(
          self, this, receiver, args + 1, result, /*stay_in_interpreter=*/ true);
    }
  } else {
    ...
    constexpr bool kLogInvocationStartAndReturn = false;
    bool have_quick_code = GetEntryPointFromQuickCompiledCode() != nullptr;
    if (LIKELY(have_quick_code)) {
      //执行机器码
      ...
      if (!IsStatic()) {
        (*art_quick_invoke_stub)(this, args, args_size, self, result, shorty);
      } else {
        (*art_quick_invoke_static_stub)(this, args, args_size, self, result, shorty);
      }
      if (UNLIKELY(self->GetException() == Thread::GetDeoptimizationException())) {
        // Unusual case where we were running generated code and an
        // exception was thrown to force the activations to be removed from the
        // stack. Continue execution in the interpreter.
        self->DeoptimizeWithDeoptimizationException(result);
      }
      ...
    } else {
      ...
    }
  }

  // Pop transition.
  self->PopManagedStackFragment(fragment);
}
```

函数调用的时候既可以被解释器执行也可以直接执行其机器码，这取决于art是否为解释器与函数的类型。对于启动入口函数main，我们姑且认为它是执行其机器码。art_quick_invoke_static_stub函数是执行静态函数main的接下逻辑处理，其调用链`art_quick_invoke_static_stub-->quick_invoke_reg_setup-->art_quick_invoke_stub_internal`,art_quick_invoke_stub_internal函数是用汇编编写在art/runtime/arch/arm/quick_entrypoints_arm.S

```armasm
    /*
     * Quick invocation stub internal.
     * On entry:
     *   r0 = method pointer
     *   r1 = argument array or null for no argument methods
     *   r2 = size of argument array in bytes
     *   r3 = (managed) thread pointer
     *   [sp] = JValue* result
     *   [sp + 4] = result_in_float
     *   [sp + 8] = core register argument array
     *   [sp + 12] = fp register argument array
     *  +-------------------------+
     *  | uint32_t* fp_reg_args   |
     *  | uint32_t* core_reg_args |
     *  |   result_in_float       | <- Caller frame
     *  |   Jvalue* result        |
     *  +-------------------------+
     *  |          lr             |
     *  |          r11            |
     *  |          r9             |
     *  |          r4             | <- r11
     *  +-------------------------+
     *  | uint32_t out[n-1]       |
     *  |    :      :             |        Outs
     *  | uint32_t out[0]         |
     *  | StackRef<ArtMethod>     | <- SP  value=null
     *  +-------------------------+
     */
ENTRY art_quick_invoke_stub_internal
    SPILL_ALL_CALLEE_SAVE_GPRS             @ spill regs (9)
    mov    r11, sp                         @ save the stack pointer
    .cfi_def_cfa_register r11

    mov    r9, r3                          @ move managed thread pointer into r9

    add    r4, r2, #4                      @ create space for method pointer in frame
    sub    r4, sp, r4                      @ reserve & align *stack* to 16 bytes: native calling
    and    r4, #0xFFFFFFF0                 @ convention only aligns to 8B, so we have to ensure ART
    mov    sp, r4                          @ 16B alignment ourselves.

    mov    r4, r0                          @ save method*
    add    r0, sp, #4                      @ pass stack pointer + method ptr as dest for memcpy
    bl     memcpy                          @ memcpy (dest, src, bytes)
    mov    ip, #0                          @ set ip to 0
    str    ip, [sp]                        @ store null for method* at bottom of frame

    ldr    ip, [r11, #48]                  @ load fp register argument array pointer
    vldm   ip, {s0-s15}                    @ copy s0 - s15

    ldr    ip, [r11, #44]                  @ load core register argument array pointer
    mov    r0, r4                          @ restore method*
    add    ip, ip, #4                      @ skip r0
    ldm    ip, {r1-r3}                     @ copy r1 - r3

    REFRESH_MARKING_REGISTER

    ldr    ip, [r0, #ART_METHOD_QUICK_CODE_OFFSET_32]  @ get pointer to the code
    blx    ip                              @ call the method

    mov    sp, r11                         @ restore the stack pointer
    .cfi_def_cfa_register sp

    ldr    r4, [sp, #40]                   @ load result_is_float
    ldr    r9, [sp, #36]                   @ load the result pointer
    cmp    r4, #0
    ite    eq
    strdeq r0, [r9]                        @ store r0/r1 into result pointer
    vstrne d0, [r9]                        @ store s0-s1/d0 into result pointer

    pop    {r4, r5, r6, r7, r8, r9, r10, r11, pc}               @ restore spill regs
END art_quick_invoke_stub_internal
```

blx函数用于函数跳转，ip保存了ART_METHOD_QUICK_CODE_OFFSET_32地址，也就是说blx将会调用启动入口函数main的机器码，控制权彻底从cpp层到了java层，ZygoteInit#main中做了一件非常重要的事情fork system server，以便于初始化framework层的各种binder service，比如AMS、PMS，最后会调用native方法nativeZygoteInit回调AndroidRuntime的生命周期onZygoteInit函数。在onZygoteInit函数中会启动binder线程池。这里要展开说一下如果启动的是应用进程，则不会调用ZygoteInit#main,而是调用RuntimeInit#main并且最后回调AndroidRuntime类的onStarted函数。
```cpp
    virtual void onStarted()
    {
        sp<ProcessState> proc = ProcessState::self();
        ALOGV("App process: starting thread pool.\n");
        proc->startThreadPool();

        AndroidRuntime* ar = AndroidRuntime::getRuntime();
        ar->callMain(mClassName, mClass, mArgs);

        IPCThreadState::self()->stopProcess();
        hardware::IPCThreadState::self()->stopProcess();
    }

    virtual void onZygoteInit()
    {
        sp<ProcessState> proc = ProcessState::self();
        ALOGV("App process: starting thread pool.\n");
        proc->startThreadPool();
    }
```
相比较于onZygoteInit函数，onStarted函数不仅会初始化binder线程池，还会启动应用的入口类ActivityThread#main。我们知道ActivityThread#main函数会调用Looper阻塞主线程，作为消息的消费者如果发生程序结束或者异常，那么线程池也会被销毁回收，至此onZygoteInit或者onStarted任意个函数调用都算art都算启动完毕。

关于函数的调用我们这里还有一些没有展开讲，比如解释器执行的代码调用机器码，执行机器码时调用了解释器，解释器调用解释器，感兴趣可以看这一篇文章[Android运行时ART执行类方法的过程分析](https://blog.csdn.net/luoshengyang/article/details/40289405)。


## Android 热修复

基于art实现的热修复，主要是dest artmethod替换src artmethod整个函数的内存(memcpy),阿里提供的技术沉淀[《深入探索Android热修复技术原理》电子书](https://developer.aliyun.com/ebook/296?spm=a2c6h.26392470.ebook-read.2.227f6bbbsIdaen)

## 参考资料

[AndFix](https://github.com/alibaba/AndFix)

[YAHFA](https://github.com/PAGalaxyLab/YAHFA)

[epic](https://github.com/tiann/epic)

