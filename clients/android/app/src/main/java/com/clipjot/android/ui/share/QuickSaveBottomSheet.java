package com.clipjot.android.ui.share;

import android.content.DialogInterface;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.content.ContextCompat;

import com.clipjot.android.R;
import com.clipjot.android.data.api.ApiClient;
import com.clipjot.android.data.api.ClipJotApi;
import com.clipjot.android.data.api.model.ApiError;
import com.clipjot.android.data.api.model.BookmarkRequest;
import com.clipjot.android.data.api.model.BookmarkResponse;
import com.clipjot.android.data.prefs.TokenManager;
import com.google.android.material.bottomsheet.BottomSheetDialogFragment;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.progressindicator.CircularProgressIndicator;

import java.util.ArrayList;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Bottom sheet for quick save mode - saves immediately without editing.
 * Shows save status and provides an Edit button on failure.
 */
public class QuickSaveBottomSheet extends BottomSheetDialogFragment {

    private static final String ARG_URL = "url";
    private static final String ARG_TITLE = "title";
    private static final int AUTO_DISMISS_DELAY_MS = 1500;

    private String url;
    private String title;

    private TextView urlText;
    private CircularProgressIndicator progressIndicator;
    private ImageView statusIcon;
    private TextView statusText;
    private MaterialButton editButton;

    private OnQuickSaveListener listener;

    public interface OnQuickSaveListener {
        void onDismiss();
        void onEditRequested(String url, String title);
    }

    public static QuickSaveBottomSheet newInstance(String url, String title) {
        QuickSaveBottomSheet fragment = new QuickSaveBottomSheet();
        Bundle args = new Bundle();
        args.putString(ARG_URL, url);
        args.putString(ARG_TITLE, title);
        fragment.setArguments(args);
        return fragment;
    }

    public void setOnQuickSaveListener(OnQuickSaveListener listener) {
        this.listener = listener;
    }

    @Override
    public void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (getArguments() != null) {
            url = getArguments().getString(ARG_URL);
            title = getArguments().getString(ARG_TITLE);
        }
    }

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.bottom_sheet_quick_save, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        // Bind views
        urlText = view.findViewById(R.id.urlText);
        progressIndicator = view.findViewById(R.id.progressIndicator);
        statusIcon = view.findViewById(R.id.statusIcon);
        statusText = view.findViewById(R.id.statusText);
        editButton = view.findViewById(R.id.editButton);

        // Setup UI - show title if available, otherwise URL
        String displayText = (title != null && !title.isEmpty()) ? title : url;
        urlText.setText(displayText);

        editButton.setOnClickListener(v -> {
            if (listener != null) {
                listener.onEditRequested(url, title);
            }
            dismissAllowingStateLoss();
        });

        // Start saving immediately
        saveBookmark();
    }

    private void saveBookmark() {
        BookmarkRequest request = new BookmarkRequest(
                url,
                title != null && !title.isEmpty() ? title : null,
                null,  // no comment in quick save
                new ArrayList<>()  // no tags in quick save
        );

        ClipJotApi api = ApiClient.getApi(requireContext());
        api.addBookmark(request).enqueue(new Callback<BookmarkResponse>() {
            @Override
            public void onResponse(Call<BookmarkResponse> call, Response<BookmarkResponse> response) {
                if (!isAdded()) return;

                if (response.isSuccessful()) {
                    showSuccess();
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
                showError(getString(R.string.error_network));
            }
        });
    }

    private void showSuccess() {
        progressIndicator.setVisibility(View.GONE);
        statusIcon.setVisibility(View.VISIBLE);
        statusIcon.setImageResource(R.drawable.ic_check);
        statusIcon.setColorFilter(ContextCompat.getColor(requireContext(), R.color.success));
        statusText.setText(R.string.quick_save_success);
        statusText.setTextColor(ContextCompat.getColor(requireContext(), R.color.success));
        editButton.setVisibility(View.GONE);

        // Auto-dismiss after delay
        statusText.postDelayed(() -> {
            if (isAdded()) {
                dismissAllowingStateLoss();
            }
        }, AUTO_DISMISS_DELAY_MS);
    }

    private void showError(String message) {
        progressIndicator.setVisibility(View.GONE);
        statusIcon.setVisibility(View.VISIBLE);
        statusIcon.setImageResource(R.drawable.ic_error);
        statusIcon.setColorFilter(ContextCompat.getColor(requireContext(), R.color.error));
        statusText.setText(message != null ? message : getString(R.string.quick_save_error));
        statusText.setTextColor(ContextCompat.getColor(requireContext(), R.color.error));
        editButton.setVisibility(View.VISIBLE);
    }

    @Override
    public void onDismiss(@NonNull DialogInterface dialog) {
        super.onDismiss(dialog);
        if (listener != null) {
            listener.onDismiss();
        }
    }
}
