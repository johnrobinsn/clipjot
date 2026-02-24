package com.clipjot.android.data.api.model;

import com.google.gson.annotations.SerializedName;

/**
 * Response model for user profile endpoint.
 */
public class UserProfileResponse {

    @SerializedName("email")
    private String email;

    @SerializedName("provider")
    private String provider;

    @SerializedName("is_premium")
    private int isPremium;

    @SerializedName("created_at")
    private String createdAt;

    public String getEmail() {
        return email;
    }

    public String getProvider() {
        return provider;
    }

    public boolean isPremium() {
        return isPremium != 0;
    }

    public String getCreatedAt() {
        return createdAt;
    }
}
