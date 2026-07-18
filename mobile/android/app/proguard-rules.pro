-keepattributes *Annotation*
-keepclassmembers class ** {
    @org.greenrobot.eventbus.Subscribe <methods>;
}
-keep enum org.greenrobot.eventbus.ThreadMode { *; }

# React Native
-keep class com.facebook.react.** { *; }
-keep class com.ashamy.** { *; }
