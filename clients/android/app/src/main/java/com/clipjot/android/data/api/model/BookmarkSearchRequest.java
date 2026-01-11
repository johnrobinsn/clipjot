package com.clipjot.android.data.api.model;

import com.google.gson.annotations.SerializedName;
import java.util.List;

/**
 * Request body for /api/v1/bookmarks/search endpoint.
 */
public class BookmarkSearchRequest {

    @SerializedName("query")
    private String query;

    @SerializedName("tags")
    private List<String> tags;

    @SerializedName("page")
    private int page;

    @SerializedName("per_page")
    private int perPage;

    public BookmarkSearchRequest() {
        this.page = 1;
        this.perPage = 50;
    }

    public BookmarkSearchRequest(String query, int page, int perPage) {
        this.query = query;
        this.page = page;
        this.perPage = perPage;
    }

    public String getQuery() {
        return query;
    }

    public void setQuery(String query) {
        this.query = query;
    }

    public List<String> getTags() {
        return tags;
    }

    public void setTags(List<String> tags) {
        this.tags = tags;
    }

    public int getPage() {
        return page;
    }

    public void setPage(int page) {
        this.page = page;
    }

    public int getPerPage() {
        return perPage;
    }

    public void setPerPage(int perPage) {
        this.perPage = perPage;
    }
}
