package com.clipjot.android.ui.links;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

import com.clipjot.android.R;
import com.clipjot.android.ui.auth.LoginActivity;
import com.clipjot.android.ui.settings.SettingsActivity;
import com.clipjot.android.data.api.ApiClient;
import com.clipjot.android.data.api.ClipJotApi;
import com.clipjot.android.data.api.model.BookmarkResponse;
import com.clipjot.android.data.api.model.BookmarkSearchRequest;
import com.clipjot.android.data.api.model.BookmarkSearchResponse;
import com.clipjot.android.data.api.model.DeleteResponse;
import com.clipjot.android.data.prefs.TokenManager;
import com.google.android.material.appbar.MaterialToolbar;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.card.MaterialCardView;
import com.google.android.material.progressindicator.CircularProgressIndicator;
import com.google.android.material.textfield.TextInputEditText;
import com.google.android.material.textfield.TextInputLayout;

import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Activity for displaying and managing the user's bookmarks.
 */
public class MyLinksActivity extends AppCompatActivity implements BookmarkAdapter.OnBookmarkClickListener {

    private static final int PAGE_SIZE = 30;
    private static final int SEARCH_DEBOUNCE_MS = 300;
    private static final int LOAD_MORE_THRESHOLD = 5;

    private RecyclerView recyclerView;
    private SwipeRefreshLayout swipeRefresh;
    private LinearLayout emptyState;
    private TextView emptyTitle;
    private TextView emptySubtitle;
    private LinearLayout errorState;
    private TextView errorMessage;
    private MaterialButton retryButton;
    private CircularProgressIndicator loadingIndicator;
    private MaterialCardView selectionBar;
    private TextView selectionCount;
    private TextInputEditText searchInput;
    private TextInputLayout searchLayout;

    private BookmarkAdapter adapter;
    private TokenManager tokenManager;

    private String currentQuery = "";
    private int currentPage = 1;
    private boolean hasMore = true;
    private boolean isLoading = false;

    private final Handler searchHandler = new Handler(Looper.getMainLooper());
    private Runnable searchRunnable;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        tokenManager = new TokenManager(this);

        // Check if logged in, redirect to login if not
        if (!tokenManager.hasToken()) {
            startActivity(new Intent(this, LoginActivity.class));
            finish();
            return;
        }

        setContentView(R.layout.activity_my_links);

        bindViews();
        setupToolbar();
        setupRecyclerView();
        setupSearch();
        setupSwipeRefresh();
        setupSelectionBar();

