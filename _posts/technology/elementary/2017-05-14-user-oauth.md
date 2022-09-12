---
layout: post
title: Android的Account机制
description: 
date: 2017-05-14
share: true
comments: true
tag: elementary/other

---
## *1.Summary*{:.header2-font}
&emsp;&emsp;
## *2.About*{:.header2-font}
&emsp;&emsp;我们都知道微信客户端和微信服务端直接交互数据需要账号和密码，而如果第三方应用想要以微信的账号登入时，就需要第三方应用使用OAuth协议向微信服务端申请token，有个这个token就可以访问微信服务端的资源。这种方案替代了第三方应用通过输入账号和密码向微信服务器交互数据，可以保证不让第三方应用知道账号和密码。再看看Android平台默认提供的Account机制。不清楚的可以看看这个[文章](http://kohoh1992.github.io/AndroidAccountsGuide)。OAuth的使用在C/S和B/S模式上都有，而OAuth在Android平台中却是基于C/C，就是Account机制。客户端还是第三方应用，而服务端确是Android平台上的应用，比如Email。真是有点畸形，不过我们应该回到OAuth在C/S和B/S模式上的机制，再来看Android中基于C/C模式的Account机制。
## *3.Introduction*{:.header2-font}
资料看完了，有空再来填坑。


![authentication flowchart]({{site.baseurl}}/asset/network/authentication_flowchart.png){:.white-bg-image}


## *4.Reference*{:.header2-font}
[OAuth官网](https://oauth.net/2/)
[google服务器OAuth](https://developers.google.com/identity/protocols/OAuth2)
[google服务器OAuth](https://open.weixin.qq.com/cgi-bin/showdocument?action=dir_list&t=resource/res_list&verify=1&id=open1453779503&token=&lang=zh_CN)
[理解OAuth 2.0](http://www.ruanyifeng.com/blog/2014/05/oauth_2_0.html)
[第三方授权 api](https://developer.android.com/reference/android/accounts/AccountManager.html)
[Write your own Android Authenticator](http://blog.udinic.com/2013/04/24/write-your-own-android-authenticator/)
[Write your own Android Authenticator中文版](http://kohoh1992.github.io/AndroidAccountsGuide)
