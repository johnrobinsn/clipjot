package com.clipjot.android.data.api.model;

import com.google.gson.annotations.SerializedName;

/**
 * Error response format from ClipJot API.
 */
public class ApiError {

    @SerializedName("error")
    private String error;

    @SerializedName("code")
    private String code;

    public ApiError() {
    }

    public ApiError(String error, String code) {
        this.error = error;
        this.code = code;
    }

    public String getError() {
        return error;
    }

    public void setError(String error) {
        this.error = error;
    }

    public String getCode() {
        return code;
    }

    public void setCode(String code) {
        this.code = code;
    }

    /**
     * Check if this is an authentication error.
     */
    public boolean isAuthError() {
        return "INVALID_TOKEN".equals(code) || "PERMISSION_DENIED".equals(code);
    }

    /**
     * Check if this is a rate limit error.
     */
    public boolean isRateLimited() {
        return "RATE_LIMITED".equals(code);
    }

    /**
     * Check if this is a validation error.
     */
    public boolean isValidationError() {
        return "VALIDATION_ERROR".equals(code);
    }
}
