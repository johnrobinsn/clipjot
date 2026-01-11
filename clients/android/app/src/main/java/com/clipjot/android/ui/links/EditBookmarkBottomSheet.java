package com.clipjot.android.ui.links;

import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.KeyEvent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AlertDialog;

import com.clipjot.android.R;
import com.clipjot.android.data.api.ApiClient;
import com.clipjot.android.data.api.ClipJotApi;
import com.clipjot.android.data.api.model.ApiError;
import com.clipjot.android.data.api.model.BookmarkEditRequest;
import com.clipjot.android.data.api.model.BookmarkResponse;
import com.clipjot.android.data.api.model.DeleteResponse;
import com.clipjot.android.data.api.model.Tag;
import com.clipjot.android.data.api.model.TagsResponse;
import com.clipjot.android.data.prefs.TokenManager;
import com.google.android.material.bottomsheet.BottomSheetDialogFragment;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.card.MaterialCardView;
import com.google.android.material.chip.Chip;
import com.google.android.material.chip.ChipGroup;
import com.google.android.material.progressindicator.LinearProgressIndicator;
import com.google.android.material.textfield.TextInputEditText;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Bottom sheet for editing a bookmark.
 */
public class EditBookmarkBottomSheet extends BottomSheetDialogFragment {

    private static final String ARG_BOOKMARK_ID = "bookmark_id";
    private static final String ARG_URL = "url";
    private static final String ARG_TITLE = "title";
    private static final String ARG_COMMENT = "comment";
    private static final String ARG_TAGS = "tags";

    private int bookmarkId;
    private String url;
    private String initialTitle;
    private String initialComment;
    private ArrayList<String> initialTags;

    private TextInputEditText urlInput;
    private TextInputEditText titleInput;
    private TextInputEditText commentInput;
    private EditText tagInput;
    private LinearLayout tagTokenContainer;
    private MaterialCardView tagSuggestionsCard;
    private ChipGroup tagSuggestionsChipGroup;
    private TextView noTagsMessage;
    private MaterialButton saveButton;
    private MaterialButton deleteButton;
    private LinearProgressIndicator progressIndicator;
    private TextView errorMessage;

    private List<Tag> allTags = new ArrayList<>();
    private Set<String> selectedTags = new HashSet<>();

    private OnBookmarkUpdatedListener listener;

    public interface OnBookmarkUpdatedListener {
        void onBookmarkUpdated(BookmarkResponse updated);
        void onBookmarkDeleted(int bookmarkId);
    }

    public static EditBookmarkBottomSheet newInstance(BookmarkResponse bookmark) {
        EditBookmarkBottomSheet fragment = new EditBookmarkBottomSheet();
        Bundle args = new Bundle();
        args.putInt(ARG_BOOKMARK_ID, bookmark.getId());
        args.putString(ARG_URL, bookmark.getUrl());
        args.putString(ARG_TITLE, bookmark.getTitle());
        args.putString(ARG_COMMENT, bookmark.getComment());

        // Convert tags to list of names
        ArrayList<String> tagNames = new ArrayList<>();
        if (bookmark.getTags() != null) {
            for (Tag tag : bookmark.getTags()) {
                tagNames.add(tag.getName());
            }
        }
        args.putStringArrayList(ARG_TAGS, tagNames);

        fragment.setArguments(args);
        return fragment;
    }

    public void setOnBookmarkUpdatedListener(OnBookmarkUpdatedListener listener) {
        this.listener = listener;
    }

