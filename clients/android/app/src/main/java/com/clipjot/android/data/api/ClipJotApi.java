package com.clipjot.android.data.api;

import com.clipjot.android.data.api.model.BookmarkEditRequest;
import com.clipjot.android.data.api.model.BookmarkRequest;
import com.clipjot.android.data.api.model.BookmarkResponse;
import com.clipjot.android.data.api.model.BookmarkSearchRequest;
import com.clipjot.android.data.api.model.BookmarkSearchResponse;
import com.clipjot.android.data.api.model.DeleteResponse;
import com.clipjot.android.data.api.model.InviteCodeAuthResponse;
import com.clipjot.android.data.api.model.InviteCodeRequest;
import com.clipjot.android.data.api.model.LatestBookmarkResponse;
import com.clipjot.android.data.api.model.LogoutResponse;
import com.clipjot.android.data.api.model.TagsResponse;
import com.clipjot.android.data.api.model.UserProfileResponse;

import java.util.Map;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
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
     * Authenticate with an invite code.
     * No authentication header required.
     */
    @POST("api/v1/auth/invite")
    Call<InviteCodeAuthResponse> authenticateWithInviteCode(@Body InviteCodeRequest request);

    /**
     * Logout and revoke the current session.
     * Only works with session tokens.
     */
    @POST("api/v1/logout")
    Call<LogoutResponse> logout(@Body Map<String, Object> body);

    /**
     * Search bookmarks with pagination.
     * Requires read scope.
     */
    @POST("api/v1/bookmarks/search")
    Call<BookmarkSearchResponse> searchBookmarks(@Body BookmarkSearchRequest request);

    /**
     * Edit an existing bookmark.
     * Requires write scope.
     */
    @POST("api/v1/bookmarks/edit")
    Call<BookmarkResponse> editBookmark(@Body BookmarkEditRequest request);

    /**
     * Delete a bookmark.
     * Requires write scope.
     */
    @POST("api/v1/bookmarks/delete")
    Call<DeleteResponse> deleteBookmark(@Body Map<String, Integer> body);

    /**
     * Get the latest bookmark ID for the current user.
     * Used to detect when new bookmarks have been added.
     */
    @GET("api/internal/latest-bookmark")
    Call<LatestBookmarkResponse> getLatestBookmarkId();

    /**
     * Get the current user's profile information.
     * Requires read scope.
     */
    @POST("api/v1/user/profile")
    Call<UserProfileResponse> getUserProfile(@Body Map<String, Object> body);
}
