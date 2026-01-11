package com.clipjot.android.data.api.model;

import com.google.gson.annotations.SerializedName;

/**
 * Response from /api/v1/bookmarks/delete endpoint.
 */
public class DeleteResponse {

    @SerializedName("deleted")
    private boolean deleted;

    public DeleteResponse() {
    }

    public boolean isDeleted() {
        return deleted;
    }

    public void setDeleted(boolean deleted) {
        this.deleted = deleted;
    }
}
