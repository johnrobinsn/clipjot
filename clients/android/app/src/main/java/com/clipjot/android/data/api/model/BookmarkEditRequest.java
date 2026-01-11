package com.clipjot.android.data.api.model;

import com.google.gson.annotations.SerializedName;
import java.util.List;

/**
 * Request body for /api/v1/bookmarks/edit endpoint.
 */
public class BookmarkEditRequest {

    @SerializedName("id")
    private int id;

    @SerializedName("title")
    private String title;

    @SerializedName("comment")
    private String comment;

    @SerializedName("tags")
    private List<String> tags;

    public BookmarkEditRequest() {
    }

    public BookmarkEditRequest(int id, String title, String comment, List<String> tags) {
        this.id = id;
        this.title = title;
        this.comment = comment;
        this.tags = tags;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
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
}
