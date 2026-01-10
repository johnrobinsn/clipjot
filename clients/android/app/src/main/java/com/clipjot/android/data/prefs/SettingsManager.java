package com.clipjot.android.data.prefs;

import android.content.Context;
import android.content.SharedPreferences;

import com.clipjot.android.BuildConfig;

/**
 * Non-sensitive settings storage using regular SharedPreferences.
 */
public class SettingsManager {

    private static final String PREFS_NAME = "clipjot_settings";
    private static final String KEY_BACKEND_URL = "backend_url";
    private static final String KEY_PENDING_URL = "pending_bookmark_url";
    private static final String KEY_PENDING_TITLE = "pending_bookmark_title";
    private static final String KEY_USER_EMAIL = "user_email";
    private static final String KEY_PANEL_EXPANDED = "panel_expanded";

    private final SharedPreferences prefs;

    public SettingsManager(Context context) {
        prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    /**
     * Get the configured backend URL.
     */
    public String getBackendUrl() {
        return prefs.getString(KEY_BACKEND_URL, BuildConfig.DEFAULT_BACKEND_URL);
    }

    /**
     * Set the backend URL.
     */
    public void setBackendUrl(String url) {
        // Remove trailing slashes
        String normalizedUrl = url != null ? url.replaceAll("/+$", "") : BuildConfig.DEFAULT_BACKEND_URL;
        prefs.edit().putString(KEY_BACKEND_URL, normalizedUrl).apply();
    }

    /**
     * Store a pending bookmark (when user needs to login first).
     */
    public void setPendingBookmark(String url, String title) {
        prefs.edit()
                .putString(KEY_PENDING_URL, url)
                .putString(KEY_PENDING_TITLE, title)
                .apply();
    }

    /**
     * Check if there's a pending bookmark.
     */
    public boolean hasPendingBookmark() {
        return prefs.getString(KEY_PENDING_URL, null) != null;
    }

    /**
     * Get the pending bookmark URL.
     */
    public String getPendingBookmarkUrl() {
        return prefs.getString(KEY_PENDING_URL, null);
    }

    /**
     * Get the pending bookmark title.
     */
    public String getPendingBookmarkTitle() {
        return prefs.getString(KEY_PENDING_TITLE, null);
    }

    /**
     * Clear the pending bookmark.
     */
    public void clearPendingBookmark() {
        prefs.edit()
                .remove(KEY_PENDING_URL)
                .remove(KEY_PENDING_TITLE)
                .apply();
    }

    /**
     * Store the user's email (for display in settings).
     */
    public void setUserEmail(String email) {
        prefs.edit().putString(KEY_USER_EMAIL, email).apply();
    }

    /**
     * Get the stored user email.
     */
    public String getUserEmail() {
        return prefs.getString(KEY_USER_EMAIL, null);
    }

    /**
     * Clear all user data (logout).
     */
    public void clearUserData() {
        prefs.edit()
                .remove(KEY_USER_EMAIL)
                .remove(KEY_PENDING_URL)
                .remove(KEY_PENDING_TITLE)
                .apply();
    }

    /**
     * Get the panel expanded state (defaults to true).
     */
    public boolean isPanelExpanded() {
        return prefs.getBoolean(KEY_PANEL_EXPANDED, true);
    }

    /**
     * Set the panel expanded state.
     */
    public void setPanelExpanded(boolean expanded) {
        prefs.edit().putBoolean(KEY_PANEL_EXPANDED, expanded).apply();
    }

    /**
     * Reset all settings to defaults (keeps user logged in).
     */
    public void resetToDefaults() {
        prefs.edit()
                .remove(KEY_BACKEND_URL)
                .remove(KEY_PANEL_EXPANDED)
                .apply();
    }
}
