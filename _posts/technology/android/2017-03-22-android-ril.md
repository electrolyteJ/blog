---
layout: post
title: Android | RIL
description: Radio Layer
tag:
- android
- network
---
* TOC
{:toc}
# Framework

手机开机会调用一系列的服务，然后启动PhoneApp应用进程，这个关键入口。如果不清楚PhoneApp类怎么启动的话，可以观看这一篇博客([Android7.0 PhoneApp的启动](http://blog.csdn.net/gaugamela/article/details/52311508))

先不着急看PhoneApp类的代码，我们先来看看这个应用的makefile文件。

/packages/services/Telephony/Android.mk
```makefile
LOCAL_PATH:= $(call my-dir)

# Build the Phone app which includes the emergency dialer. See Contacts
# for the 'other' dialer.
include $(CLEAR_VARS)

phone_common_dir := ../../apps/PhoneCommon

src_dirs := src $(phone_common_dir)/src sip/src
res_dirs := res $(phone_common_dir)/res sip/res

LOCAL_JAVA_LIBRARIES := telephony-common voip-common ims-common
LOCAL_STATIC_JAVA_LIBRARIES := \
        guava

LOCAL_SRC_FILES := $(call all-java-files-under, $(src_dirs))
LOCAL_SRC_FILES += \
        src/com/android/phone/EventLogTags.logtags \
        src/com/android/phone/INetworkQueryService.aidl \
        src/com/android/phone/INetworkQueryServiceCallback.aidl
LOCAL_RESOURCE_DIR := $(addprefix $(LOCAL_PATH)/, $(res_dirs))

LOCAL_AAPT_FLAGS := \
    --auto-add-overlay \
    --extra-packages com.android.phone.common \
    --extra-packages com.android.services.telephony.sip

LOCAL_PACKAGE_NAME := TeleService

LOCAL_CERTIFICATE := platform
LOCAL_PRIVILEGED_MODULE := true

LOCAL_PROGUARD_FLAG_FILES := proguard.flags sip/proguard.flags

include frameworks/base/packages/SettingsLib/common.mk

include $(BUILD_PACKAGE)

# Build the test package
include $(call all-makefiles-under,$(LOCAL_PATH))

```
根据上面的代码，我们可以知道，将会编译出一个TeleService.apk应用。而该应用引用的java库文件为telephony-common、voip-common、ims-common、SettingsLib、guava这四个。其中的guava为google公司的[java开源库](https://github.com/google/guava)，SettingsLib为Settings应用的库文件。这里我们只关注其余三个库文件

telephony-common的makefile文件

/frameworks/opt/telephony/Android.mk
```makefile
# enable this build only when platform library is available
ifeq ($(TARGET_BUILD_JAVA_SUPPORT_LEVEL),platform)

LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_AIDL_INCLUDES := $(LOCAL_PATH)/src/java
LOCAL_SRC_FILES := $(call all-java-files-under, src/java) \
	$(call all-Iaidl-files-under, src/java) \
	$(call all-logtags-files-under, src/java)

LOCAL_JAVA_LIBRARIES := voip-common ims-common
LOCAL_MODULE_TAGS := optional
LOCAL_MODULE := telephony-common

include $(BUILD_JAVA_LIBRARY)

# Include subdirectory makefiles
# ============================================================
include $(call all-makefiles-under,$(LOCAL_PATH))

endif # JAVA platform
```
telephony-common可有引用了voip-common、ims-common两个库文件，该库还是很重要的，整个jar包是framework层提供给application层使用的库文件。比如CarrierConfig应用（可以控制整个平台通信的功能，比如想要去掉彩信功能，就可以通过该应用达到目的）、CellBroadcastReceiver应用（国外使用较广，在特定区域会给用户推送一些新闻资讯）、InCallUI应用（通话界面）、Settings应用（手机设置）、Stk应用（管理sim的一些业务）、SettingsProvider应用(设置数据库)、ContactsProvider应用（联系人数据库）、TelephonyProvider应用（电话短信数据库）、MMsService应用（短信Application层中的服务层）、TeleServicey应用（电话Application层中的服务层）、Telecom应用（Teleservice层的上层应用）、Keyguard应用（锁屏应用）、SystemUI应用、service.core库文件（framework层jar包）



voip-common的makefile文件

/frameworks/opt/net/voip/Android.mk
```makefile
LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_AIDL_INCLUDES := $(LOCAL_PATH)/src/java
LOCAL_SRC_FILES := $(call all-java-files-under, src/java) \
	$(call all-Iaidl-files-under, src/java) \
	$(call all-logtags-files-under, src/java)

#LOCAL_JAVA_LIBRARIES := telephony-common
LOCAL_JNI_SHARED_LIBRARIES := librtp_jni 
LOCAL_REQUIRED_MODULES := librtp_jni

LOCAL_MODULE_TAGS := optional
LOCAL_MODULE := voip-common

include $(BUILD_JAVA_LIBRARY)

# Include subdirectory makefiles
# ============================================================
include $(call all-makefiles-under,$(LOCAL_PATH)/src/jni)
```
voip-common java库引用了librtp_jni动态库，voip-common库主要是sip信令协议和rtp媒体传输协议的实现而librtp_jni库是rtp协议的c/c++实现部分

/frameworks/opt/net/voip/src/jni/rtp/Android.mk
```makefile
LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := librtp_jni

LOCAL_SRC_FILES := \
	AudioCodec.cpp \
	AudioGroup.cpp \
	EchoSuppressor.cpp \
	RtpStream.cpp \
	util.cpp \
	rtp_jni.cpp

LOCAL_SRC_FILES += \
	AmrCodec.cpp \
	G711Codec.cpp \
	GsmCodec.cpp

LOCAL_SHARED_LIBRARIES := \
	libnativehelper \
	libcutils \
	libutils \
	liblog \
	libmedia \
	libstagefright_amrnb_common

LOCAL_STATIC_LIBRARIES := libgsm libstagefright_amrnbdec libstagefright_amrnbenc

LOCAL_C_INCLUDES += \
	$(JNI_H_INCLUDE) \
	external/libgsm/inc \
	frameworks/av/media/libstagefright/codecs/amrnb/common/include \
	frameworks/av/media/libstagefright/codecs/amrnb/common/ \
	frameworks/av/media/libstagefright/codecs/amrnb/enc/include \
	frameworks/av/media/libstagefright/codecs/amrnb/enc/src \
	frameworks/av/media/libstagefright/codecs/amrnb/dec/include \
	frameworks/av/media/libstagefright/codecs/amrnb/dec/src \
	$(call include-path-for, audio-effects)

# getInput() is deprecated but we want to continue to track the usage of it elsewhere
LOCAL_CFLAGS += -fvisibility=hidden -Wall -Wextra -Wno-deprecated-declarations -Werror

include $(BUILD_SHARED_LIBRARY)

```


ims-common的makefile文件

/frameworks/opt/net/ims/Android.mk
```makefile
LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_AIDL_INCLUDES := $(LOCAL_PATH)/src/java
LOCAL_SRC_FILES := \
    $(call all-java-files-under, src/java)

#LOCAL_JAVA_LIBRARIES := telephony-common

LOCAL_MODULE_TAGS := optional
LOCAL_MODULE := ims-common

include $(BUILD_JAVA_LIBRARY)

include $(call all-makefiles-under,$(LOCAL_PATH))
```



好了，现在我们终于可以回到TeleService.apk应用的入口类PhoneApp。

 /packages/services/Telephony/src/com/android/phone/PhoneApp.java
```java
/**
 * Top-level Application class for the Phone app.
 */
public class PhoneApp extends Application {
    PhoneGlobals mPhoneGlobals;
    TelephonyGlobals mTelephonyGlobals;

    public PhoneApp() {
    }

    @Override
    public void onCreate() {
        if (UserHandle.myUserId() == 0) {
            // We are running as the primary user, so should bring up the
            // global phone state.
            mPhoneGlobals = new PhoneGlobals(this);
            mPhoneGlobals.onCreate();

            mTelephonyGlobals = new TelephonyGlobals(this);
            mTelephonyGlobals.onCreate();
        }
    }
}
```
PhoneApp应用主要做了两件事：创建PhoneGlobals、TelephonyGlobals两个单例对象，并且启动两个单例对象。

那么我们向来看看PhoneGlobals的代码

/packages/services/Telephony/src/com/android/phone/PhoneGlobals.java
```java
/**
 * Global state for the telephony subsystem when running in the primary
 * phone process.
 */
public class PhoneGlobals extends ContextWrapper {
    ...
    private static PhoneGlobals sMe;
    ....
    public PhoneGlobals(Context context) {
        super(context);
        sMe = this;
    }
    ...
    /**
     * Returns the singleton instance of the PhoneApp.
     */
    public static PhoneGlobals getInstance() {
        if (sMe == null) {
            throw new IllegalStateException("No PhoneGlobals here!");
        }
        return sMe;
    }
    /**
     * Returns the singleton instance of the PhoneApp if running as the
     * primary user, otherwise null.
     */
    static PhoneGlobals getInstanceIfPrimary() {
        return sMe;
    }
    ...
    public void onCreate() {
        if (VDBG) Log.v(LOG_TAG, "onCreate()...");

        ContentResolver resolver = getContentResolver();

        // Cache the "voice capable" flag.
        // This flag currently comes from a resource (which is
        // overrideable on a per-product basis):
        sVoiceCapable =
                getResources().getBoolean(com.android.internal.R.bool.config_voice_capable);
        // ...but this might eventually become a PackageManager "system
        // feature" instead, in which case we'd do something like:
        // sVoiceCapable =
        //   getPackageManager().hasSystemFeature(PackageManager.FEATURE_TELEPHONY_VOICE_CALLS);

        if (mCM == null) {
            // Initialize the telephony framework
            PhoneFactory.makeDefaultPhones(this);

            // Start TelephonyDebugService After the default phone is created.
            Intent intent = new Intent(this, TelephonyDebugService.class);
            startService(intent);

            mCM = CallManager.getInstance();
            for (Phone phone : PhoneFactory.getPhones()) {
                mCM.registerPhone(phone);
            }

            // Create the NotificationMgr singleton, which is used to display
            // status bar icons and control other status bar behavior.
            notificationMgr = NotificationMgr.init(this);

            // If PhoneGlobals has crashed and is being restarted, then restart.
            mHandler.sendEmptyMessage(EVENT_RESTART_SIP);

            // Create an instance of CdmaPhoneCallState and initialize it to IDLE
            cdmaPhoneCallState = new CdmaPhoneCallState();
            cdmaPhoneCallState.CdmaPhoneCallStateInit();

            // before registering for phone state changes
            mPowerManager = (PowerManager) getSystemService(Context.POWER_SERVICE);
            mWakeLock = mPowerManager.newWakeLock(PowerManager.FULL_WAKE_LOCK, LOG_TAG);
            // lock used to keep the processor awake, when we don't care for the display.
            mPartialWakeLock = mPowerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK
                    | PowerManager.ON_AFTER_RELEASE, LOG_TAG);

            mKeyguardManager = (KeyguardManager) getSystemService(Context.KEYGUARD_SERVICE);

            // Get UpdateLock to suppress system-update related events (e.g. dialog show-up)
            // during phone calls.
            mUpdateLock = new UpdateLock("phone");

            if (DBG) Log.d(LOG_TAG, "onCreate: mUpdateLock: " + mUpdateLock);

            CallLogger callLogger = new CallLogger(this, new CallLogAsync());

            callGatewayManager = CallGatewayManager.getInstance();

            // Create the CallController singleton, which is the interface
            // to the telephony layer for user-initiated telephony functionality
            // (like making outgoing calls.)
            callController = CallController.init(this, callLogger, callGatewayManager);

            // Create the CallerInfoCache singleton, which remembers custom ring tone and
            // send-to-voicemail settings.
            //
            // The asynchronous caching will start just after this call.
            callerInfoCache = CallerInfoCache.init(this);

            phoneMgr = PhoneInterfaceManager.init(this, PhoneFactory.getDefaultPhone());

            configLoader = CarrierConfigLoader.init(this);

            // Create the CallNotifer singleton, which handles
            // asynchronous events from the telephony layer (like
            // launching the incoming-call UI when an incoming call comes
            // in.)
            notifier = CallNotifier.init(this);

            PhoneUtils.registerIccStatus(mHandler, EVENT_SIM_NETWORK_LOCKED);

            // register for MMI/USSD
            mCM.registerForMmiComplete(mHandler, MMI_COMPLETE, null);

            // register connection tracking to PhoneUtils
            PhoneUtils.initializeConnectionHandler(mCM);

            // Register for misc other intent broadcasts.
            IntentFilter intentFilter =
                    new IntentFilter(Intent.ACTION_AIRPLANE_MODE_CHANGED);
            intentFilter.addAction(TelephonyIntents.ACTION_ANY_DATA_CONNECTION_STATE_CHANGED);
            intentFilter.addAction(TelephonyIntents.ACTION_SIM_STATE_CHANGED);
            intentFilter.addAction(TelephonyIntents.ACTION_RADIO_TECHNOLOGY_CHANGED);
            intentFilter.addAction(TelephonyIntents.ACTION_SERVICE_STATE_CHANGED);
            intentFilter.addAction(TelephonyIntents.ACTION_EMERGENCY_CALLBACK_MODE_CHANGED);
            registerReceiver(mReceiver, intentFilter);

            //set the default values for the preferences in the phone.
            PreferenceManager.setDefaultValues(this, R.xml.network_setting, false);

            PreferenceManager.setDefaultValues(this, R.xml.call_feature_setting, false);

            // Make sure the audio mode (along with some
            // audio-mode-related state of our own) is initialized
            // correctly, given the current state of the phone.
            PhoneUtils.setAudioMode(mCM);
        }

        cdmaOtaProvisionData = new OtaUtils.CdmaOtaProvisionData();
        cdmaOtaConfigData = new OtaUtils.CdmaOtaConfigData();
        cdmaOtaScreenState = new OtaUtils.CdmaOtaScreenState();
        cdmaOtaInCallScreenUiState = new OtaUtils.CdmaOtaInCallScreenUiState();

        simActivationManager = new SimActivationManager();

        // XXX pre-load the SimProvider so that it's ready
        resolver.getType(Uri.parse("content://icc/adn"));

        // TODO: Register for Cdma Information Records
        // phone.registerCdmaInformationRecord(mHandler, EVENT_UNSOL_CDMA_INFO_RECORD, null);

        // Read HAC settings and configure audio hardware
        if (getResources().getBoolean(R.bool.hac_enabled)) {
            int hac = android.provider.Settings.System.getInt(
                    getContentResolver(),
                    android.provider.Settings.System.HEARING_AID,
                    0);
            AudioManager audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
            audioManager.setParameter(SettingsConstants.HAC_KEY,
                    hac == SettingsConstants.HAC_ENABLED
                            ? SettingsConstants.HAC_VAL_ON : SettingsConstants.HAC_VAL_OFF);
        }
    }
    ...
}
```
PhoneGlobals这个类有下面几点可以讨论的：
- 设计模式：PhoneGlobals使用的设计模式为懒汉式单例。当其他地方调用getInstance方法时，对象就已经被创建了。这样可以节省启动时间。
- PhoneGlobals类的意义：我们再来看看PhoneGlobals类的父类ContextWrapper。。。。。占坑。。。。。。关于ContextWrapper类的意义查看这一篇博客。
- 在onCreate方法的初始化：通过工厂模式生产出Phone对象；将生产出来的Phone对象注册到CallManager饿汉式单例对象中；初始化NotificationMgr懒汉式单例对象，用于的status bar；获得到PowerManager、KeyguardManager两个类的对象用于管理电源和锁屏；CallController。。。。。。 ；动态注册一个广播，比如接受飞行模式的变化消息。



/frameworks/opt/telephony/src/java/com/android/internal/telephony/PhoneFactory.java
```java
/**
 * {@hide}
 */
public class PhoneFactory {
    ...
    public static void makeDefaultPhones(Context context) {
        makeDefaultPhone(context);
    }

    /**
     * FIXME replace this with some other way of making these
     * instances
     */
    public static void makeDefaultPhone(Context context) {
        synchronized (sLockProxyPhones) {
            if (!sMadeDefaults) {
                sContext = context;

                // create the telephony device controller.
                TelephonyDevController.create();

                int retryCount = 0;
                for(;;) {
                    boolean hasException = false;
                    retryCount ++;

                    try {
                        // use UNIX domain socket to
                        // prevent subsequent initialization
                        new LocalServerSocket("com.android.internal.telephony");
                    } catch (java.io.IOException ex) {
                        hasException = true;
                    }

                    if ( !hasException ) {
                        break;
                    } else if (retryCount > SOCKET_OPEN_MAX_RETRY) {
                        throw new RuntimeException("PhoneFactory probably already running");
                    } else {
                        try {
                            Thread.sleep(SOCKET_OPEN_RETRY_MILLIS);
                        } catch (InterruptedException er) {
                        }
                    }
                }

                sPhoneNotifier = new DefaultPhoneNotifier();

                int cdmaSubscription = CdmaSubscriptionSourceManager.getDefault(context);
                Rlog.i(LOG_TAG, "Cdma Subscription set to " + cdmaSubscription);

                /* In case of multi SIM mode two instances of Phone, RIL are created,
                   where as in single SIM mode only instance. isMultiSimEnabled() function checks
                   whether it is single SIM or multi SIM mode */
                int numPhones = TelephonyManager.getDefault().getPhoneCount();
                int[] networkModes = new int[numPhones];
                sPhones = new Phone[numPhones];
                sCommandsInterfaces = new RIL[numPhones];
                sTelephonyNetworkFactories = new TelephonyNetworkFactory[numPhones];

                for (int i = 0; i < numPhones; i++) {
                    // reads the system properties and makes commandsinterface
                    // Get preferred network type.
                    networkModes[i] = RILConstants.PREFERRED_NETWORK_MODE;

                    Rlog.i(LOG_TAG, "Network Mode set to " + Integer.toString(networkModes[i]));
                    sCommandsInterfaces[i] = new RIL(context, networkModes[i],
                            cdmaSubscription, i);
                }
                Rlog.i(LOG_TAG, "Creating SubscriptionController");
                SubscriptionController.init(context, sCommandsInterfaces);

                // Instantiate UiccController so that all other classes can just
                // call getInstance()
                sUiccController = UiccController.make(context, sCommandsInterfaces);

                for (int i = 0; i < numPhones; i++) {
                    Phone phone = null;
                    int phoneType = TelephonyManager.getPhoneType(networkModes[i]);
                    if (phoneType == PhoneConstants.PHONE_TYPE_GSM) {
                        phone = new GsmCdmaPhone(context,
                                sCommandsInterfaces[i], sPhoneNotifier, i,
                                PhoneConstants.PHONE_TYPE_GSM,
                                TelephonyComponentFactory.getInstance());
                    } else if (phoneType == PhoneConstants.PHONE_TYPE_CDMA) {
                        phone = new GsmCdmaPhone(context,
                                sCommandsInterfaces[i], sPhoneNotifier, i,
                                PhoneConstants.PHONE_TYPE_CDMA_LTE,
                                TelephonyComponentFactory.getInstance());
                    }
                    Rlog.i(LOG_TAG, "Creating Phone with type = " + phoneType + " sub = " + i);

                    sPhones[i] = phone;
                }

                // Set the default phone in base class.
                // FIXME: This is a first best guess at what the defaults will be. It
                // FIXME: needs to be done in a more controlled manner in the future.
                sPhone = sPhones[0];
                sCommandsInterface = sCommandsInterfaces[0];

                // Ensure that we have a default SMS app. Requesting the app with
                // updateIfNeeded set to true is enough to configure a default SMS app.
                ComponentName componentName =
                        SmsApplication.getDefaultSmsApplication(context, true /* updateIfNeeded */);
                String packageName = "NONE";
                if (componentName != null) {
                    packageName = componentName.getPackageName();
                }
                Rlog.i(LOG_TAG, "defaultSmsApplication: " + packageName);

                // Set up monitor to watch for changes to SMS packages
                SmsApplication.initSmsPackageMonitor(context);

                sMadeDefaults = true;

                Rlog.i(LOG_TAG, "Creating SubInfoRecordUpdater ");
                sSubInfoRecordUpdater = new SubscriptionInfoUpdater(context,
                        sPhones, sCommandsInterfaces);
                SubscriptionController.getInstance().updatePhonesAvailability(sPhones);

                // Start monitoring after defaults have been made.
                // Default phone must be ready before ImsPhone is created
                // because ImsService might need it when it is being opened.
                for (int i = 0; i < numPhones; i++) {
                    sPhones[i].startMonitoringImsService();
                }

                ITelephonyRegistry tr = ITelephonyRegistry.Stub.asInterface(
                        ServiceManager.getService("telephony.registry"));
                SubscriptionController sc = SubscriptionController.getInstance();

                sSubscriptionMonitor = new SubscriptionMonitor(tr, sContext, sc, numPhones);

                sPhoneSwitcher = new PhoneSwitcher(MAX_ACTIVE_PHONES, numPhones,
                        sContext, sc, Looper.myLooper(), tr, sCommandsInterfaces,
                        sPhones);

                sProxyController = ProxyController.getInstance(context, sPhones,
                        sUiccController, sCommandsInterfaces, sPhoneSwitcher);

                sTelephonyNetworkFactories = new TelephonyNetworkFactory[numPhones];
                for (int i = 0; i < numPhones; i++) {
                    sTelephonyNetworkFactories[i] = new TelephonyNetworkFactory(
                            sPhoneSwitcher, sc, sSubscriptionMonitor, Looper.myLooper(),
                            sContext, i, sPhones[i].mDcTracker);
                }
            }
        }
    }
    ...
}
```
了解设计模式中的工厂模式，那么对于PhoneFactory就会清楚它所要做的事情了。调用makeDefaultPhones方法创建出Phone对象，如果有插入两张卡就会有两个Phone对象，多个就会有多个对象。那么我们就再来看看具体的细节处理部分




































/frameworks/opt/telephony/src/java/com/android/internal/telephony/RIL.java
```java
public final class RIL extends BaseCommands implements CommandsInterface {
...
    class RILReceiver implements Runnable {
        byte[] buffer;

        RILReceiver() {
            buffer = new byte[RIL_MAX_COMMAND_BYTES];
        }

        @Override
        public void
        run() {
            int retryCount = 0;
            String rilSocket = "rild";

            try {for (;;) {
                LocalSocket s = null;
                LocalSocketAddress l;

                if (mInstanceId == null || mInstanceId == 0 ) {
                    rilSocket = SOCKET_NAME_RIL[0];
                } else {
                    rilSocket = SOCKET_NAME_RIL[mInstanceId];
                }

                try {
                    s = new LocalSocket();
                    l = new LocalSocketAddress(rilSocket,
                            LocalSocketAddress.Namespace.RESERVED);
                    s.connect(l);
                } catch (IOException ex){
                    try {
                        if (s != null) {
                            s.close();
                        }
                    } catch (IOException ex2) {
                        //ignore failure to close after failure to connect
                    }

                    // don't print an error message after the the first time
                    // or after the 8th time

                    if (retryCount == 8) {
                        Rlog.e (RILJ_LOG_TAG,
                            "Couldn't find '" + rilSocket
                            + "' socket after " + retryCount
                            + " times, continuing to retry silently");
                    } else if (retryCount >= 0 && retryCount < 8) {
                        Rlog.i (RILJ_LOG_TAG,
                            "Couldn't find '" + rilSocket
                            + "' socket; retrying after timeout");
                    }

                    try {
                        Thread.sleep(SOCKET_OPEN_RETRY_MILLIS);
                    } catch (InterruptedException er) {
                    }

                    retryCount++;
                    continue;
                }

                retryCount = 0;

                mSocket = s;
                Rlog.i(RILJ_LOG_TAG, "(" + mInstanceId + ") Connected to '"
                        + rilSocket + "' socket");

                int length = 0;
                try {
                    InputStream is = mSocket.getInputStream();

                    for (;;) {
                        Parcel p;

                        length = readRilMessage(is, buffer);

                        if (length < 0) {
                            // End-of-stream reached
                            break;
                        }

                        p = Parcel.obtain();
                        p.unmarshall(buffer, 0, length);
                        p.setDataPosition(0);

                        //Rlog.v(RILJ_LOG_TAG, "Read packet: " + length + " bytes");

                        processResponse(p);
                        p.recycle();
                    }
                } catch (java.io.IOException ex) {
                    Rlog.i(RILJ_LOG_TAG, "'" + rilSocket + "' socket closed",
                          ex);
                } catch (Throwable tr) {
                    Rlog.e(RILJ_LOG_TAG, "Uncaught exception read length=" + length +
                        "Exception:" + tr.toString());
                }

                Rlog.i(RILJ_LOG_TAG, "(" + mInstanceId + ") Disconnected from '" + rilSocket
                      + "' socket");

                setRadioState (RadioState.RADIO_UNAVAILABLE);

                try {
                    mSocket.close();
                } catch (IOException ex) {
                }

                mSocket = null;
                RILRequest.resetSerial();

                // Clear request list on close
                clearRequestList(RADIO_NOT_AVAILABLE, false);
            }} catch (Throwable tr) {
                Rlog.e(RILJ_LOG_TAG,"Uncaught exception", tr);
            }

            /* We're disconnected so we don't know the ril version */
            notifyRegistrantsRilConnectionChanged(-1);
        }
    }
...
}
```

# HAL

背景知识：

RILJ：RIL.Java（framework-java层中的Radio相关代码）

RILD：ril可执行程序（HAL层中Radio相关代码）

RILC：libril共享库（HAL层到framework-Native中Radio相关代码）

RIL：libreference-ril库（HAL层中Radio相关代码）

AT：atchannel文件


首先我们来看看/hardware/ril/rild目录下的makefile文件
/hardware/ril/rild/Android.mk

```makefile
# Copyright 2006 The Android Open Source Project

LOCAL_PATH:= $(call my-dir)
include $(CLEAR_VARS)

LOCAL_SRC_FILES:= \
	rild.c


LOCAL_SHARED_LIBRARIES := \
	liblog \
	libcutils \
	libril \
	libdl

# temporary hack for broken vendor rils
LOCAL_WHOLE_STATIC_LIBRARIES := \
	librilutils_static

LOCAL_CFLAGS := -DRIL_SHLIB
#LOCAL_CFLAGS += -DANDROID_MULTI_SIM

ifeq ($(SIM_COUNT), 2)
    LOCAL_CFLAGS += -DANDROID_SIM_COUNT_2
endif

LOCAL_MODULE:= rild
LOCAL_MODULE_TAGS := optional
LOCAL_INIT_RC := rild.rc

LOCAL_C_INCLUDES += $(TARGET_OUT_HEADERS)/libril

include $(BUILD_EXECUTABLE)

# For radiooptions binary
# =======================
include $(CLEAR_VARS)

LOCAL_SRC_FILES:= \
	radiooptions.c

LOCAL_SHARED_LIBRARIES := \
	liblog \
	libcutils \

LOCAL_CFLAGS := \

LOCAL_MODULE:= radiooptions
LOCAL_MODULE_TAGS := debug

include $(BUILD_EXECUTABLE)
```

会有两个可执行程序生成rild、radiooptions，但是radiooptions可执行程序并不是任何时候都会有。只有在系统编译编译类型为debug是，才会生成。而通过rild.rc文件创建的rild-debug就是用于radiooptions。接着看看/hardware/ril/rild目录下的rc文件。通过LOCAL_INIT_RC宏会将指定的rc文件 rild.rc复制到system/etc/目录下面，当系统启动是回去解析 rild.rc文件并完成所要求的操作

我们来看看 rild.rc文件的内容

/hardware/ril/rild/rild.rc
```rc
service ril-daemon /system/bin/rild
    class main
    socket rild stream 660 root radio
    socket sap_uim_socket1 stream 660 bluetooth bluetooth
    socket rild-debug stream 660 radio system
    user root
    group radio cache inet misc audio log readproc wakelock
```
rild.rc文件会启动一个名为ril-deam后台服务，也叫守护进程，该可执行程序是在/system/bin/目录下的rild程序,该服务会创建了三个名为rild、sap_uim_socket1、rild-debug的socket。拥有root权限，所属组较多，就不一一说明了。

那么当系统初次启动后，我们来看看ril-deam服务的入口函数main

/hardware/ril/rild/rild.c
```c
int main(int argc, char **argv) {
    ...
    umask(S_IRGRP | S_IWGRP | S_IXGRP | S_IROTH | S_IWOTH | S_IXOTH);
    for (i = 1; i < argc ;) {
        if (0 == strcmp(argv[i], "-l") && (argc - i > 1)) {
            rilLibPath = argv[i + 1];
            i += 2;
        } else if (0 == strcmp(argv[i], "--")) {
            i++;
            hasLibArgs = 1;
            break;
        } else if (0 == strcmp(argv[i], "-c") &&  (argc - i > 1)) {
            clientId = argv[i+1];
            i += 2;
        } else {
            usage(argv[0]);
        }
    }

    if (clientId == NULL) {
        clientId = "0";
    } else if (atoi(clientId) >= MAX_RILDS) {
        RLOGE("Max Number of rild's supported is: %d", MAX_RILDS);
        exit(0);
    }
    if (strncmp(clientId, "0", MAX_CLIENT_ID_LENGTH)) {
        strlcat(rild, clientId, MAX_SOCKET_NAME_LENGTH);
        RIL_setRilSocketName(rild);
    }

    if (rilLibPath == NULL) {
        if ( 0 == property_get(LIB_PATH_PROPERTY, libPath, NULL)) {
            // No lib sepcified on the command line, and nothing set in props.
            // Assume "no-ril" case.
            goto done;
        } else {
            rilLibPath = libPath;
        }
    }

    /* special override when in the emulator */
#if 1
    {
        static char*  arg_overrides[5];
        static char   arg_device[32];
        int           done = 0;

#define  REFERENCE_RIL_PATH  "libreference-ril.so"

        /* first, read /proc/cmdline into memory */
        char          buffer[1024] = {'\0'}, *p, *q;
        int           len;
        int           fd = open("/proc/cmdline",O_RDONLY);

        if (fd < 0) {
            RLOGD("could not open /proc/cmdline:%s", strerror(errno));
            goto OpenLib;
        }

        do {
            len = read(fd,buffer,sizeof(buffer)); }
        while (len == -1 && errno == EINTR);

        if (len < 0) {
            RLOGD("could not read /proc/cmdline:%s", strerror(errno));
            close(fd);
            goto OpenLib;
        }
        close(fd);

        if (strstr(buffer, "android.qemud=") != NULL)
        {
            /* the qemud daemon is launched after rild, so
            * give it some time to create its GSM socket
            */
            int  tries = 5;
#define  QEMUD_SOCKET_NAME    "qemud"

            while (1) {
                int  fd;

                sleep(1);

                fd = qemu_pipe_open("qemud:gsm");
                if (fd < 0) {
                    fd = socket_local_client(
                                QEMUD_SOCKET_NAME,
                                ANDROID_SOCKET_NAMESPACE_RESERVED,
                                SOCK_STREAM );
                }
                if (fd >= 0) {
                    close(fd);
                    snprintf( arg_device, sizeof(arg_device), "%s/%s",
                                ANDROID_SOCKET_DIR, QEMUD_SOCKET_NAME );

                    arg_overrides[1] = "-s";
                    arg_overrides[2] = arg_device;
                    done = 1;
                    break;
                }
                RLOGD("could not connect to %s socket: %s",
                    QEMUD_SOCKET_NAME, strerror(errno));
                if (--tries == 0)
                    break;
            }
            if (!done) {
                RLOGE("could not connect to %s socket (giving up): %s",
                    QEMUD_SOCKET_NAME, strerror(errno));
                while(1)
                    sleep(0x00ffffff);
            }
        }

        /* otherwise, try to see if we passed a device name from the kernel */
        if (!done) do {
#define  KERNEL_OPTION  "android.ril="
#define  DEV_PREFIX     "/dev/"

            p = strstr( buffer, KERNEL_OPTION );
            if (p == NULL)
                break;

            p += sizeof(KERNEL_OPTION)-1;
            q  = strpbrk( p, " \t\n\r" );
            if (q != NULL)
                *q = 0;

            snprintf( arg_device, sizeof(arg_device), DEV_PREFIX "%s", p );
            arg_device[sizeof(arg_device)-1] = 0;
            arg_overrides[1] = "-d";
            arg_overrides[2] = arg_device;
            done = 1;

        } while (0);

        if (done) {
            argv = arg_overrides;
            argc = 3;
            i    = 1;
            hasLibArgs = 1;
            rilLibPath = REFERENCE_RIL_PATH;

            RLOGD("overriding with %s %s", arg_overrides[1], arg_overrides[2]);
        }
    }
...

done:

    RLOGD("RIL_Init starting sleep loop");
    while (true) {
        sleep(UINT32_MAX);
    }
```
整个main函数代码思路较为简单。

- 1.对启动ril-deam服务时传过来的参数进行解析。
- 2.在读/proc/cmdline 文件读取之后，就会进入整个服务的核心部分。加载动态库、调用库中的函数、开启event轮询器等
- 3.存在qemud服务，就会在/dev/socket目录下创建一个文件名为qemud的客户端socket，用于与gsm modem交互
- 4.如果qemud服务创建失败，那么就会在/dev/目录下创建ttyxx 文件（linux下的终端控制台）
 
3、4在生产版本，要把 #if 1 修改为 #if 0, 或者在编译kernel里把生成的 /proc/cmdline 配置去掉android.qemud,使用模拟器时会有效果,[关于 android RIL 调试](http://blog.lytsing.org/archives/476.html)

所以接下来，我们主要关注点在于1、2


## 1.对启动ril-deam服务时传过来的参数进行解析。

执行rild守护进程时，一开始会对传进来的参数(rilLibPath、hasLibArgs、clientId)有个判断（指定了多少动态加载库，指定的动态库有都是参数，准备创建多少个socket客户端。）

如果启动时存在-c参数，则会调用RIL_setRilSocketName函数，将命令行中的客户端socket的名字保存到RILC（ril.cpp）的全局变量rild数组中。以供RILC(ril.cpp）调用android_get_control_socket函数创建服务端socket，然后RILJ客户端就可以和RILC服务端利用socket进行通信。

如果初次运行或者无参数运行rild服务则使用默认的rilLibPath（值位于build.prop里面，通过rild.libpath键名可以取到），socket默认为0个。


 /hardware/ril/libril/ril.cpp
 ```cpp
 ...
 char rild[MAX_SOCKET_NAME_LENGTH] = SOCKET_NAME_RIL;
 ...
 static char * RIL_getRilSocketName() {
    return rild;
}
 extern "C"
void RIL_setRilSocketName(const char * s) {
    strncpy(rild, s, MAX_SOCKET_NAME_LENGTH);
}
 ```
 
## 2.加载动态库、调用库中的函数、开启event轮询器等
 
 
接下来， 打开并且读取/proc/cmdline文件内容。得到其中的内容查询是否存在“android.qemud=”的字符串。

如果存在qemud守护进程，就会调用socket_local_client函数在/dev/socket目录下创建流类型的socket客户端，并且将socket名字传给RILC，，让其创建相应的socket服务端

如果不存在，继续查找内容中是否存在"android.ril="的字符串，如果存在，将其值（“android.ril”的值tty+"android.ril="字符串的大小-1，比如tty11）保存到数组arg_overrides中，而数组arg_overrides将被传到动态加载库libreference-ril的/hardware/ril/reference-ril/reference-ril.c的RIL_Init函数中,RIL_Init函数将在/dev/目录下创建tty 设备（tty就是一个终端控制台）


其实读取完/proc/cmdline 文件后还会动态加载libreference-ril库（RIL）、操作库中的函数

/hardware/ril/rild/rild.c

```c
OpenLib:
#endif
    switchUser();

    dlHandle = dlopen(rilLibPath, RTLD_NOW);

    if (dlHandle == NULL) {
        RLOGE("dlopen failed: %s", dlerror());
        exit(EXIT_FAILURE);
    }

    RIL_startEventLoop();

    rilInit =
        (const RIL_RadioFunctions *(*)(const struct RIL_Env *, int, char **))
        dlsym(dlHandle, "RIL_Init");

    if (rilInit == NULL) {
        RLOGE("RIL_Init not defined or exported in %s\n", rilLibPath);
        exit(EXIT_FAILURE);
    }

    dlerror(); // Clear any previous dlerror
    rilUimInit =
        (const RIL_RadioFunctions *(*)(const struct RIL_Env *, int, char **))
        dlsym(dlHandle, "RIL_SAP_Init");
    err_str = dlerror();
    if (err_str) {
        RLOGW("RIL_SAP_Init not defined or exported in %s: %s\n", rilLibPath, err_str);
    } else if (!rilUimInit) {
        RLOGW("RIL_SAP_Init defined as null in %s. SAP Not usable\n", rilLibPath);
    }

    if (hasLibArgs) {
        rilArgv = argv + i - 1;
        argc = argc -i + 1;
    } else {
        static char * newArgv[MAX_LIB_ARGS];
        static char args[PROPERTY_VALUE_MAX];
        rilArgv = newArgv;
        property_get(LIB_ARGS_PROPERTY, args, "");
        argc = make_argv(args, rilArgv);
    }

    rilArgv[argc++] = "-c";
    rilArgv[argc++] = clientId;
    RLOGD("RIL_Init argc = %d clientId = %s", argc, rilArgv[argc-1]);

    // Make sure there's a reasonable argv[0]
    rilArgv[0] = argv[0];

    funcs = rilInit(&s_rilEnv, argc, rilArgv);
    RLOGD("RIL_Init rilInit completed");

    RIL_register(funcs);

    RLOGD("RIL_Init RIL_register completed");

    if (rilUimInit) {
        RLOGD("RIL_register_socket started");
        RIL_register_socket(rilUimInit, RIL_SAP_SOCKET, argc, rilArgv);
    }

    RLOGD("RIL_register_socket completed");
```
=========================================================================================================
RILC层
=========================================================================================================
通过dlopen加载共享库、dlsym操作库中的函数。在使用dlsym函数之前，会调用RIL_startEventLoop函数创建一个轮询线程

/hardware/ril/libril/ril.cpp
```cpp
...
static pthread_t s_tid_dispatch;
...
static int s_started = 0;
...
static pthread_mutex_t s_startupMutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t s_startupCond = PTHREAD_COND_INITIALIZER;
...
extern "C" void
RIL_startEventLoop(void) {
    /* spin up eventLoop thread and wait for it to get started */
    s_started = 0;
    pthread_mutex_lock(&s_startupMutex);

    pthread_attr_t attr;
    pthread_attr_init(&attr);
    pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);

    int result = pthread_create(&s_tid_dispatch, &attr, eventLoop, NULL);
    if (result != 0) {
        RLOGE("Failed to create dispatch thread: %s", strerror(result));
        goto done;
    }

    while (s_started == 0) {
        pthread_cond_wait(&s_startupCond, &s_startupMutex);
    }

done:
    pthread_mutex_unlock(&s_startupMutex);
}
```
将eventLoop函数加入线程中，调用pthread_cond_wait函数等待结果。。。。。。。

/hardware/ril/libril/ril.cpp
```cpp
...
static struct ril_event s_wakeupfd_event;
...
static void *
eventLoop(void *param) {
    int ret;
    int filedes[2];

    ril_event_init();

    pthread_mutex_lock(&s_startupMutex);

    s_started = 1;
    pthread_cond_broadcast(&s_startupCond);

    pthread_mutex_unlock(&s_startupMutex);

    ret = pipe(filedes);

    if (ret < 0) {
        RLOGE("Error in pipe() errno:%d", errno);
        return NULL;
    }

    s_fdWakeupRead = filedes[0];
    s_fdWakeupWrite = filedes[1];

    fcntl(s_fdWakeupRead, F_SETFL, O_NONBLOCK);

    ril_event_set (&s_wakeupfd_event, s_fdWakeupRead, true,
                processWakeupCallback, NULL);

    rilEventAddWakeup (&s_wakeupfd_event);

    // Only returns on error
    ril_event_loop();
    RLOGE ("error in event_loop_base errno:%d", errno);
    // kill self to restart on error
    kill(0, SIGKILL);

    return NULL;
}
...
```
- 给timer_list、pending_list连个双链表和一个watch_table数组分配内存
- 给ril_event类型的结构体s_wakeupfd_event设置具体的值，其中的回调函数processWakeupCallback是用来读取文件描述符s_fdWakeupRead，而s_fdWakeupRead的更新是基于s_fdWakeupWrite，因为这两者利用管道（pipe）进行通信
- 添加ril_event类型的结构体s_wakeupfd_event到监听事件数组watch_table中，并且会往文件描述符s_fdWakeupWrite写值，来触发监听文件描述符s_fdWakeupRead的监听器
- 开始event loop，这是个死循环，如果循环终止，这说明出现问题了，该线程会被kill掉，并且重新启动

`初始化event loop`

/hardware/ril/libril/ril_event.cpp
```cpp
...
static pthread_mutex_t listMutex;
...
#define MUTEX_INIT() pthread_mutex_init(&listMutex, NULL)
...
static struct ril_event * watch_table[MAX_FD_EVENTS];
static struct ril_event timer_list;
static struct ril_event pending_list;
void ril_event_init()
{
    MUTEX_INIT();

    FD_ZERO(&readFds);
    init_list(&timer_list);
    init_list(&pending_list);
    memset(watch_table, 0, sizeof(watch_table));
}
```
初始化timer_list、pending_list这两个双链表时间和一个监听事件的数组watch_table，以及清空readFds文件描述符集合

 /hardware/ril/libril/ril_event.h
```cpp
// Max number of fd's we watch at any one time.  Increase if necessary.
#define MAX_FD_EVENTS 8

typedef void (*ril_event_cb)(int fd, short events, void *userdata);

struct ril_event {
    struct ril_event *next;
    struct ril_event *prev;

    int fd;
    int index;
    bool persist;
    struct timeval timeout;
    ril_event_cb func;
    void *param;
};
```


`设置event loop`

ril_event_set函数较为简单就是对ril_event结构体变量s_wakeupfd_event进行赋值，其中的processWakeupCallback函数是回到函数

`添加event到监听事件数组watch_table中`

/hardware/ril/libril/ril.cpp
```cpp
static void rilEventAddWakeup(struct ril_event *ev) {
    ril_event_add(ev);
    triggerEvLoop();
}
```
该函数就是做了两件事情，第一件事：增加事件到监听事件数组watch_table；第二件事：触发文件描述符s_fdWakeupRead的监听器

第一件事：

/hardware/ril/libril/ril_event.cpp
```cpp
void ril_event_add(struct ril_event * ev)
{
    dlog("~~~~ +ril_event_add ~~~~");
    MUTEX_ACQUIRE();
    for (int i = 0; i < MAX_FD_EVENTS; i++) {
        if (watch_table[i] == NULL) {
            watch_table[i] = ev;
            ev->index = i;
            dlog("~~~~ added at %d ~~~~", i);
            dump_event(ev);
            FD_SET(ev->fd, &readFds);
            if (ev->fd >= nfds) nfds = ev->fd+1;
            dlog("~~~~ nfds = %d ~~~~", nfds);
            break;
        }
    }
    MUTEX_RELEASE();
    dlog("~~~~ -ril_event_add ~~~~");
}
```
调用FD_SET宏空，将ril_event中的文件描述符加入到readFds文件描述符集合，以便循环时使用select函数来监听是否有可读数据

第二件事：

/hardware/ril/libril/ril.cpp
```cpp
static void triggerEvLoop() {
    int ret;
    if (!pthread_equal(pthread_self(), s_tid_dispatch)) {
        /* trigger event loop to wakeup. No reason to do this,
         * if we're in the event loop thread */
         do {
            ret = write (s_fdWakeupWrite, " ", 1);
         } while (ret < 0 && errno == EINTR);
    }
}
```

`开始event loop`

/hardware/ril/libril/ril_event.cpp

```cpp
void ril_event_loop()
{
    int n;
    fd_set rfds;
    struct timeval tv;
    struct timeval * ptv;

    for (;;) {
        // make local copy of read fd_set
        memcpy(&rfds, &readFds, sizeof(fd_set));
        if (-1 == calcNextTimeout(&tv)) {
            // no pending timers; block indefinitely
            dlog("~~~~ no timers; blocking indefinitely ~~~~");
            ptv = NULL;
        } else {
            dlog("~~~~ blocking for %ds + %dus ~~~~", (int)tv.tv_sec, (int)tv.tv_usec);
            ptv = &tv;
        }
        printReadies(&rfds);
        n = select(nfds, &rfds, NULL, NULL, ptv);
        printReadies(&rfds);
        dlog("~~~~ %d events fired ~~~~", n);
        if (n < 0) {
            if (errno == EINTR) continue;

            RLOGE("ril_event: select error (%d)", errno);
            // bail?
            return;
        }

        // Check for timeouts
        processTimeouts();
        // Check for read-ready
        processReadReadies(&rfds, n);
        // Fire away
        firePending();
    }
}
```
终于讲到了整个ril层的重点了，其中利用一个阻塞循环，调用select监视rfds文件描述符集合的内容变化。通过将watch_tabel数组和timer_list双链表中有更新的event添加到pending_list双链表中，并且依次执行ril_event类型的结构体event中的回调函数（专门用来处理RILJ层传过来的消息并对其进行处理）既然已经知道RILC对于RILJ层的处理，那么接下来就是RILC和RIL层的交互了。


=========================================================================================================
RIL层
=========================================================================================================
接下来调用dlsym函数将RIL_Init函数指针传给rilInit；RIL_SAP_Init函数指针传给rilUimInit，返回值都为RIL_RadioFunctions类型的结构体。见名知意，RIL_Init函数就是用来初始化RIL层的。我们来看看返回值RIL_RadioFunctions的代码

 /hardware/ril/include/telephony/ril.h
```cpp
#if defined(ANDROID_MULTI_SIM)

typedef void (*RIL_RequestFunc) (int request, void *data,
                                    size_t datalen, RIL_Token t, RIL_SOCKET_ID socket_id);

typedef RIL_RadioState (*RIL_RadioStateRequest)(RIL_SOCKET_ID socket_id);

#else

typedef void (*RIL_RequestFunc) (int request, void *data,
                                    size_t datalen, RIL_Token t);

typedef RIL_RadioState (*RIL_RadioStateRequest)();

#endif

typedef int (*RIL_Supports)(int requestCode);


typedef void (*RIL_Cancel)(RIL_Token t);

typedef void (*RIL_TimedCallback) (void *param);

typedef const char * (*RIL_GetVersion) (void);

typedef struct {
    int version;        /* set to RIL_VERSION */
    RIL_RequestFunc onRequest;
    RIL_RadioStateRequest onStateRequest;
    RIL_Supports supports;
    RIL_Cancel onCancel;
    RIL_GetVersion getVersion;
} RIL_RadioFunctions;
```
在RILC层声明的RIL_RadioFunctions类型的结构体，存储着一些回调函数指针。在RIL层实现了在RILC层申明的函数。简单来说就是在RILC层注册了一些监听器（代码中叫做callback），在RIL层监听RILC层的变化

/hardware/ril/reference-ril/reference-ril.c
```c
static const RIL_RadioFunctions s_callbacks = {
    RIL_VERSION,
    onRequest,
    currentState,
    onSupports,
    onCancel,
    getVersion
};
```
那么我们在回来看看RIL_Init函数的定义吧。
 
 /hardware/ril/reference-ril/reference-ril.c
```c
#ifdef RIL_SHLIB

pthread_t s_tid_mainloop;
const RIL_RadioFunctions *RIL_Init(const struct RIL_Env *env, int argc, char **argv)
{
    int ret;
    int fd = -1;
    int opt;
    pthread_attr_t attr;

    s_rilenv = env;

    while ( -1 != (opt = getopt(argc, argv, "p:d:s:c:"))) {
        switch (opt) {
            case 'p':
                s_port = atoi(optarg);
                if (s_port == 0) {
                    usage(argv[0]);
                    return NULL;
                }
                RLOGI("Opening loopback port %d\n", s_port);
            break;

            case 'd':
                s_device_path = optarg;
                RLOGI("Opening tty device %s\n", s_device_path);
            break;

            case 's':
                s_device_path   = optarg;
                s_device_socket = 1;
                RLOGI("Opening socket %s\n", s_device_path);
            break;

            case 'c':
                RLOGI("Client id received %s\n", optarg);
            break;

            default:
                usage(argv[0]);
                return NULL;
        }
    }

    if (s_port < 0 && s_device_path == NULL) {
        usage(argv[0]);
        return NULL;
    }

    sMdmInfo = calloc(1, sizeof(ModemInfo));
    if (!sMdmInfo) {
        RLOGE("Unable to alloc memory for ModemInfo");
        return NULL;
    }
    pthread_attr_init (&attr);
    pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);
    ret = pthread_create(&s_tid_mainloop, &attr, mainLoop, NULL);

    return &s_callbacks;
}
#else /* RIL_SHLIB */
int main (int argc, char **argv)
{
    ...
}
#endif /* RIL_SHLIB */
```

首先我们来看看从RILD传过来的参数env,该参数也是一个存储回调函数指针的结构体。是在RIL层注册，在RILC层监听（在RILD层中定义了一个RIL_Env类型的结构体s_rilEnv，并将结构体中的函数指针当做接口提供给RILC，并让其实现。而RIL通过在运行逻辑中调用这些接口，可以及时的通知RILC层，从而让其做出变化）。大概来看看都有什么具体的函数

RILC ---> RIL(RIL_RadioFunctions监听器)

(RIL_Env监听器)RILC <--- RIL


 /hardware/ril/rild/rild.c
```c
static struct RIL_Env s_rilEnv = {
    RIL_onRequestComplete,
    RIL_onUnsolicitedResponse,
    RIL_requestTimedCallback,
    RIL_onRequestAck
};
```

说了这么多，感觉有点偏离。我们还是回到RIL_Init函数吧，不光实现了RILC层和RIL层双向监听，还开启了一个轮询线程。这里说个题外话，RILD层活在主线程，而RILC层和RIL层却活在两个由主线程创建出来的工作线程。而在RIL层的工作线程由创建了一个AT轮询线程

轮询线程

/hardware/ril/reference-ril/reference-ril.c
```c
static void *
mainLoop(void *param __unused)
{
    int fd;
    int ret;

    AT_DUMP("== ", "entering mainLoop()", -1 );
    at_set_on_reader_closed(onATReaderClosed);
    at_set_on_timeout(onATTimeout);

    for (;;) {
        fd = -1;
        while  (fd < 0) {
            if (s_port > 0) {
                fd = socket_loopback_client(s_port, SOCK_STREAM);
            } else if (s_device_socket) {
                if (!strcmp(s_device_path, "/dev/socket/qemud")) {
                    /* Before trying to connect to /dev/socket/qemud (which is
                     * now another "legacy" way of communicating with the
                     * emulator), we will try to connecto to gsm service via
                     * qemu pipe. */
                    fd = qemu_pipe_open("qemud:gsm");
                    if (fd < 0) {
                        /* Qemu-specific control socket */
                        fd = socket_local_client( "qemud",
                                                  ANDROID_SOCKET_NAMESPACE_RESERVED,
                                                  SOCK_STREAM );
                        if (fd >= 0 ) {
                            char  answer[2];

                            if ( write(fd, "gsm", 3) != 3 ||
                                 read(fd, answer, 2) != 2 ||
                                 memcmp(answer, "OK", 2) != 0)
                            {
                                close(fd);
                                fd = -1;
                            }
                       }
                    }
                }
                else
                    fd = socket_local_client( s_device_path,
                                            ANDROID_SOCKET_NAMESPACE_FILESYSTEM,
                                            SOCK_STREAM );
            } else if (s_device_path != NULL) {
                fd = open (s_device_path, O_RDWR);
                if ( fd >= 0 && !memcmp( s_device_path, "/dev/ttyS", 9 ) ) {
                    /* disable echo on serial ports */
                    struct termios  ios;
                    tcgetattr( fd, &ios );
                    ios.c_lflag = 0;  /* disable ECHO, ICANON, etc... */
                    tcsetattr( fd, TCSANOW, &ios );
                }
            }

            if (fd < 0) {
                perror ("opening AT interface. retrying...");
                sleep(10);
                /* never returns */
            }
        }

        s_closed = 0;
        ret = at_open(fd, onUnsolicited);

        if (ret < 0) {
            RLOGE ("AT error %d on at_open\n", ret);
            return 0;
        }

        RIL_requestTimedCallback(initializeCallback, NULL, &TIMEVAL_0);

        // Give initializeCallback a chance to dispatched, since
        // we don't presently have a cancellation mechanism
        sleep(1);

        waitForClose();
        RLOGI("Re-opening after close");
    }
}

```
mainloop函数主要做了以下几件事

- 在AT层注册onATReaderClosed、onATTimeout两个回调函数
- 创建给at和modem通信的文件描述符。
- 在RIL层的工作线程中再创建出一个AT工作线程
- 通过RIL层的函数RIL_requestTimedCallback回到RILC层的函数RIL_requestTimedCallback

- 调用waitForClose函数阻塞mainloop线程，当at通道发生异常时，通过改变全局变量s_closed为1，就会进入下一次的for循环，重新调用at_open函数去打开at通道

`第一件事情：在AT层注册onATReaderClosed、onATTimeout两个回调函数`

将处理at异常、超时的函数传到AT层去注册，这样上层可以对AT层的异常及时的处理
```c
    at_set_on_reader_closed(onATReaderClosed);
    at_set_on_timeout(onATTimeout);
```



`第二件事情：创建给at和modem通信的文件描述符。`

一个有三次判断，无非是s_port、s_device_path、s_device_socket这三种。其实在进入mainloop线程之前，主线程就有对这些字段的赋值处理。

 /hardware/ril/reference-ril/reference-ril.c
```c
#ifdef RIL_SHLIB

pthread_t s_tid_mainloop;
const RIL_RadioFunctions *RIL_Init(const struct RIL_Env *env, int argc, char **argv)
{
    ...

    while ( -1 != (opt = getopt(argc, argv, "p:d:s:c:"))) {
        switch (opt) {
            case 'p':
                s_port = atoi(optarg);
                if (s_port == 0) {
                    usage(argv[0]);
                    return NULL;
                }
                RLOGI("Opening loopback port %d\n", s_port);
            break;

            case 'd':
                s_device_path = optarg;
                RLOGI("Opening tty device %s\n", s_device_path);
            break;

            case 's':
                s_device_path   = optarg;
                s_device_socket = 1;
                RLOGI("Opening socket %s\n", s_device_path);
            break;

            case 'c':
                RLOGI("Client id received %s\n", optarg);
            break;

            default:
                usage(argv[0]);
                return NULL;
        }
    }
...
#endif /* RIL_SHLIB */
```

那么现在我们重新回到mainloop线程。

一个是面向回环端口（“p”）的socket文件描述符,一个是面向文件(“s”）的socket文件描述符,还有一个是面向设备串口("d")的设备文件描述符。而是面向文件(“s”）的socket文件描述符，当手机为模拟机（qemu）时才会创建的。因为模拟机本身不具备modem设备，是可以外接modem设备的。如果外接了modem设备才会创建socket。而面向设备串口("d")的设备文件描述符，是手机为真机时创建的。而AT指令其实是通过文集描述符和modem设备进行通信的


`第三件事情：在RIL层的工作线程中再创建出一个AT工作线程。`

RIL层在AT层注册了一个ATUnsolHandler类型的回调函数onUnsolicited，会向之前的onATTimeout、 onATReaderClosed两个回调函数，这已经是第三个。不过不同的是这个回调函数处理的是modem设备传过俩的信号。想要了解这些回调函数的具体实现。==观看这一篇《RIL层的回调函数》==。

/hardware/ril/reference-ril/atchannel.c
```c
int at_open(int fd, ATUnsolHandler h)
{
    int ret;
    pthread_t tid;
    pthread_attr_t attr;

    s_fd = fd;
    s_unsolHandler = h;
    s_readerClosed = 0;

    s_responsePrefix = NULL;
    s_smsPDU = NULL;
    sp_response = NULL;

    pthread_attr_init (&attr);
    pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);

    ret = pthread_create(&s_tid_reader, &attr, readerLoop, &attr);

    if (ret < 0) {
        perror ("pthread_create");
        return -1;
    }


    return 0;
}
```
不过关键点还是在于创建了一个readerlooper线程

/hardware/ril/reference-ril/atchannel.c
```c
static void *readerLoop(void *arg)
{
    for (;;) {
        const char * line;

        line = readline();

        if (line == NULL) {
            break;
        }

        if(isSMSUnsolicited(line)) {
            char *line1;
            const char *line2;

            // The scope of string returned by 'readline()' is valid only
            // till next call to 'readline()' hence making a copy of line
            // before calling readline again.
            line1 = strdup(line);
            line2 = readline();

            if (line2 == NULL) {
                free(line1);
                break;
            }

            if (s_unsolHandler != NULL) {
                s_unsolHandler (line1, line2);
            }
            free(line1);
        } else {
            processLine(line);
        }
    }

    onReaderClosed();

    return NULL;
}
```
- readline：读取modem设备上传的at指令

- isSMSUnsolicited:判断modem上传的at指令，是不是上层下发+CNMI或者+CSCB指令（设置短信接收提示方式）后的unsolicited类型的响应（有cmt、cds、cbm）。如果该at指令时短信的unsolicited响应的话，会通过s_unsolHandler函数（RIL层的onUnsolicited函数），上报给RIL层

- processLine：如果不是短信的unsolicited响应，那么会调用processLine函数处理
- onReaderClosed：如果for循环被break掉的话，也就是数据读取完了，就会调用onReaderClosed通知RIL层的回调函数onATReaderClosed关闭AT通道

那我们就来看看processLine函数的处理逻辑

/hardware/ril/reference-ril/atchannel.c
```c
static void processLine(const char *line)
{
    pthread_mutex_lock(&s_commandmutex);

    if (sp_response == NULL) {
        /* no command pending */
        handleUnsolicited(line);
    } else if (isFinalResponseSuccess(line)) {
        sp_response->success = 1;
        handleFinalResponse(line);
    } else if (isFinalResponseError(line)) {
        sp_response->success = 0;
        handleFinalResponse(line);
    } else if (s_smsPDU != NULL && 0 == strcmp(line, "> ")) {
        // See eg. TS 27.005 4.3
        // Commands like AT+CMGS have a "> " prompt
        writeCtrlZ(s_smsPDU);
        s_smsPDU = NULL;
    } else switch (s_type) {
        case NO_RESULT:
            handleUnsolicited(line);
            break;
        case NUMERIC:
            if (sp_response->p_intermediates == NULL
                && isdigit(line[0])
            ) {
                addIntermediate(line);
            } else {
                /* either we already have an intermediate response or
                   the line doesn't begin with a digit */
                handleUnsolicited(line);
            }
            break;
        case SINGLELINE:
            if (sp_response->p_intermediates == NULL
                && strStartsWith (line, s_responsePrefix)
            ) {
                addIntermediate(line);
            } else {
                /* we already have an intermediate response */
                handleUnsolicited(line);
            }
            break;
        case MULTILINE:
            if (strStartsWith (line, s_responsePrefix)) {
                addIntermediate(line);
            } else {
                handleUnsolicited(line);
            }
        break;

        default: /* this should never be reached */
            RLOGE("Unsupported AT command type %d\n", s_type);
            handleUnsolicited(line);
        break;
    }

    pthread_mutex_unlock(&s_commandmutex);
}
```
交给at指令上传给了RIL层去处理了

`第四件事情：通过RIL层的函数RIL_requestTimedCallback回到RILC层的函数RIL_requestTimedCallback`

RILC层RIL_requestTimedCallback函数实现就是调用了internalRequestTimedCallback函数。我们来看看RILC层的回调函数internalRequestTimedCallback的代码


/hardware/ril/libril/ril.cpp
```c
static UserCallbackInfo *
internalRequestTimedCallback (RIL_TimedCallback callback, void *param,
                                const struct timeval *relativeTime)
{
    struct timeval myRelativeTime;
    UserCallbackInfo *p_info;

    p_info = (UserCallbackInfo *) calloc(1, sizeof(UserCallbackInfo));
    if (p_info == NULL) {
        RLOGE("Memory allocation failed in internalRequestTimedCallback");
        return p_info;

    }

    p_info->p_callback = callback;
    p_info->userParam = param;

    if (relativeTime == NULL) {
        /* treat null parameter as a 0 relative time */
        memset (&myRelativeTime, 0, sizeof(myRelativeTime));
    } else {
        /* FIXME I think event_add's tv param is really const anyway */
        memcpy (&myRelativeTime, relativeTime, sizeof(myRelativeTime));
    }

    ril_event_set(&(p_info->event), -1, false, userTimerCallback, p_info);

    ril_timer_add(&(p_info->event), &myRelativeTime);

    triggerEvLoop();
    return p_info;
}
```

将从RIL层上报到RILC层的参数用UserCallbackInfo类型的结构体p_info包装起来，并将其中的event添加timer_list双链表中，而timer_list中的event数据会在eventLoop轮询线程中被添加到pending_list双链表中。随之而来的就是回调userTimerCallback函数。那么我们来看看这个函数的代码吧

/hardware/ril/libril/ril.cpp
 ```c
 static void userTimerCallback (int fd, short flags, void *param) {
    UserCallbackInfo *p_info;

    p_info = (UserCallbackInfo *)param;

    p_info->p_callback(p_info->userParam);


    // FIXME generalize this...there should be a cancel mechanism
    if (s_last_wake_timeout_info != NULL && s_last_wake_timeout_info == p_info) {
        s_last_wake_timeout_info = NULL;
    }

    free(p_info);
}
```
终于回调了RIL层的回调函数initializeCallback。我们知道之前在RIL层的readerLoop轮询线程调用 RIL_requestTimedCallback函数，并传入了initializeCallback函数指针。在RILC层走了一圈终于回到了RIL层，并且为RIL层带来了UserCallbackInfo单链表，不过很可惜，这个表里面并没有可用的信息,因为userparam为null。

/hardware/ril/libril/ril.cpp
```c
/**
 * Initialize everything that can be configured while we're still in
 * AT+CFUN=0
 */
static void initializeCallback(void *param __unused)
{
    ATResponse *p_response = NULL;
    int err;

    setRadioState (RADIO_STATE_OFF);

    at_handshake();

    probeForModemMode(sMdmInfo);
    /* note: we don't check errors here. Everything important will
       be handled in onATTimeout and onATReaderClosed */

    /*  atchannel is tolerant of echo but it must */
    /*  have verbose result codes */
    at_send_command("ATE0Q0V1", NULL);

    /*  No auto-answer */
    at_send_command("ATS0=0", NULL);

    /*  Extended errors */
    at_send_command("AT+CMEE=1", NULL);

    /*  Network registration events */
    err = at_send_command("AT+CREG=2", &p_response);

    /* some handsets -- in tethered mode -- don't support CREG=2 */
    if (err < 0 || p_response->success == 0) {
        at_send_command("AT+CREG=1", NULL);
    }

    at_response_free(p_response);

    /*  GPRS registration events */
    at_send_command("AT+CGREG=1", NULL);

    /*  Call Waiting notifications */
    at_send_command("AT+CCWA=1", NULL);

    /*  Alternating voice/data off */
    at_send_command("AT+CMOD=0", NULL);

    /*  Not muted */
    at_send_command("AT+CMUT=0", NULL);

    /*  +CSSU unsolicited supp service notifications */
    at_send_command("AT+CSSN=0,1", NULL);

    /*  no connected line identification */
    at_send_command("AT+COLP=0", NULL);

    /*  HEX character set */
    at_send_command("AT+CSCS=\"HEX\"", NULL);

    /*  USSD unsolicited */
    at_send_command("AT+CUSD=1", NULL);

    /*  Enable +CGEV GPRS event notifications, but don't buffer */
    at_send_command("AT+CGEREP=1,0", NULL);

    /*  SMS PDU mode */
    at_send_command("AT+CMGF=0", NULL);

#ifdef USE_TI_COMMANDS

    at_send_command("AT%CPI=3", NULL);

    /*  TI specific -- notifications when SMS is ready (currently ignored) */
    at_send_command("AT%CSTAT=1", NULL);

#endif /* USE_TI_COMMANDS */


    /* assume radio is off on error */
    if (isRadioOn() > 0) {
        setRadioState (RADIO_STATE_ON);
    }
}

```
radio的状态为先关闭再开。主要是为了重新连接modem，我们可以看到最开始AT层会和modem握手连接，然后查找modem的模式，是gsm，cdma或者是都支持（全网通），接着就是各种ta指令。大概的流程已经明白，我们再看看最后如何将radio功能打开

/hardware/ril/reference-ril/reference-ril.c
```c
static void
setRadioState(RIL_RadioState newState)
{
    RLOGD("setRadioState(%d)", newState);
    RIL_RadioState oldState;

    pthread_mutex_lock(&s_state_mutex);

    oldState = sState;

    if (s_closed > 0) {
        // If we're closed, the only reasonable state is
        // RADIO_STATE_UNAVAILABLE
        // This is here because things on the main thread
        // may attempt to change the radio state after the closed
        // event happened in another thread
        newState = RADIO_STATE_UNAVAILABLE;
    }

    if (sState != newState || s_closed > 0) {
        sState = newState;

        pthread_cond_broadcast (&s_state_cond);
    }

    pthread_mutex_unlock(&s_state_mutex);


    /* do these outside of the mutex */
    if (sState != oldState) {
        RIL_onUnsolicitedResponse (RIL_UNSOL_RESPONSE_RADIO_STATE_CHANGED,
                                    NULL, 0);
        // Sim state can change as result of radio state change
        RIL_onUnsolicitedResponse (RIL_UNSOL_RESPONSE_SIM_STATUS_CHANGED,
                                    NULL, 0);

        /* FIXME onSimReady() and onRadioPowerOn() cannot be called
         * from the AT reader thread
         * Currently, this doesn't happen, but if that changes then these
         * will need to be dispatched on the request thread
         */
        if (sState == RADIO_STATE_ON) {
            onRadioPowerOn();
        }
    }
}
```
如果关闭radio就会调用RIL_onUnsolicitedResponse函数向RILC层上报。现在我们不看关闭radio的逻辑代码，我们来看看启动radio的逻辑代码

/hardware/ril/reference-ril/reference-ril.c
```c
/** do post-AT+CFUN=1 initialization */
static void onRadioPowerOn()
{
#ifdef USE_TI_COMMANDS
    /*  Must be after CFUN=1 */
    /*  TI specific -- notifications for CPHS things such */
    /*  as CPHS message waiting indicator */

    at_send_command("AT%CPHS=1", NULL);

    /*  TI specific -- enable NITZ unsol notifs */
    at_send_command("AT%CTZV=1", NULL);
#endif

    pollSIMState(NULL);
}
```
通过pollSIMState函数实现从RILC层到RIL层循环。我们来看看到底怎么实现的

 /hardware/ril/reference-ril/reference-ril.c
```c
/**
 * SIM ready means any commands that access the SIM will work, including:
 *  AT+CPIN, AT+CSMS, AT+CNMI, AT+CRSM
 *  (all SMS-related commands)
 */

static void pollSIMState (void *param __unused)
{
    ATResponse *p_response;
    int ret;

    if (sState != RADIO_STATE_SIM_NOT_READY) {
        // no longer valid to poll
        return;
    }

    switch(getSIMStatus()) {
        case SIM_ABSENT:
        case SIM_PIN:
        case SIM_PUK:
        case SIM_NETWORK_PERSONALIZATION:
        default:
            RLOGI("SIM ABSENT or LOCKED");
            RIL_onUnsolicitedResponse(RIL_UNSOL_RESPONSE_SIM_STATUS_CHANGED, NULL, 0);
        return;

        case SIM_NOT_READY:
            RIL_requestTimedCallback (pollSIMState, NULL, &TIMEVAL_SIMPOLL);
        return;

        case SIM_READY:
            RLOGI("SIM_READY");
            onSIMReady();
            RIL_onUnsolicitedResponse(RIL_UNSOL_RESPONSE_SIM_STATUS_CHANGED, NULL, 0);
        return;
    }
}
```
sim卡的状态为SIM_NOT_READY时，就会调用RIL_requestTimedCallback函数。看到这个函数是不是觉得很熟悉啊。没错，在之前RIL层的mainLoop路线线程中就是用到了这个函数，通过RILC层的RIL_requestTimedCallback函数和RIL层的pollSIMState函数，我们就实现了一个层与层之前的循环，从而不停的获取sim卡的最新状态。当sim卡的状态为SIM_READY，那么又会调用onSIMReady函数，向modem下发指令；调用RIL_onUnsolicitedResponse函数上报sim卡状态到RILC层。

/hardware/ril/reference-ril/reference-ril.c
```c
/** do post- SIM ready initialization */
static void onSIMReady()
{
    at_send_command_singleline("AT+CSMS=1", "+CSMS:", NULL);
    /*
     * Always send SMS messages directly to the TE
     *
     * mode = 1 // discard when link is reserved (link should never be
     *             reserved)
     * mt = 2   // most messages routed to TE
     * bm = 2   // new cell BM's routed to TE
     * ds = 1   // Status reports routed to TE
     * bfr = 1  // flush buffer
     */
    at_send_command("AT+CNMI=1,2,2,1,1", NULL);
}
```

==第五件事情：阻塞mainloop线程==

调用waitForClose函数阻塞mainloop线程，当at通道发生异常时，通过改变全局变量s_closed为1，就会进入下一次的for循环，重新调用at_open函数去打开at通道。如果s_closed为0说明at通道在使用


好的现在回到RILD层中，初始化完了ril层现在我们需要注册RILC层和RILJ层之前的通信方式

 /hardware/ril/libril/ril.cpp
```cpp
extern "C" void
RIL_register (const RIL_RadioFunctions *callbacks) {
    int ret;
    int flags;

    ...

    memcpy(&s_callbacks, callbacks, sizeof (RIL_RadioFunctions));

    /* Initialize socket1 parameters */
    s_ril_param_socket = {
                        RIL_SOCKET_1,             /* socket_id */
                        -1,                       /* fdListen */
                        -1,                       /* fdCommand */
                        PHONE_PROCESS,            /* processName */
                        &s_commands_event,        /* commands_event */
                        &s_listen_event,          /* listen_event */
                        processCommandsCallback,  /* processCommandsCallback */
                        NULL                      /* p_rs */
                        };

#if (SIM_COUNT >= 2)
    s_ril_param_socket2 = {
                        RIL_SOCKET_2,               /* socket_id */
                        -1,                         /* fdListen */
                        -1,                         /* fdCommand */
                        PHONE_PROCESS,              /* processName */
                        &s_commands_event_socket2,  /* commands_event */
                        &s_listen_event_socket2,    /* listen_event */
                        processCommandsCallback,    /* processCommandsCallback */
                        NULL                        /* p_rs */
                        };
#endif

...
    s_registerCalled = 1;

    RLOGI("s_registerCalled flag set, %d", s_started);
    // Little self-check

    for (int i = 0; i < (int)NUM_ELEMS(s_commands); i++) {
        assert(i == s_commands[i].requestNumber);
    }

    for (int i = 0; i < (int)NUM_ELEMS(s_unsolResponses); i++) {
        assert(i + RIL_UNSOL_RESPONSE_BASE
                == s_unsolResponses[i].requestNumber);
    }

    // New rild impl calls RIL_startEventLoop() first
    // old standalone impl wants it here.

    if (s_started == 0) {
        RIL_startEventLoop();
    }

    // start listen socket1
    startListen(RIL_SOCKET_1, &s_ril_param_socket);

#if (SIM_COUNT >= 2)
    // start listen socket2
    startListen(RIL_SOCKET_2, &s_ril_param_socket2);
#endif /* (SIM_COUNT == 2) */

...
}

```
有几张卡就会创建几个与RILJ层通信的socket.那么接下来就会启动服务端的socket，接受来至RILJ层的socket消息
```cpp
static void startListen(RIL_SOCKET_ID socket_id, SocketListenParam* socket_listen_p) {
    int fdListen = -1;
    int ret;
    char socket_name[10];

    memset(socket_name, 0, sizeof(char)*10);

    switch(socket_id) {
        case RIL_SOCKET_1:
            strncpy(socket_name, RIL_getRilSocketName(), 9);
            break;
    #if (SIM_COUNT >= 2)
        case RIL_SOCKET_2:
            strncpy(socket_name, SOCKET2_NAME_RIL, 9);
            break;
    #endif
    ...
        default:
            RLOGE("Socket id is wrong!!");
            return;
    }

    RLOGI("Start to listen %s", rilSocketIdToString(socket_id));

    fdListen = android_get_control_socket(socket_name);
    if (fdListen < 0) {
        RLOGE("Failed to get socket %s", socket_name);
        exit(-1);
    }

    ret = listen(fdListen, 4);

    if (ret < 0) {
        RLOGE("Failed to listen on control socket '%d': %s",
             fdListen, strerror(errno));
        exit(-1);
    }
    socket_listen_p->fdListen = fdListen;

    /* note: non-persistent so we can accept only one connection at a time */
    ril_event_set (socket_listen_p->listen_event, fdListen, false,
                listenCallback, socket_listen_p);

    rilEventAddWakeup (socket_listen_p->listen_event);
}
```

来看看SocketListenParam类型的结构体socket_listen_p的代码。其中的listen_event会被添加watch_tabel数组中。而我们都知道ril_event类型的结构体listen_event，保存着listenCallback函数指针和参数socket_listen_p指针以及fdListen文件描述符。listen_event只会在eventLoop轮询线程中执行一次，用来监听连接客户端后的逻辑判断

/hardware/ril/include/libril/ril_ex.h
```h
typedef struct SocketListenParam {
    RIL_SOCKET_ID socket_id;
    int fdListen;
    int fdCommand;
    char* processName;
    struct ril_event* commands_event;
    struct ril_event* listen_event;
    void (*processCommandsCallback)(int fd, short flags, void *param);
    RecordStream *p_rs;
    RIL_SOCKET_TYPE type;
} SocketListenParam;
```
当fdListen有变化时就会触发listenCallback函数

/hardware/ril/libril/ril.cpp
```cpp
static void listenCallback (int fd, short flags, void *param) {
    int ret;
    int err;
    int is_phone_socket;
    int fdCommand = -1;
    char* processName;
    RecordStream *p_rs;
    MySocketListenParam* listenParam;
    RilSocket *sapSocket = NULL;
    socketClient *sClient = NULL;

    SocketListenParam *p_info = (SocketListenParam *)param;

    if(RIL_SAP_SOCKET == p_info->type) {
        listenParam = (MySocketListenParam *)param;
        sapSocket = listenParam->socket;
    }

    struct sockaddr_un peeraddr;
    socklen_t socklen = sizeof (peeraddr);

    struct ucred creds;
    socklen_t szCreds = sizeof(creds);

    struct passwd *pwd = NULL;

    if(NULL == sapSocket) {
        assert (*p_info->fdCommand < 0);
        assert (fd == *p_info->fdListen);
        processName = PHONE_PROCESS;
    } else {
        assert (sapSocket->commandFd < 0);
        assert (fd == sapSocket->listenFd);
        processName = BLUETOOTH_PROCESS;
    }


    fdCommand = accept(fd, (sockaddr *) &peeraddr, &socklen);

    if (fdCommand < 0 ) {
        RLOGE("Error on accept() errno:%d", errno);
        /* start listening for new connections again */
        if(NULL == sapSocket) {
            rilEventAddWakeup(p_info->listen_event);
        } else {
            rilEventAddWakeup(sapSocket->getListenEvent());
        }
        return;
    }

    /* check the credential of the other side and only accept socket from
     * phone process
     */
    errno = 0;
    is_phone_socket = 0;

    err = getsockopt(fdCommand, SOL_SOCKET, SO_PEERCRED, &creds, &szCreds);

    if (err == 0 && szCreds > 0) {
        errno = 0;
        pwd = getpwuid(creds.uid);
        if (pwd != NULL) {
            if (strcmp(pwd->pw_name, processName) == 0) {
                is_phone_socket = 1;
            } else {
                RLOGE("RILD can't accept socket from process %s", pwd->pw_name);
            }
        } else {
            RLOGE("Error on getpwuid() errno: %d", errno);
        }
    } else {
        RLOGD("Error on getsockopt() errno: %d", errno);
    }

    if (!is_phone_socket) {
        RLOGE("RILD must accept socket from %s", processName);

        close(fdCommand);
        fdCommand = -1;

        if(NULL == sapSocket) {
            onCommandsSocketClosed(p_info->socket_id);

            /* start listening for new connections again */
            rilEventAddWakeup(p_info->listen_event);
        } else {
            sapSocket->onCommandsSocketClosed();

            /* start listening for new connections again */
            rilEventAddWakeup(sapSocket->getListenEvent());
        }

        return;
    }

    ret = fcntl(fdCommand, F_SETFL, O_NONBLOCK);

    if (ret < 0) {
        RLOGE ("Error setting O_NONBLOCK errno:%d", errno);
    }

    if(NULL == sapSocket) {
        RLOGI("libril: new connection to %s", rilSocketIdToString(p_info->socket_id));

        p_info->fdCommand = fdCommand;
        p_rs = record_stream_new(p_info->fdCommand, MAX_COMMAND_BYTES);
        p_info->p_rs = p_rs;

        ril_event_set (p_info->commands_event, p_info->fdCommand, 1,
        p_info->processCommandsCallback, p_info);
        rilEventAddWakeup (p_info->commands_event);

        onNewCommandConnect(p_info->socket_id);
    } else {
        RLOGI("libril: new connection");

        sapSocket->setCommandFd(fdCommand);
        p_rs = record_stream_new(sapSocket->getCommandFd(), MAX_COMMAND_BYTES);
        sClient = new socketClient(sapSocket,p_rs);
        ril_event_set (sapSocket->getCallbackEvent(), sapSocket->getCommandFd(), 1,
        sapSocket->getCommandCb(), sClient);

        rilEventAddWakeup(sapSocket->getCallbackEvent());
        sapSocket->onNewCommandConnect();
    }
}

```

通过accept函数接受到了RILJ层传过来的at指令。对指令进行解析之后会调用ril_event_set，创建用于监听fdCommand变化的commands事件，其对应的回调函数为processCommandsCallback，在调用ril_event_add，将其推到watch_table数组中里面。如果RILJ层下发了at指令，就会回到回调processCommandsCallback函数

/hardware/ril/libril/ril.cpp
```cpp
static void processCommandsCallback(int fd, short flags, void *param) {
    RecordStream *p_rs;
    void *p_record;
    size_t recordlen;
    int ret;
    SocketListenParam *p_info = (SocketListenParam *)param;

    assert(fd == p_info->fdCommand);

    p_rs = p_info->p_rs;

    for (;;) {
        /* loop until EAGAIN/EINTR, end of stream, or other error */
        ret = record_stream_get_next(p_rs, &p_record, &recordlen);

        if (ret == 0 && p_record == NULL) {
            /* end-of-stream */
            break;
        } else if (ret < 0) {
            break;
        } else if (ret == 0) { /* && p_record != NULL */
            processCommandBuffer(p_record, recordlen, p_info->socket_id);
        }
    }

    if (ret == 0 || !(errno == EAGAIN || errno == EINTR)) {
        /* fatal error or end-of-stream */
        if (ret != 0) {
            RLOGE("error on reading command socket errno:%d\n", errno);
        } else {
            RLOGW("EOS.  Closing command socket.");
        }

        close(fd);
        p_info->fdCommand = -1;

        ril_event_del(p_info->commands_event);

        record_stream_free(p_rs);

        /* start listening for new connections again */
        rilEventAddWakeup(&s_listen_event);

        onCommandsSocketClosed(p_info->socket_id);
    }
}
```

那么接着就是会利用一个轮询循环解析processCommandBuffer。并且下发at指令到modem

/hardware/ril/libril/ril.cpp
```cpp
static int
processCommandBuffer(void *buffer, size_t buflen, RIL_SOCKET_ID socket_id) {
    Parcel p;
    status_t status;
    int32_t request;
    int32_t token;
    RequestInfo *pRI;
    int ret;
    /* Hook for current context */
    /* pendingRequestsMutextHook refer to &s_pendingRequestsMutex */
    pthread_mutex_t* pendingRequestsMutexHook = &s_pendingRequestsMutex;
    /* pendingRequestsHook refer to &s_pendingRequests */
    RequestInfo**    pendingRequestsHook = &s_pendingRequests;

    p.setData((uint8_t *) buffer, buflen);

    // status checked at end
    status = p.readInt32(&request);
    status = p.readInt32 (&token);

#if (SIM_COUNT >= 2)
    if (socket_id == RIL_SOCKET_2) {
        pendingRequestsMutexHook = &s_pendingRequestsMutex_socket2;
        pendingRequestsHook = &s_pendingRequests_socket2;
    }
#if (SIM_COUNT >= 3)
    else if (socket_id == RIL_SOCKET_3) {
        pendingRequestsMutexHook = &s_pendingRequestsMutex_socket3;
        pendingRequestsHook = &s_pendingRequests_socket3;
    }
#endif
#if (SIM_COUNT >= 4)
    else if (socket_id == RIL_SOCKET_4) {
        pendingRequestsMutexHook = &s_pendingRequestsMutex_socket4;
        pendingRequestsHook = &s_pendingRequests_socket4;
    }
#endif
#endif

    if (status != NO_ERROR) {
        RLOGE("invalid request block");
        return 0;
    }

    // Received an Ack for the previous result sent to RIL.java,
    // so release wakelock and exit
    if (request == RIL_RESPONSE_ACKNOWLEDGEMENT) {
        releaseWakeLock();
        return 0;
    }

    if (request < 1 || request >= (int32_t)NUM_ELEMS(s_commands)) {
        Parcel pErr;
        RLOGE("unsupported request code %d token %d", request, token);
        // FIXME this should perhaps return a response
        pErr.writeInt32 (RESPONSE_SOLICITED);
        pErr.writeInt32 (token);
        pErr.writeInt32 (RIL_E_GENERIC_FAILURE);

        sendResponse(pErr, socket_id);
        return 0;
    }

    pRI = (RequestInfo *)calloc(1, sizeof(RequestInfo));
    if (pRI == NULL) {
        RLOGE("Memory allocation failed for request %s", requestToString(request));
        return 0;
    }

    pRI->token = token;
    pRI->pCI = &(s_commands[request]);
    pRI->socket_id = socket_id;

    ret = pthread_mutex_lock(pendingRequestsMutexHook);
    assert (ret == 0);

    pRI->p_next = *pendingRequestsHook;
    *pendingRequestsHook = pRI;

    ret = pthread_mutex_unlock(pendingRequestsMutexHook);
    assert (ret == 0);

/*    sLastDispatchedToken = token; */

    pRI->pCI->dispatchFunction(p, pRI);

    return 0;
}
```
最后通过dispatchFunction(p, pRI)实现下发at指令




/hardware/ril/libril/ril.cpp
```cpp

static void onNewCommandConnect(RIL_SOCKET_ID socket_id) {
    // Inform we are connected and the ril version
    int rilVer = s_callbacks.version;
    RIL_UNSOL_RESPONSE(RIL_UNSOL_RIL_CONNECTED,
                                    &rilVer, sizeof(rilVer), socket_id);

    // implicit radio state changed
    RIL_UNSOL_RESPONSE(RIL_UNSOL_RESPONSE_RADIO_STATE_CHANGED,
                                    NULL, 0, socket_id);

    // Send last NITZ time data, in case it was missed
    if (s_lastNITZTimeData != NULL) {
        sendResponseRaw(s_lastNITZTimeData, s_lastNITZTimeDataSize, socket_id);

        free(s_lastNITZTimeData);
        s_lastNITZTimeData = NULL;
    }

    // Get version string
    if (s_callbacks.getVersion != NULL) {
        const char *version;
        version = s_callbacks.getVersion();
        RLOGI("RIL Daemon version: %s\n", version);

        property_set(PROPERTY_RIL_IMPL, version);
    } else {
        RLOGI("RIL Daemon version: unavailable\n");
        property_set(PROPERTY_RIL_IMPL, "unavailable");
    }

}
```













RIL_register_socket(rilUimInit, RIL_SAP_SOCKET, argc, rilArgv);

 /hardware/ril/libril/ril.cpp
```cpp
extern "C" void
RIL_register_socket (RIL_RadioFunctions *(*Init)(const struct RIL_Env *, int, char **),RIL_SOCKET_TYPE socketType, int argc, char **argv) {

    RIL_RadioFunctions* UimFuncs = NULL;

    if(Init) {
        UimFuncs = Init(&RilSapSocket::uimRilEnv, argc, argv);

        switch(socketType) {
            case RIL_SAP_SOCKET:
                RilSapSocket::initSapSocket("sap_uim_socket1", UimFuncs);

#if (SIM_COUNT >= 2)
                RilSapSocket::initSapSocket("sap_uim_socket2", UimFuncs);
#endif

#if (SIM_COUNT >= 3)
                RilSapSocket::initSapSocket("sap_uim_socket3", UimFuncs);
#endif

#if (SIM_COUNT >= 4)
                RilSapSocket::initSapSocket("sap_uim_socket4", UimFuncs);
#endif
        }
    }
}
```

# RIL层的回调函数

 /hardware/ril/reference-ril/reference-ril.c
```c
/* Called on command or reader thread */
static void onATReaderClosed()
{
    RLOGI("AT channel closed\n");
    at_close();
    s_closed = 1;

    setRadioState (RADIO_STATE_UNAVAILABLE);
}

/* Called on command thread */
static void onATTimeout()
{
    ...
}
...
static void
setRadioState(RIL_RadioState newState)
{
    RLOGD("setRadioState(%d)", newState);
    RIL_RadioState oldState;

    pthread_mutex_lock(&s_state_mutex);

    oldState = sState;

    if (s_closed > 0) {
        // If we're closed, the only reasonable state is
        // RADIO_STATE_UNAVAILABLE
        // This is here because things on the main thread
        // may attempt to change the radio state after the closed
        // event happened in another thread
        newState = RADIO_STATE_UNAVAILABLE;
    }

    if (sState != newState || s_closed > 0) {
        sState = newState;

        pthread_cond_broadcast (&s_state_cond);
    }

    pthread_mutex_unlock(&s_state_mutex);


    /* do these outside of the mutex */
    if (sState != oldState) {
        RIL_onUnsolicitedResponse (RIL_UNSOL_RESPONSE_RADIO_STATE_CHANGED,
                                    NULL, 0);
        // Sim state can change as result of radio state change
        RIL_onUnsolicitedResponse (RIL_UNSOL_RESPONSE_SIM_STATUS_CHANGED,
                                    NULL, 0);

        /* FIXME onSimReady() and onRadioPowerOn() cannot be called
         * from the AT reader thread
         * Currently, this doesn't happen, but if that changes then these
         * will need to be dispatched on the request thread
         */
        if (sState == RADIO_STATE_ON) {
            onRadioPowerOn();
        }
    }
}
...
```

onATTimeout和onATReaderClosed函数的实现是一样的，都是先关闭at通道，然后将radio状态置为RADIO_STATE_UNAVAILABLE。RILD、RILC、RIL层中radio的状态主要是有11中。如下代码有详细的描述。

/hardware/ril/reference-ril/ril.h
```h
typedef enum {
    RADIO_STATE_OFF = 0,                   /* Radio explictly powered off (eg CFUN=0) */
    RADIO_STATE_UNAVAILABLE = 1,           /* Radio unavailable (eg, resetting or not booted) */
    /* States 2-9 below are deprecated. Just leaving them here for backward compatibility. */
    RADIO_STATE_SIM_NOT_READY = 2,         /* Radio is on, but the SIM interface is not ready */
    RADIO_STATE_SIM_LOCKED_OR_ABSENT = 3,  /* SIM PIN locked, PUK required, network
                                              personalization locked, or SIM absent */
    RADIO_STATE_SIM_READY = 4,             /* Radio is on and SIM interface is available */
    RADIO_STATE_RUIM_NOT_READY = 5,        /* Radio is on, but the RUIM interface is not ready */
    RADIO_STATE_RUIM_READY = 6,            /* Radio is on and the RUIM interface is available */
    RADIO_STATE_RUIM_LOCKED_OR_ABSENT = 7, /* RUIM PIN locked, PUK required, network
                                              personalization locked, or RUIM absent */
    RADIO_STATE_NV_NOT_READY = 8,          /* Radio is on, but the NV interface is not available */
    RADIO_STATE_NV_READY = 9,              /* Radio is on and the NV interface is available */
    RADIO_STATE_ON = 10                    /* Radio is on */
} RIL_RadioState;
```
在RIL层改变当前的radio状态为不可用后，会向RILC层上传两个消息RIL_UNSOL_RESPONSE_RADIO_STATE_CHANGED、RIL_UNSOL_RESPONSE_SIM_STATUS_CHANGED，RILC层会对其包装在上传到RILJ上层。如果radio之前的状态是打开的话，程序会相对应的查询sim的状态。


/hardware/ril/reference-ril/reference-ril.c
```c
/** do post-AT+CFUN=1 initialization */
static void onRadioPowerOn()
{
#ifdef USE_TI_COMMANDS
    /*  Must be after CFUN=1 */
    /*  TI specific -- notifications for CPHS things such */
    /*  as CPHS message waiting indicator */

    at_send_command("AT%CPHS=1", NULL);

    /*  TI specific -- enable NITZ unsol notifs */
    at_send_command("AT%CTZV=1", NULL);
#endif

    pollSIMState(NULL);

/**
 * SIM ready means any commands that access the SIM will work, including:
 *  AT+CPIN, AT+CSMS, AT+CNMI, AT+CRSM
 *  (all SMS-related commands)
 */

static void pollSIMState (void *param __unused)
{
    ATResponse *p_response;
    int ret;

    if (sState != RADIO_STATE_SIM_NOT_READY) {
        // no longer valid to poll
        return;
    }

    switch(getSIMStatus()) {
        case SIM_ABSENT:
        case SIM_PIN:
        case SIM_PUK:
        case SIM_NETWORK_PERSONALIZATION:
        default:
            RLOGI("SIM ABSENT or LOCKED");
            RIL_onUnsolicitedResponse(RIL_UNSOL_RESPONSE_SIM_STATUS_CHANGED, NULL, 0);
        return;

        case SIM_NOT_READY:
            RIL_requestTimedCallback (pollSIMState, NULL, &TIMEVAL_SIMPOLL);
        return;

        case SIM_READY:
            RLOGI("SIM_READY");
            onSIMReady();
            RIL_onUnsolicitedResponse(RIL_UNSOL_RESPONSE_SIM_STATUS_CHANGED, NULL, 0);
        return;
    }
}

```


onUnsolicited


# pending_list双链表


初始化链表
```cpp
static void init_list(struct ril_event * list)
{
    memset(list, 0, sizeof(struct ril_event));
    list->next = list;
    list->prev = list;
    list->fd = -1;
}
```

初始化链表中的根节点。将根节点中的next、prev指针都指向了自己


插入数据到链表
```cpp
static void addToList(struct ril_event * ev, struct ril_event * list)
{
    ev->next = list;
    ev->prev = list->prev;
    ev->prev->next = ev;
    list->prev = ev;
    dump_event(ev);
}
```
addToList函数有两个形参，一个是当前想要插入的ev数据，另一个为根节点。通过根节点的prev指针和当前节点的next指针来控制输入的插入。
如图所示各个节点指针的操作顺序如第三张图


从链表删除数据
```cpp
static void removeFromList(struct ril_event * ev)
{
    dlog("~~~~ +removeFromList ~~~~");
    dump_event(ev);

    ev->next->prev = ev->prev;
    ev->prev->next = ev->next;
    ev->next = NULL;
    ev->prev = NULL;
    dlog("~~~~ -removeFromList ~~~~");
}
```
图四中删除的顺序：
1.将根节点的prev指针重新指向到被删除的前一个节点
2.将被删除的前一个节点中next指针重新指向根节点
3.要删除的节点next、prev指针置空

# 参考资料

- [Modem简单流程及案例分析V1.0]({{site.baseurl}}/asset/android-framework/Modem简单流程及案例分析V1.0.pdf)
- [RIL_command_flow.chm]({{site.baseurl}}/asset/android-framework/RIL_command_flow.chm)
- [VOIP protocol stack.pdf]({{site.baseurl}}/asset/android-framework/VOIP_protocol_stack.pdf)
- [3962019479.jpg]({{site.baseurl}}/asset/android-framework/3962019479.jpg)
- [AT命令集详解](http://blog.csdn.net/gujing001/article/details/7936812)
- [pstn网络与modem的关系](https://books.google.co.jp/books?id=IidbMC2LgvIC&pg=PA174&lpg=PA174&dq=modem%E5%8D%8F%E8%AE%AE&source=bl&ots=6GH0cKerRU&sig=jHzwvv6Lgf3oiHuiHBAnDJTkEgM&hl=en&sa=X&ved=0ahUKEwiO5KX7mObVAhUCUbwKHZJuB3gQ6AEIRzAF#v=onepage&q=modem%E5%8D%8F%E8%AE%AE&f=false)
- [modem中的协议族](http://blog.csdn.net/sjz4860402/article/details/40744113)
- [深入理解Android Telephony之RILD的启动](http://blog.csdn.net/mathcompfrac/article/details/53872191)


