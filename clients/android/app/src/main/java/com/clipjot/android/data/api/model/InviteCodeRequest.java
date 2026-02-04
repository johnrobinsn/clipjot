package com.clipjot.android.data.api.model;

import com.google.gson.annotations.SerializedName;

/**
 * Request model for invite code authentication.
 */
public class InviteCodeRequest {

    @SerializedName("code")
    private String code;

    @SerializedName("client_name")
    private String clientName;

    public InviteCodeRequest(String code) {
        this.code = code;
        this.clientName = "android";
    }

    public String getCode() {
        return code;
    }

    public String getClientName() {
        return clientName;
    }
}
