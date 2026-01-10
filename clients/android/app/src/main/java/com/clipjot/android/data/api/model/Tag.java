package com.clipjot.android.data.api.model;

import com.google.gson.annotations.SerializedName;

/**
 * Tag model matching backend API response.
 */
public class Tag {

    @SerializedName("id")
    private int id;

    @SerializedName("name")
    private String name;

    @SerializedName("bookmark_count")
    private int bookmarkCount;

    public Tag() {
    }

    public Tag(int id, String name, int bookmarkCount) {
        this.id = id;
        this.name = name;
        this.bookmarkCount = bookmarkCount;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getBookmarkCount() {
        return bookmarkCount;
    }

    public void setBookmarkCount(int bookmarkCount) {
        this.bookmarkCount = bookmarkCount;
    }

    @Override
    public String toString() {
        return name;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Tag tag = (Tag) o;
        return id == tag.id;
    }

    @Override
    public int hashCode() {
        return id;
    }
}