    @Override
    public void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (getArguments() != null) {
            bookmarkId = getArguments().getInt(ARG_BOOKMARK_ID);
            url = getArguments().getString(ARG_URL);
            initialTitle = getArguments().getString(ARG_TITLE);
            initialComment = getArguments().getString(ARG_COMMENT);
            initialTags = getArguments().getStringArrayList(ARG_TAGS);
            if (initialTags != null) {
                selectedTags.addAll(initialTags);
            }
        }
    }

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.bottom_sheet_edit_bookmark, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        // Bind views
        urlInput = view.findViewById(R.id.urlInput);
        titleInput = view.findViewById(R.id.titleInput);
        commentInput = view.findViewById(R.id.commentInput);
        tagInput = view.findViewById(R.id.tagInput);
        tagTokenContainer = view.findViewById(R.id.tagTokenContainer);
        tagSuggestionsCard = view.findViewById(R.id.tagSuggestionsCard);
        tagSuggestionsChipGroup = view.findViewById(R.id.tagSuggestionsChipGroup);
        noTagsMessage = view.findViewById(R.id.noTagsMessage);
        saveButton = view.findViewById(R.id.saveButton);
        deleteButton = view.findViewById(R.id.deleteButton);
        progressIndicator = view.findViewById(R.id.progressIndicator);
        errorMessage = view.findViewById(R.id.errorMessage);

        // Set initial values
        urlInput.setText(url);
        if (initialTitle != null) {
            titleInput.setText(initialTitle);
        }
        if (initialComment != null) {
            commentInput.setText(initialComment);
        }

        setupTagInput();
        updateInlineTagChips();

        saveButton.setOnClickListener(v -> saveBookmark());
        deleteButton.setOnClickListener(v -> confirmDelete());

        // Load all tags for suggestions
        loadTags();
    }

    private void setupTagInput() {
        // Show/hide suggestions based on focus
        tagInput.setOnFocusChangeListener((v, hasFocus) -> {
            if (hasFocus) {
                showSuggestions();
            } else {
                hideSuggestions();
            }
        });

        // Handle text changes for filtering
        tagInput.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {}

            @Override
            public void afterTextChanged(Editable s) {
                updateSuggestions(s.toString().trim());
            }
        });

        // Handle enter key to add tag
        tagInput.setOnEditorActionListener((v, actionId, event) -> {
            String text = tagInput.getText() != null ? tagInput.getText().toString().trim() : "";
            if (!text.isEmpty()) {
                addSelectedTag(text);
                tagInput.setText("");
                return true;
            }
            return false;
        });

        // Handle backspace to remove last tag when input is empty
        tagInput.setOnKeyListener((v, keyCode, event) -> {
            if (keyCode == KeyEvent.KEYCODE_DEL && event.getAction() == KeyEvent.ACTION_DOWN) {
                String text = tagInput.getText() != null ? tagInput.getText().toString() : "";
                if (text.isEmpty() && !selectedTags.isEmpty()) {
                    String lastTag = null;
                    for (String tag : selectedTags) {
                        lastTag = tag;
                    }
                    if (lastTag != null) {
                        removeSelectedTag(lastTag);
                        return true;
                    }
                }
            }
            return false;
        });
    }

    private void showSuggestions() {
        updateSuggestions(tagInput.getText() != null ? tagInput.getText().toString().trim() : "");
        tagSuggestionsCard.setVisibility(View.VISIBLE);
    }

    private void hideSuggestions() {
        tagSuggestionsCard.setVisibility(View.GONE);
    }

    private void updateSuggestions(String filter) {
        tagSuggestionsChipGroup.removeAllViews();

        List<Tag> filteredTags = new ArrayList<>();
        for (Tag tag : allTags) {
            if (selectedTags.contains(tag.getName())) {
                continue;
            }
            if (filter.isEmpty() || tag.getName().toLowerCase().contains(filter.toLowerCase())) {
                filteredTags.add(tag);
            }
        }

        if (filteredTags.isEmpty() && filter.isEmpty()) {
            noTagsMessage.setVisibility(View.VISIBLE);
            tagSuggestionsChipGroup.setVisibility(View.GONE);
        } else {
            noTagsMessage.setVisibility(View.GONE);
            tagSuggestionsChipGroup.setVisibility(View.VISIBLE);

            for (Tag tag : filteredTags) {
                Chip chip = new Chip(requireContext());
                chip.setText(tag.getName());
                chip.setOnClickListener(v -> {
                    addSelectedTag(tag.getName());
                    tagInput.setText("");
                });
                tagSuggestionsChipGroup.addView(chip);
            }
        }
    }

    private void addSelectedTag(String tagName) {
        if (selectedTags.contains(tagName)) {
            return;
        }
        selectedTags.add(tagName);
        updateInlineTagChips();
        updateSuggestions(tagInput.getText() != null ? tagInput.getText().toString().trim() : "");
    }

    private void removeSelectedTag(String tagName) {
        selectedTags.remove(tagName);
        updateInlineTagChips();
        updateSuggestions(tagInput.getText() != null ? tagInput.getText().toString().trim() : "");
    }

    private void updateInlineTagChips() {
        // Remove all views except the EditText (which is the last child)
        while (tagTokenContainer.getChildCount() > 1) {
            tagTokenContainer.removeViewAt(0);
        }

        // Add chips for each selected tag (before the EditText)
        int insertIndex = 0;
        for (String tagName : selectedTags) {
            Chip chip = new Chip(requireContext());
            chip.setText(tagName);
            chip.setCloseIconVisible(true);
            chip.setChipMinHeight(getResources().getDimensionPixelSize(R.dimen.chip_min_height_small));
            chip.setTextSize(12);
            chip.setOnCloseIconClickListener(v -> removeSelectedTag(tagName));

            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
            );
            params.setMarginEnd(4);
            chip.setLayoutParams(params);

            tagTokenContainer.addView(chip, insertIndex);
            insertIndex++;
        }
    }

    private void loadTags() {
        ClipJotApi api = ApiClient.getApi(requireContext());
        api.listTags(Collections.emptyMap()).enqueue(new Callback<TagsResponse>() {
            @Override
            public void onResponse(Call<TagsResponse> call, Response<TagsResponse> response) {
                if (!isAdded()) return;

                if (response.isSuccessful() && response.body() != null) {
                    allTags = response.body().getTags();
                    if (allTags == null) {
                        allTags = new ArrayList<>();
                    }
                    if (tagSuggestionsCard.getVisibility() == View.VISIBLE) {
                        updateSuggestions(tagInput.getText() != null ? tagInput.getText().toString().trim() : "");
                    }
                }
            }

            @Override
            public void onFailure(Call<TagsResponse> call, Throwable t) {
                // Continue without suggestions
            }
        });
    }

    private void saveBookmark() {
        String title = titleInput.getText() != null ? titleInput.getText().toString().trim() : "";
        String comment = commentInput.getText() != null ? commentInput.getText().toString().trim() : "";

        setLoading(true);
        hideError();

        BookmarkEditRequest request = new BookmarkEditRequest(
                bookmarkId,
                title.isEmpty() ? null : title,
                comment.isEmpty() ? null : comment,
                new ArrayList<>(selectedTags)
        );

        ClipJotApi api = ApiClient.getApi(requireContext());
        api.editBookmark(request).enqueue(new Callback<BookmarkResponse>() {
            @Override
            public void onResponse(Call<BookmarkResponse> call, Response<BookmarkResponse> response) {
                if (!isAdded()) return;

                setLoading(false);

                if (response.isSuccessful() && response.body() != null) {
                    if (listener != null) {
                        listener.onBookmarkUpdated(response.body());
                    }
                    dismissAllowingStateLoss();
                } else {
                    ApiError error = ApiClient.parseError(response);
                    if (error.isAuthError()) {
                        new TokenManager(requireContext()).clearToken();
                        showError(getString(R.string.error_session_expired));
                    } else {
                        showError(error.getError());
                    }
                }
            }

            @Override
            public void onFailure(Call<BookmarkResponse> call, Throwable t) {
                if (!isAdded()) return;

                setLoading(false);
                showError(getString(R.string.error_network));
            }
        });
    }

    private void confirmDelete() {
        new AlertDialog.Builder(requireContext())
                .setTitle(R.string.delete_link_title)
                .setMessage(R.string.delete_link_confirm)
                .setPositiveButton(R.string.delete, (dialog, which) -> deleteBookmark())
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    private void deleteBookmark() {
        setLoading(true);
        hideError();

        ClipJotApi api = ApiClient.getApi(requireContext());
        api.deleteBookmark(Collections.singletonMap("id", bookmarkId)).enqueue(new Callback<DeleteResponse>() {
            @Override
            public void onResponse(Call<DeleteResponse> call, Response<DeleteResponse> response) {
                if (!isAdded()) return;

                setLoading(false);

                if (response.isSuccessful()) {
                    if (listener != null) {
                        listener.onBookmarkDeleted(bookmarkId);
                    }
                    dismissAllowingStateLoss();
                } else {
                    ApiError error = ApiClient.parseError(response);
                    showError(error.getError());
                }
            }

            @Override
            public void onFailure(Call<DeleteResponse> call, Throwable t) {
                if (!isAdded()) return;

                setLoading(false);
                showError(getString(R.string.error_network));
            }
        });
    }

    private void setLoading(boolean loading) {
        saveButton.setEnabled(!loading);
        deleteButton.setEnabled(!loading);
        progressIndicator.setVisibility(loading ? View.VISIBLE : View.GONE);
        titleInput.setEnabled(!loading);
        commentInput.setEnabled(!loading);
        tagInput.setEnabled(!loading);
    }

    private void showError(String message) {
        errorMessage.setText(message);
        errorMessage.setVisibility(View.VISIBLE);
    }

    private void hideError() {
        errorMessage.setVisibility(View.GONE);
    }
}
