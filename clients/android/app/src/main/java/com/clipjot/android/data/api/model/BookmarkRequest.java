package com.clipjot.android.data.api.model;

import com.google.gson.annotations.SerializedName;
import java.util.List;

/**
 * Request body for /api/v1/bookmarks/add endpoint.
 */
public class BookmarkRequest {

    @SerializedName("url")
    private String url;

    @SerializedName("title")
    private String title;

    @SerializedName("comment")
    private String comment;

    @SerializedName("tags")
    private List<String> tags;

    @SerializedName("client_name")
    private String clientName = "android";

    public BookmarkRequest() {
    }

    public BookmarkRequest(String url, String title, String comment, List<String> tags) {
        this.url = url;
        this.title = title;
        this.comment = comment;
        this.tags = tags;
        this.clientName = "android";
    }

    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getComment() {
        return comment;
    }

    public void setComment(String comment) {
        this.comment = comment;
    }

    public List<String> getTags() {
        return tags;
    }

    public void setTags(List<String> tags) {
        this.tags = tags;
    }

    public String getClientName() {
        return clientName;
    }

    public void setClientName(String clientName) {
        this.clientName = clientName;
    }
}
