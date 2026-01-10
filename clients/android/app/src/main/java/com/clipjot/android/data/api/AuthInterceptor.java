package com.clipjot.android.data.api;

import android.content.Context;

import com.clipjot.android.data.prefs.TokenManager;

import java.io.IOException;

import okhttp3.Interceptor;
import okhttp3.Request;
import okhttp3.Response;

/**
 * OkHttp interceptor that adds Bearer token authentication header.
 */
public class AuthInterceptor implements Interceptor {

    private final TokenManager tokenManager;

    public AuthInterceptor(Context context) {
        this.tokenManager = new TokenManager(context);
    }

    @Override
    public Response intercept(Chain chain) throws IOException {
        Request original = chain.request();

        String token = tokenManager.getToken();
        if (token == null || token.isEmpty()) {
            return chain.proceed(original);
        }

        Request.Builder builder = original.newBuilder()
                .header("Authorization", "Bearer " + token)
                .header("Content-Type", "application/json");

        return chain.proceed(builder.build());
    }
}
