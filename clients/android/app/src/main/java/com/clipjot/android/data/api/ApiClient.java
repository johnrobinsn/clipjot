package com.clipjot.android.data.api;

import android.content.Context;

import com.clipjot.android.data.api.model.ApiError;
import com.clipjot.android.data.prefs.SettingsManager;
import com.google.gson.Gson;

import java.util.concurrent.TimeUnit;

import okhttp3.OkHttpClient;
import okhttp3.ResponseBody;
import okhttp3.logging.HttpLoggingInterceptor;
import retrofit2.Response;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

/**
 * Singleton API client for ClipJot backend.
 */
public class ApiClient {

    private static final String DEFAULT_BACKEND_URL = "http://localhost:5001";
    private static ClipJotApi api;
    private static String currentBaseUrl;
    private static final Gson gson = new Gson();

    /**
     * Get the API instance, creating or rebuilding if URL changed.
     */
    public static synchronized ClipJotApi getApi(Context context) {
        String baseUrl = getBackendUrl(context);

        // Rebuild client if URL changed
        if (api == null || !baseUrl.equals(currentBaseUrl)) {
            currentBaseUrl = baseUrl;

            HttpLoggingInterceptor logging = new HttpLoggingInterceptor();
            logging.setLevel(HttpLoggingInterceptor.Level.BODY);

            OkHttpClient client = new OkHttpClient.Builder()
                    .addInterceptor(new AuthInterceptor(context))
                    .addInterceptor(logging)
                    .connectTimeout(30, TimeUnit.SECONDS)
                    .readTimeout(30, TimeUnit.SECONDS)
                    .writeTimeout(30, TimeUnit.SECONDS)
                    .build();

            Retrofit retrofit = new Retrofit.Builder()
                    .baseUrl(normalizeUrl(baseUrl))
                    .client(client)
                    .addConverterFactory(GsonConverterFactory.create())
                    .build();

            api = retrofit.create(ClipJotApi.class);
        }
        return api;
    }

    /**
     * Reset the client (call when backend URL changes).
     */
    public static synchronized void resetClient() {
        api = null;
        currentBaseUrl = null;
    }

    /**
     * Get the configured backend URL.
     */
    public static String getBackendUrl(Context context) {
        SettingsManager settings = new SettingsManager(context);
        String url = settings.getBackendUrl();
        return (url != null && !url.isEmpty()) ? url : DEFAULT_BACKEND_URL;
    }

    /**
     * Normalize URL to ensure it ends with a single slash.
     */
    private static String normalizeUrl(String url) {
        if (url == null || url.isEmpty()) {
            return DEFAULT_BACKEND_URL + "/";
        }
        return url.replaceAll("/+$", "") + "/";
    }

    /**
     * Parse error response body into ApiError.
     */
    public static ApiError parseError(Response<?> response) {
        try {
            ResponseBody errorBody = response.errorBody();
            if (errorBody != null) {
                return gson.fromJson(errorBody.charStream(), ApiError.class);
            }
        } catch (Exception e) {
            // Fallback to generic error
        }
        return new ApiError("An error occurred", "UNKNOWN");
    }

    /**
     * Parse error response body into ApiError.
     */
    public static ApiError parseError(ResponseBody errorBody) {
        try {
            if (errorBody != null) {
                return gson.fromJson(errorBody.charStream(), ApiError.class);
            }
        } catch (Exception e) {
            // Fallback to generic error
        }
        return new ApiError("An error occurred", "UNKNOWN");
    }
}
