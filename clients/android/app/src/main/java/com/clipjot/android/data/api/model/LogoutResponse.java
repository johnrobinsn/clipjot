package com.clipjot.android.data.api.model;

import com.google.gson.annotations.SerializedName;

/**
 * Response model for logout API.
 */
public class LogoutResponse {

    @SerializedName("logged_out")
    private boolean loggedOut;

    @SerializedName("message")
    private String message;

    public boolean isLoggedOut() {
        return loggedOut;
    }

    public String getMessage() {
        return message;
    }
}