        loadBookmarks(true);
    }

    @Override
    protected void onResume() {
        super.onResume();
        // Check if still logged in (might have logged out from settings)
        if (!tokenManager.hasToken()) {
            startActivity(new Intent(this, LoginActivity.class));
            finish();
            return;
        }
        // Silently refresh if we already have data
        if (adapter.getItemCount() > 0) {
            silentRefresh();
        }
    }

    /**
     * Refreshes bookmarks in the background without showing loading indicators.
     * Uses DiffUtil to smoothly update only changed items.
     */
    private void silentRefresh() {
        BookmarkSearchRequest request = new BookmarkSearchRequest(currentQuery, 1, PAGE_SIZE);

        ClipJotApi api = ApiClient.getApi(this);
        api.searchBookmarks(request).enqueue(new Callback<BookmarkSearchResponse>() {
            @Override
            public void onResponse(Call<BookmarkSearchResponse> call, Response<BookmarkSearchResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    BookmarkSearchResponse body = response.body();
                    List<BookmarkResponse> bookmarks = body.getBookmarks();
                    hasMore = body.isHasMore();
                    currentPage = 1;

                    if (bookmarks != null) {
                        adapter.updateBookmarks(bookmarks);
                    }
                    updateEmptyState();
                }
                // Silently ignore errors - user can pull to refresh if needed
            }

            @Override
            public void onFailure(Call<BookmarkSearchResponse> call, Throwable t) {
                // Silently ignore - user can pull to refresh if needed
            }
        });
    }

    private void bindViews() {
        recyclerView = findViewById(R.id.recyclerView);
        swipeRefresh = findViewById(R.id.swipeRefresh);
        emptyState = findViewById(R.id.emptyState);
        emptyTitle = findViewById(R.id.emptyTitle);
        emptySubtitle = findViewById(R.id.emptySubtitle);
        errorState = findViewById(R.id.errorState);
        errorMessage = findViewById(R.id.errorMessage);
        retryButton = findViewById(R.id.retryButton);
        loadingIndicator = findViewById(R.id.loadingIndicator);
        selectionBar = findViewById(R.id.selectionBar);
        selectionCount = findViewById(R.id.selectionCount);
        searchInput = findViewById(R.id.searchInput);
        searchLayout = findViewById(R.id.searchLayout);
    }

    private void setupToolbar() {
        MaterialToolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        // No back button on main screen
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(false);
        }
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.menu_my_links, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(@NonNull MenuItem item) {
        if (item.getItemId() == R.id.action_settings) {
            startActivity(new Intent(this, SettingsActivity.class));
            return true;
        }
        return super.onOptionsItemSelected(item);
    }

    private void setupRecyclerView() {
        adapter = new BookmarkAdapter();
        adapter.setOnBookmarkClickListener(this);

        LinearLayoutManager layoutManager = new LinearLayoutManager(this);
        recyclerView.setLayoutManager(layoutManager);
        recyclerView.setAdapter(adapter);

        // Infinite scroll
        recyclerView.addOnScrollListener(new RecyclerView.OnScrollListener() {
            @Override
            public void onScrolled(@NonNull RecyclerView recyclerView, int dx, int dy) {
                if (dy > 0 && !isLoading && hasMore) {
                    int visibleItemCount = layoutManager.getChildCount();
                    int totalItemCount = layoutManager.getItemCount();
                    int firstVisibleItem = layoutManager.findFirstVisibleItemPosition();

                    if ((totalItemCount - visibleItemCount) <= (firstVisibleItem + LOAD_MORE_THRESHOLD)) {
                        loadMoreBookmarks();
                    }
                }
            }
        });
    }

    private void setupSearch() {
        searchInput.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                // Show/hide clear button based on text content
                updateClearButtonVisibility(s.length() > 0);
            }

            @Override
            public void afterTextChanged(Editable s) {
                // Debounce search
                if (searchRunnable != null) {
                    searchHandler.removeCallbacks(searchRunnable);
                }
                searchRunnable = () -> {
                    String query = s.toString().trim();
                    if (!query.equals(currentQuery)) {
                        currentQuery = query;
                        loadBookmarks(true);
                    }
                };
                searchHandler.postDelayed(searchRunnable, SEARCH_DEBOUNCE_MS);
            }
        });

        // Set up clear button click listener
        searchLayout.setEndIconOnClickListener(v -> {
            searchInput.setText("");
        });

        // Initially hide the clear button
        updateClearButtonVisibility(false);
    }

    private void updateClearButtonVisibility(boolean hasText) {
        searchLayout.setEndIconVisible(hasText);
    }

    private void setupSwipeRefresh() {
        swipeRefresh.setOnRefreshListener(() -> loadBookmarks(true));
    }

    private void setupSelectionBar() {
        MaterialButton cancelButton = findViewById(R.id.cancelSelectionButton);
        MaterialButton selectAllButton = findViewById(R.id.selectAllButton);
        MaterialButton deleteButton = findViewById(R.id.deleteSelectedButton);

        cancelButton.setOnClickListener(v -> exitSelectionMode());
        selectAllButton.setOnClickListener(v -> selectAll());
        deleteButton.setOnClickListener(v -> confirmDeleteSelected());
    }

    private void selectAll() {
        adapter.selectAll();
    }

    private void loadBookmarks(boolean refresh) {
        if (isLoading) return;

        if (refresh) {
            currentPage = 1;
            hasMore = true;
        }

        isLoading = true;

        // Show loading state
        if (refresh && adapter.getItemCount() == 0) {
            showLoadingState();
        }

        BookmarkSearchRequest request = new BookmarkSearchRequest(currentQuery, currentPage, PAGE_SIZE);

        ClipJotApi api = ApiClient.getApi(this);
        api.searchBookmarks(request).enqueue(new Callback<BookmarkSearchResponse>() {
            @Override
            public void onResponse(Call<BookmarkSearchResponse> call, Response<BookmarkSearchResponse> response) {
                isLoading = false;
                swipeRefresh.setRefreshing(false);

                if (response.isSuccessful() && response.body() != null) {
                    BookmarkSearchResponse body = response.body();
                    List<BookmarkResponse> bookmarks = body.getBookmarks();
                    hasMore = body.isHasMore();

                    if (refresh) {
                        adapter.setBookmarks(bookmarks != null ? bookmarks : Collections.emptyList());
                    } else {
                        adapter.addBookmarks(bookmarks != null ? bookmarks : Collections.emptyList());
                    }

                    updateEmptyState();
                } else if (response.code() == 401) {
                    handleSessionExpired();
                } else {
                    showErrorState(getString(R.string.error_loading_links));
                }
            }

            @Override
            public void onFailure(Call<BookmarkSearchResponse> call, Throwable t) {
                isLoading = false;
                swipeRefresh.setRefreshing(false);
                showErrorState(getString(R.string.error_network));
            }
        });
    }

    private void loadMoreBookmarks() {
        currentPage++;
        loadBookmarks(false);
    }

    private void showLoadingState() {
        loadingIndicator.setVisibility(View.VISIBLE);
        emptyState.setVisibility(View.GONE);
        errorState.setVisibility(View.GONE);
    }

    private void updateEmptyState() {
        loadingIndicator.setVisibility(View.GONE);
        errorState.setVisibility(View.GONE);

        if (adapter.getItemCount() == 0) {
            emptyState.setVisibility(View.VISIBLE);
            if (currentQuery.isEmpty()) {
                emptyTitle.setText(R.string.no_links_yet);
                emptySubtitle.setText(R.string.no_links_subtitle);
            } else {
                emptyTitle.setText(R.string.no_search_results);
                emptySubtitle.setText(R.string.no_search_results_subtitle);
            }
        } else {
            emptyState.setVisibility(View.GONE);
        }
    }

    private void showErrorState(String message) {
        loadingIndicator.setVisibility(View.GONE);
        emptyState.setVisibility(View.GONE);

        if (adapter.getItemCount() == 0) {
            errorState.setVisibility(View.VISIBLE);
            errorMessage.setText(message);
            retryButton.setOnClickListener(v -> loadBookmarks(true));
        } else {
            // Show toast if we have some data
            Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
        }
    }

    private void handleSessionExpired() {
        tokenManager.clearToken();
        Toast.makeText(this, R.string.error_session_expired, Toast.LENGTH_SHORT).show();
        finish();
    }

    // BookmarkAdapter.OnBookmarkClickListener implementation

    @Override
    public void onBookmarkClick(BookmarkResponse bookmark) {
        // Open URL in browser
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(bookmark.getUrl()));
            startActivity(intent);
        } catch (Exception e) {
            Toast.makeText(this, R.string.error_invalid_url, Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    public void onEditClick(BookmarkResponse bookmark) {
        EditBookmarkBottomSheet sheet = EditBookmarkBottomSheet.newInstance(bookmark);
        sheet.setOnBookmarkUpdatedListener(new EditBookmarkBottomSheet.OnBookmarkUpdatedListener() {
            @Override
            public void onBookmarkUpdated(BookmarkResponse updated) {
                adapter.updateBookmark(updated);
            }

            @Override
            public void onBookmarkDeleted(int bookmarkId) {
                adapter.removeBookmark(bookmarkId);
                updateEmptyState();
            }
        });
        sheet.show(getSupportFragmentManager(), "edit_bookmark");
    }

    @Override
    public void onSelectionChanged(Set<Integer> selectedIds) {
        if (selectedIds.isEmpty()) {
            exitSelectionMode();
        } else {
            selectionCount.setText(getString(R.string.selected_count, selectedIds.size()));
        }
    }

    @Override
    public void onLongClick(BookmarkResponse bookmark) {
        enterSelectionMode();
        // Toggle selection for the long-pressed item
        adapter.notifyDataSetChanged();
    }

    private void enterSelectionMode() {
        adapter.setSelectionMode(true);
        selectionBar.setVisibility(View.VISIBLE);
        selectionCount.setText(getString(R.string.selected_count, 0));
    }

    private void exitSelectionMode() {
        adapter.setSelectionMode(false);
        adapter.clearSelection();
        selectionBar.setVisibility(View.GONE);
    }

    private void confirmDeleteSelected() {
        Set<Integer> selected = adapter.getSelectedIds();
        if (selected.isEmpty()) return;

        new AlertDialog.Builder(this)
                .setTitle(R.string.delete_selected_title)
                .setMessage(getString(R.string.delete_selected_confirm, selected.size()))
                .setPositiveButton(R.string.delete, (dialog, which) -> deleteSelected(selected))
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    private void deleteSelected(Set<Integer> ids) {
        // Track progress
        final int[] remaining = {ids.size()};
        final int[] deleted = {0};
        Set<Integer> toRemove = new HashSet<>();

        ClipJotApi api = ApiClient.getApi(this);

        for (int id : ids) {
            api.deleteBookmark(Collections.singletonMap("id", id)).enqueue(new Callback<DeleteResponse>() {
                @Override
                public void onResponse(Call<DeleteResponse> call, Response<DeleteResponse> response) {
                    remaining[0]--;
                    if (response.isSuccessful()) {
                        deleted[0]++;
                        toRemove.add(id);
                    }
                    if (remaining[0] == 0) {
                        onDeleteComplete(toRemove, deleted[0]);
                    }
                }

                @Override
                public void onFailure(Call<DeleteResponse> call, Throwable t) {
                    remaining[0]--;
                    if (remaining[0] == 0) {
                        onDeleteComplete(toRemove, deleted[0]);
                    }
                }
            });
        }
    }

    private void onDeleteComplete(Set<Integer> deletedIds, int count) {
        adapter.removeBookmarks(deletedIds);
        exitSelectionMode();
        updateEmptyState();

        if (count > 0) {
            Toast.makeText(this, getString(R.string.links_deleted, count), Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    public void onBackPressed() {
        if (adapter.isSelectionMode()) {
            exitSelectionMode();
        } else {
            super.onBackPressed();
        }
    }
}
