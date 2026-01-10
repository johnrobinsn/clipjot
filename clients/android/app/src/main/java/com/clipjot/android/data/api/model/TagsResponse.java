package com.clipjot.android.data.api.model;

import com.google.gson.annotations.SerializedName;
import java.util.List;

/**
 * Response from /api/v1/tags/list endpoint.
 */
public class TagsResponse {

    @SerializedName("tags")
    private List<Tag> tags;

    public TagsResponse() {
    }

    public List<Tag> getTags() {
        return tags;
    }

    public void setTags(List<Tag> tags) {
        this.tags = tags;
    }
}
