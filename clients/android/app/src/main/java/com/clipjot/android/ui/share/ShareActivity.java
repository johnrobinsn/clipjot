package com.clipjot.android.ui.share;

import android.content.Intent;
import android.os.Bundle;

import androidx.appcompat.app.AppCompatActivity;

import com.clipjot.android.data.prefs.SettingsManager;
import com.clipjot.android.data.prefs.TokenManager;
import com.clipjot.android.ui.auth.LoginActivity;
import com.clipjot.android.util.UrlValidator;

/**
 * Entry point for share intents from other apps.
 * Shows the bookmark bottom sheet or redirects to login.
 */
public class ShareActivity extends AppCompatActivity {

    private TokenManager tokenManager;
    private SettingsManager settingsManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        tokenManager = new TokenManager(this);
        settingsManager = new SettingsManager(this);

        handleIntent(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleIntent(intent);
    }

    private void handleIntent(Intent intent) {
        if (Intent.ACTION_SEND.equals(intent.getAction()) &&
                "text/plain".equals(intent.getType())) {

            String sharedText = intent.getStringExtra(Intent.EXTRA_TEXT);
            String sharedSubject = intent.getStringExtra(Intent.EXTRA_SUBJECT);

            if (sharedText != null) {
                String url = UrlValidator.extractUrl(sharedText);

                if (url != null) {
                    // Determine title - use subject if provided, or extract from text
                    String title = sharedSubject;
                    if (title == null || title.isEmpty()) {
                        title = UrlValidator.extractTitle(sharedText, url);
                    }

                    if (tokenManager.hasToken()) {
                        // Show the bookmark bottom sheet
                        showBookmarkSheet(url, title);
                    } else {
                        // Need to login first - store pending bookmark
                        settingsManager.setPendingBookmark(url, title);
                        startActivity(new Intent(this, LoginActivity.class));
                        finish();
                    }
                } else {
                    // No valid URL found
                    finish();
                }
            } else {
                finish();
            }
        } else {
            finish();
        }
    }

    private void showBookmarkSheet(String url, String title) {
        // Clear any pending bookmark since we're handling it now
        settingsManager.clearPendingBookmark();

        if (settingsManager.isQuickSaveEnabled()) {
            // Quick save mode - save immediately without editing
            QuickSaveBottomSheet quickSave = QuickSaveBottomSheet.newInstance(url, title);
            quickSave.setOnQuickSaveListener(new QuickSaveBottomSheet.OnQuickSaveListener() {
                @Override
                public void onDismiss() {
                    finish();
                }

                @Override
                public void onEditRequested(String editUrl, String editTitle) {
                    // User wants to edit after failed save - show full form
                    BookmarkBottomSheet editSheet = BookmarkBottomSheet.newInstance(editUrl, editTitle);
                    editSheet.setOnDismissListener(() -> finish());
                    editSheet.show(getSupportFragmentManager(), "bookmark_sheet");
                }
            });
            quickSave.show(getSupportFragmentManager(), "quick_save_sheet");
        } else {
            // Normal mode - show edit form
            BookmarkBottomSheet bottomSheet = BookmarkBottomSheet.newInstance(url, title);
            bottomSheet.setOnDismissListener(() -> finish());
            bottomSheet.show(getSupportFragmentManager(), "bookmark_sheet");
        }
    }
}
