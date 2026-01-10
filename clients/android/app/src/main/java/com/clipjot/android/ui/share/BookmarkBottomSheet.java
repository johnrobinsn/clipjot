package com.clipjot.android.ui.share;

import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.KeyEvent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import com.clipjot.android.ui.settings.SettingsActivity;

import com.clipjot.android.R;
import com.clipjot.android.data.api.ApiClient;
import com.clipjot.android.data.api.ClipJotApi;
import com.clipjot.android.data.api.model.ApiError;
import com.clipjot.android.data.api.model.BookmarkRequest;
import com.clipjot.android.data.api.model.BookmarkResponse;
import com.clipjot.android.data.api.model.Tag;
import com.clipjot.android.data.api.model.TagsResponse;
import com.clipjot.android.data.prefs.SettingsManager;
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
 * Bottom sheet dialog for creating a bookmark.
 */
public class BookmarkBottomSheet extends BottomSheetDialogFragment {

    private static final String ARG_URL = "url";
    private static final String ARG_TITLE = "title";

    private String url;
    private String initialTitle;

    private TextInputEditText urlInput;
    private TextInputEditText titleInput;
    private TextInputEditText commentInput;
    private EditText tagInput;
    private LinearLayout tagTokenContainer;
    private MaterialCardView tagSuggestionsCard;
    private ChipGroup tagSuggestionsChipGroup;
    private TextView noTagsMessage;
    private View expandedSection;
    private ImageButton expandButton;
    private ImageButton settingsButton;
    private MaterialButton saveButton;
    private LinearProgressIndicator progressIndicator;
    private TextView errorMessage;
    private TextView successMessage;

    private List<Tag> allTags = new ArrayList<>();
    private Set<String> selectedTags = new HashSet<>();
    private boolean isExpanded = true;
    private SettingsManager settingsManager;

    private OnDismissListener onDismissListener;

    public interface OnDismissListener {
        void onDismiss();
    }

    public static BookmarkBottomSheet newInstance(String url, String title) {
        BookmarkBottomSheet fragment = new BookmarkBottomSheet();
        Bundle args = new Bundle();
        args.putString(ARG_URL, url);
        args.putString(ARG_TITLE, title);
        fragment.setArguments(args);
        return fragment;
    }

    public void setOnDismissListener(OnDismissListener listener) {
        this.onDismissListener = listener;
    }

    @Override
    public void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (getArguments() != null) {
            url = getArguments().getString(ARG_URL);
            initialTitle = getArguments().getString(ARG_TITLE);
        }
        settingsManager = new SettingsManager(requireContext());
        isExpanded = settingsManager.isPanelExpanded();
    }

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.bottom_sheet_bookmark, container, false);
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
        expandedSection = view.findViewById(R.id.expandedSection);
        expandButton = view.findViewById(R.id.expandButton);
        settingsButton = view.findViewById(R.id.settingsButton);
        saveButton = view.findViewById(R.id.saveButton);
        progressIndicator = view.findViewById(R.id.progressIndicator);
        errorMessage = view.findViewById(R.id.errorMessage);
        successMessage = view.findViewById(R.id.successMessage);

        // Setup UI
        urlInput.setText(url);
        urlInput.setEnabled(false);

        if (initialTitle != null && !initialTitle.isEmpty()) {
            titleInput.setText(initialTitle);
        }

        // Apply saved expanded state
        applyExpandedState();

        setupExpandButton();
        setupSettingsButton();
        setupTagInput();
        setupSaveButton();

        // Load tags from server
        loadTags();
    }

    private void applyExpandedState() {
        expandedSection.setVisibility(isExpanded ? View.VISIBLE : View.GONE);
        // Arrow points down when expanded (click to collapse), up when collapsed (click to expand)
        expandButton.setImageResource(isExpanded ?
                R.drawable.ic_expand_more : R.drawable.ic_expand_less);
    }

    private void setupExpandButton() {
        expandButton.setOnClickListener(v -> toggleExpanded());
    }

    private void setupSettingsButton() {
        settingsButton.setOnClickListener(v -> {
            Intent intent = new Intent(requireContext(), SettingsActivity.class);
            intent.putExtra(SettingsActivity.EXTRA_SHOW_BACK_ARROW, true);
            startActivity(intent);
        });
    }

    private void toggleExpanded() {
        isExpanded = !isExpanded;
        settingsManager.setPanelExpanded(isExpanded);
        applyExpandedState();
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
                    // Remove the last tag
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
            // Skip already selected tags
            if (selectedTags.contains(tag.getName())) {
                continue;
            }
            // Apply filter
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

    private void setupSaveButton() {
        saveButton.setOnClickListener(v -> saveBookmark());
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
                    // Update suggestions if visible
                    if (tagSuggestionsCard.getVisibility() == View.VISIBLE) {
                        updateSuggestions(tagInput.getText() != null ? tagInput.getText().toString().trim() : "");
                    }
                } else if (response.code() == 401) {
                    // Token invalid - clear and dismiss
                    new TokenManager(requireContext()).clearToken();
                    showError(getString(R.string.error_session_expired));
                    dismissAllowingStateLoss();
                }
            }

            @Override
            public void onFailure(Call<TagsResponse> call, Throwable t) {
                if (!isAdded()) return;
                // Continue without tags - user can still type new ones
            }
        });
    }

    private void saveBookmark() {
        String title = titleInput.getText() != null ? titleInput.getText().toString().trim() : "";
        String comment = commentInput.getText() != null ? commentInput.getText().toString().trim() : "";

        // Show loading state
        setLoading(true);
        hideMessages();

        BookmarkRequest request = new BookmarkRequest(
                url,
                title.isEmpty() ? null : title,
                comment.isEmpty() ? null : comment,
                new ArrayList<>(selectedTags)
        );

        ClipJotApi api = ApiClient.getApi(requireContext());
        api.addBookmark(request).enqueue(new Callback<BookmarkResponse>() {
            @Override
            public void onResponse(Call<BookmarkResponse> call, Response<BookmarkResponse> response) {
                if (!isAdded()) return;

                setLoading(false);

                if (response.isSuccessful()) {
                    showSuccess(getString(R.string.bookmark_saved));
                    // Dismiss after a short delay
                    saveButton.postDelayed(() -> {
                        if (isAdded()) {
                            dismissAllowingStateLoss();
                        }
                    }, 1000);
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

    private void setLoading(boolean loading) {
        saveButton.setEnabled(!loading);
        progressIndicator.setVisibility(loading ? View.VISIBLE : View.GONE);
        titleInput.setEnabled(!loading);
        commentInput.setEnabled(!loading);
        tagInput.setEnabled(!loading);
    }

    private void showError(String message) {
        errorMessage.setText(message);
        errorMessage.setVisibility(View.VISIBLE);
        successMessage.setVisibility(View.GONE);
    }

    private void showSuccess(String message) {
        successMessage.setText(message);
        successMessage.setVisibility(View.VISIBLE);
        errorMessage.setVisibility(View.GONE);
    }

    private void hideMessages() {
        errorMessage.setVisibility(View.GONE);
        successMessage.setVisibility(View.GONE);
    }

    @Override
    public void onDismiss(@NonNull DialogInterface dialog) {
        super.onDismiss(dialog);
        if (onDismissListener != null) {
            onDismissListener.onDismiss();
        }
    }
}
