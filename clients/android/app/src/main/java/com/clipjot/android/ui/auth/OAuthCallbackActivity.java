package com.clipjot.android.ui.auth;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.clipjot.android.R;
import com.clipjot.android.data.prefs.SettingsManager;
import com.clipjot.android.data.prefs.TokenManager;
import com.clipjot.android.ui.share.ShareActivity;

/**
 * Handles OAuth callback via deep link.
 * Receives: clipjot://oauth/callback?token={session_token}
 */
public class OAuthCallbackActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        TokenManager tokenManager = new TokenManager(this);
        SettingsManager settingsManager = new SettingsManager(this);

        Uri uri = getIntent().getData();
        if (uri != null) {
            String token = uri.getQueryParameter("token");
            String error = uri.getQueryParameter("error");

            if (token != null && !token.isEmpty()) {
                // Save the token
                tokenManager.saveToken(token);

                // Check for pending bookmark
                if (settingsManager.hasPendingBookmark()) {
                    // Return to ShareActivity with pending bookmark
                    Intent intent = new Intent(this, ShareActivity.class);
                    intent.setAction(Intent.ACTION_SEND);
                    intent.setType("text/plain");
                    intent.putExtra(Intent.EXTRA_TEXT, settingsManager.getPendingBookmarkUrl());
                    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
                    startActivity(intent);
                } else {
                    // Just show success
                    Toast.makeText(this, R.string.login_success, Toast.LENGTH_SHORT).show();
                }

                finish();

            } else if (error != null) {
                // Show error
                Toast.makeText(this, getString(R.string.login_error, error), Toast.LENGTH_LONG).show();
                finish();

            } else {
                // No token or error - invalid callback
                Toast.makeText(this, R.string.error_invalid_callback, Toast.LENGTH_SHORT).show();
                finish();
            }
        } else {
            // No URI data
            finish();
        }
    }
}
