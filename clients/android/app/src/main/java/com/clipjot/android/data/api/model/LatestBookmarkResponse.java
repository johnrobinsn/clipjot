package com.clipjot.android.data.api.model;

import com.google.gson.annotations.SerializedName;

/**
 * Response model for the latest bookmark ID endpoint.
 * Used to detect when new bookmarks have been added.
 */
public class LatestBookmarkResponse {

    @SerializedName("id")
    private Integer id;

    public Integer getId() {
        return id;
    }
}
