package com.clipjot.android.data.api;

import com.clipjot.android.data.api.model.BookmarkRequest;
import com.clipjot.android.data.api.model.BookmarkResponse;
import com.clipjot.android.data.api.model.LogoutResponse;
import com.clipjot.android.data.api.model.TagsResponse;

import java.util.Map;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.POST;

/**
 * Retrofit interface for ClipJot API.
 */
public interface ClipJotApi {

    /**
     * Add a new bookmark.
     * Requires write scope.
     */
    @POST("api/v1/bookmarks/add")
    Call<BookmarkResponse> addBookmark(@Body BookmarkRequest request);

    /**
     * List all user tags.
     * Also used to verify session validity.
     * Requires read scope.
     */
    @POST("api/v1/tags/list")
    Call<TagsResponse> listTags(@Body Map<String, Object> body);

    /**
     * Logout and revoke the current session.
     * Only works with session tokens.
     */
    @POST("api/v1/logout")
    Call<LogoutResponse> logout(@Body Map<String, Object> body);
}
