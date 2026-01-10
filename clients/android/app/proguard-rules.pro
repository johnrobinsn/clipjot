# Retrofit
-keepattributes Signature
-keepattributes *Annotation*
-keep class retrofit2.** { *; }
-keepclasseswithmembers class * {
    @retrofit2.http.* <methods>;
}

# Gson
-keepattributes Signature
-keep class com.clipjot.android.data.api.model.** { *; }

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**
