package com.clipjot.android.ui.auth;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.browser.customtabs.CustomTabsIntent;

import com.clipjot.android.R;
import com.clipjot.android.data.prefs.SettingsManager;
import com.clipjot.android.data.prefs.TokenManager;
import com.clipjot.android.ui.settings.SettingsActivity;
import com.google.android.material.button.MaterialButton;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;

/**
 * Login activity with OAuth provider buttons.
 */
public class LoginActivity extends AppCompatActivity {

    private static final String CALLBACK_URI = "clipjot://oauth/callback";

    private SettingsManager settingsManager;
    private TokenManager tokenManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        settingsManager = new SettingsManager(this);
        tokenManager = new TokenManager(this);

        // Check if already logged in
        if (tokenManager.hasToken()) {
            finish();
            return;
        }

        setupButtons();
    }

    private void setupButtons() {
        MaterialButton googleButton = findViewById(R.id.googleLoginButton);
        MaterialButton githubButton = findViewById(R.id.githubLoginButton);
        MaterialButton settingsButton = findViewById(R.id.settingsButton);

        googleButton.setOnClickListener(v -> startOAuth("google"));
        githubButton.setOnClickListener(v -> startOAuth("github"));
        settingsButton.setOnClickListener(v -> openSettings());
    }

    private void startOAuth(String provider) {
        try {
            String backendUrl = settingsManager.getBackendUrl();
            String redirectUri = URLEncoder.encode(CALLBACK_URI, "UTF-8");
            String authUrl = backendUrl + "/auth/" + provider + "?redirect_uri=" + redirectUri;

            // Use Chrome Custom Tabs for better UX
            CustomTabsIntent customTabsIntent = new CustomTabsIntent.Builder()
                    .setShowTitle(true)
                    .build();
            customTabsIntent.launchUrl(this, Uri.parse(authUrl));

        } catch (UnsupportedEncodingException e) {
            Toast.makeText(this, R.string.error_oauth_failed, Toast.LENGTH_SHORT).show();
        }
    }

    private void openSettings() {
        Intent intent = new Intent(this, SettingsActivity.class);
        startActivity(intent);
    }

    @Override
    protected void onResume() {
        super.onResume();
        // Check if we got logged in while away
        if (tokenManager.hasToken()) {
            finish();
        }
    }
}
