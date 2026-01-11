package com.clipjot.android.data.prefs;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.security.crypto.EncryptedSharedPreferences;
import androidx.security.crypto.MasterKey;

import java.io.IOException;
import java.security.GeneralSecurityException;

/**
 * Secure token storage using EncryptedSharedPreferences.
 */
public class TokenManager {

    private static final String PREFS_NAME = "clipjot_secure_prefs";
    private static final String KEY_TOKEN = "session_token";

    private final SharedPreferences prefs;

    public TokenManager(Context context) {
        try {
            MasterKey masterKey = new MasterKey.Builder(context)
                    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                    .build();

            prefs = EncryptedSharedPreferences.create(
                    context,
                    PREFS_NAME,
                    masterKey,
                    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
            );
        } catch (GeneralSecurityException | IOException e) {
            throw new RuntimeException("Failed to initialize secure storage", e);
        }
    }

    /**
     * Save the session token.
     */
    public void saveToken(String token) {
        prefs.edit().putString(KEY_TOKEN, token).apply();
    }

    /**
     * Get the stored session token.
     */
    public String getToken() {
        return prefs.getString(KEY_TOKEN, null);
    }

    /**
     * Check if a valid token exists.
     */
    public boolean hasToken() {
        String token = getToken();
        return token != null && !token.isEmpty();
    }

    /**
     * Clear the stored token (logout).
     * Uses commit() for synchronous write to ensure token is cleared immediately.
     */
    public void clearToken() {
        prefs.edit().remove(KEY_TOKEN).commit();
    }
}
