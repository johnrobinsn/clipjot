package com.clipjot.android.data.api.model;

import com.google.gson.annotations.SerializedName;
import java.util.List;

/**
 * Response from /api/v1/bookmarks/search endpoint.
 */
public class BookmarkSearchResponse {

    @SerializedName("bookmarks")
    private List<BookmarkResponse> bookmarks;

    @SerializedName("total")
    private int total;

    @SerializedName("page")
    private int page;

    @SerializedName("per_page")
    private int perPage;

    @SerializedName("has_more")
    private boolean hasMore;

    public BookmarkSearchResponse() {
    }

    public List<BookmarkResponse> getBookmarks() {
        return bookmarks;
    }

    public void setBookmarks(List<BookmarkResponse> bookmarks) {
        this.bookmarks = bookmarks;
    }

    public int getTotal() {
        return total;
    }

    public void setTotal(int total) {
        this.total = total;
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

    public boolean isHasMore() {
        return hasMore;
    }

    public void setHasMore(boolean hasMore) {
        this.hasMore = hasMore;
    }
}
