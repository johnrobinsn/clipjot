package com.clipjot.android.data.api.model;

import com.google.gson.annotations.SerializedName;

/**
 * Response model for the latest bookmark ID endpoint.
 * Used to detect when bookmarks have been added or edited.
 */
public class LatestBookmarkResponse {

    @SerializedName("id")
    private Integer id;

    @SerializedName("last_updated")
    private String lastUpdated;

    public Integer getId() {
        return id;
    }

    public String getLastUpdated() {
        return lastUpdated;
    }
}
