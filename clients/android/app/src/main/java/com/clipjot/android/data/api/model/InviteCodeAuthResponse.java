package com.clipjot.android.data.api.model;

import com.google.gson.annotations.SerializedName;

/**
 * Response model for invite code authentication.
 */
public class InviteCodeAuthResponse {

    @SerializedName("token")
    private String token;

    @SerializedName("user")
    private User user;

    public String getToken() {
        return token;
    }

    public User getUser() {
        return user;
    }

    /**
     * Nested user object in auth response.
     */
    public static class User {
        @SerializedName("id")
        private int id;

        @SerializedName("email")
        private String email;

        public int getId() {
            return id;
        }

        public String getEmail() {
            return email;
        }
    }
}
