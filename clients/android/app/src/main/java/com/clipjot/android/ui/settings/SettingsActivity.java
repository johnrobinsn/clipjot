package com.clipjot.android.ui.settings;

import android.net.Uri;
import android.os.Bundle;
import android.view.MenuItem;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.browser.customtabs.CustomTabsIntent;

import com.clipjot.android.R;
import com.clipjot.android.data.api.ApiClient;
import com.clipjot.android.data.api.ClipJotApi;
import com.clipjot.android.data.api.model.TagsResponse;
import com.clipjot.android.data.prefs.SettingsManager;
import com.clipjot.android.data.prefs.TokenManager;
import com.clipjot.android.util.UrlValidator;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.progressindicator.LinearProgressIndicator;
import com.google.android.material.textfield.TextInputEditText;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.util.Collections;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Settings activity for backend URL configuration and account management.
 */
public class SettingsActivity extends AppCompatActivity {

    public static final String EXTRA_SHOW_BACK_ARROW = "show_back_arrow";
    private static final String CALLBACK_URI = "clipjot://oauth/callback";

    private TextInputEditText backendUrlInput;
    private MaterialButton testConnectionButton;
    private MaterialButton saveButton;
    private MaterialButton resetDefaultsButton;
    private MaterialButton logoutButton;
    private MaterialButton googleLoginButton;
    private MaterialButton githubLoginButton;
    private LinearProgressIndicator progressIndicator;
    private TextView connectionStatus;
    private TextView httpWarning;
    private TextView websiteLink;
    private View accountSection;
    private View loginSection;
    private TextView accountEmail;

    private SettingsManager settingsManager;
    private TokenManager tokenManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);

        // Configure action bar - hide when launched from drawer, show when from panel
        boolean showBackArrow = getIntent().getBooleanExtra(EXTRA_SHOW_BACK_ARROW, false);
        if (getSupportActionBar() != null) {
            if (showBackArrow) {
                getSupportActionBar().setDisplayHomeAsUpEnabled(true);
                getSupportActionBar().setTitle(R.string.settings_title);
            } else {
                getSupportActionBar().hide();
            }
        }

        settingsManager = new SettingsManager(this);
        tokenManager = new TokenManager(this);

        bindViews();
        setupUI();
    }

    private void bindViews() {
        backendUrlInput = findViewById(R.id.backendUrlInput);
        testConnectionButton = findViewById(R.id.testConnectionButton);
        saveButton = findViewById(R.id.saveButton);
        resetDefaultsButton = findViewById(R.id.resetDefaultsButton);
        logoutButton = findViewById(R.id.logoutButton);
        googleLoginButton = findViewById(R.id.googleLoginButton);
        githubLoginButton = findViewById(R.id.githubLoginButton);
        progressIndicator = findViewById(R.id.progressIndicator);
        connectionStatus = findViewById(R.id.connectionStatus);
        httpWarning = findViewById(R.id.httpWarning);
        websiteLink = findViewById(R.id.websiteLink);
        accountSection = findViewById(R.id.accountSection);
        loginSection = findViewById(R.id.loginSection);
        accountEmail = findViewById(R.id.accountEmail);
    }

    private void setupUI() {
        // Load current settings
        String currentUrl = settingsManager.getBackendUrl();
        backendUrlInput.setText(currentUrl);
        updateHttpWarning(currentUrl);

        // Setup buttons
        testConnectionButton.setOnClickListener(v -> testConnection());
        saveButton.setOnClickListener(v -> saveSettings());
        resetDefaultsButton.setOnClickListener(v -> confirmResetDefaults());
        logoutButton.setOnClickListener(v -> confirmLogout());
        googleLoginButton.setOnClickListener(v -> startOAuth("google"));
        githubLoginButton.setOnClickListener(v -> startOAuth("github"));
        websiteLink.setOnClickListener(v -> openWebsite());

        // Update account section visibility
        updateAccountSection();
    }

    private void updateAccountSection() {
        boolean loggedIn = tokenManager.hasToken();
        accountSection.setVisibility(loggedIn ? View.VISIBLE : View.GONE);
        loginSection.setVisibility(loggedIn ? View.GONE : View.VISIBLE);

        if (loggedIn) {
            String email = settingsManager.getUserEmail();
            if (email != null && !email.isEmpty()) {
                accountEmail.setText(email);
            } else {
                accountEmail.setText(R.string.account_logged_in);
            }
        }
    }

    private void openWebsite() {
        CustomTabsIntent customTabsIntent = new CustomTabsIntent.Builder()
                .setShowTitle(true)
                .build();
        customTabsIntent.launchUrl(this, Uri.parse(getString(R.string.app_website)));
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

    private void testConnection() {
        String url = backendUrlInput.getText() != null ?
                backendUrlInput.getText().toString().trim() : "";

        if (url.isEmpty()) {
            showConnectionStatus(getString(R.string.error_url_required), false);
            return;
        }

        String normalizedUrl = UrlValidator.normalizeBackendUrl(url);
        if (normalizedUrl == null || !UrlValidator.isValidUrl(normalizedUrl)) {
            showConnectionStatus(getString(R.string.error_invalid_url), false);
            return;
        }

        setLoading(true);
        hideConnectionStatus();
        updateHttpWarning(normalizedUrl);

        // Temporarily set URL for testing
        String originalUrl = settingsManager.getBackendUrl();
        settingsManager.setBackendUrl(normalizedUrl);
        ApiClient.resetClient();

        ClipJotApi api = ApiClient.getApi(this);
        api.listTags(Collections.emptyMap()).enqueue(new Callback<TagsResponse>() {
            @Override
            public void onResponse(Call<TagsResponse> call, Response<TagsResponse> response) {
                setLoading(false);

                if (response.isSuccessful() || response.code() == 401) {
                    // 401 is expected if not logged in - server is reachable
                    showConnectionStatus(getString(R.string.connection_success), true);
                } else {
                    // Restore original URL
                    settingsManager.setBackendUrl(originalUrl);
                    ApiClient.resetClient();
                    showConnectionStatus(getString(R.string.error_server_response, response.code()), false);
                }
            }

            @Override
            public void onFailure(Call<TagsResponse> call, Throwable t) {
                setLoading(false);
                // Restore original URL
                settingsManager.setBackendUrl(originalUrl);
                ApiClient.resetClient();
                showConnectionStatus(getString(R.string.error_connection_failed), false);
            }
        });
    }

    private void saveSettings() {
        String url = backendUrlInput.getText() != null ?
                backendUrlInput.getText().toString().trim() : "";

        if (url.isEmpty()) {
            Toast.makeText(this, R.string.error_url_required, Toast.LENGTH_SHORT).show();
            return;
        }

        String normalizedUrl = UrlValidator.normalizeBackendUrl(url);
        if (normalizedUrl == null || !UrlValidator.isValidUrl(normalizedUrl)) {
            Toast.makeText(this, R.string.error_invalid_url, Toast.LENGTH_SHORT).show();
            return;
        }

        settingsManager.setBackendUrl(normalizedUrl);
        ApiClient.resetClient();

        Toast.makeText(this, R.string.settings_saved, Toast.LENGTH_SHORT).show();
        backendUrlInput.setText(normalizedUrl);
        updateHttpWarning(normalizedUrl);
    }

    private void confirmResetDefaults() {
        new AlertDialog.Builder(this)
                .setTitle(R.string.reset_defaults_title)
                .setMessage(R.string.reset_defaults_confirm)
                .setPositiveButton(R.string.reset_defaults, (dialog, which) -> resetDefaults())
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    private void resetDefaults() {
        settingsManager.resetToDefaults();
        tokenManager.clearToken();
        settingsManager.clearUserData();
        ApiClient.resetClient();

        // Update UI
        String defaultUrl = settingsManager.getBackendUrl();
        backendUrlInput.setText(defaultUrl);
        updateHttpWarning(defaultUrl);
        hideConnectionStatus();
        updateAccountSection();

        Toast.makeText(this, R.string.reset_defaults_done, Toast.LENGTH_SHORT).show();
    }

    private void confirmLogout() {
        new AlertDialog.Builder(this)
                .setTitle(R.string.logout_title)
                .setMessage(R.string.logout_confirm)
                .setPositiveButton(R.string.logout, (dialog, which) -> logout())
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    private void logout() {
        tokenManager.clearToken();
        settingsManager.clearUserData();
        updateAccountSection();
        Toast.makeText(this, R.string.logged_out, Toast.LENGTH_SHORT).show();
    }

    private void setLoading(boolean loading) {
        progressIndicator.setVisibility(loading ? View.VISIBLE : View.GONE);
        testConnectionButton.setEnabled(!loading);
        saveButton.setEnabled(!loading);
        backendUrlInput.setEnabled(!loading);
    }

    private void showConnectionStatus(String message, boolean success) {
        connectionStatus.setText(message);
        connectionStatus.setTextColor(getColor(success ? R.color.success : R.color.error));
        connectionStatus.setVisibility(View.VISIBLE);
    }

    private void hideConnectionStatus() {
        connectionStatus.setVisibility(View.GONE);
    }

    private void updateHttpWarning(String url) {
        if (url != null && url.toLowerCase().startsWith("http://")) {
            httpWarning.setVisibility(View.VISIBLE);
        } else {
            httpWarning.setVisibility(View.GONE);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        // Check if login status changed (e.g., after OAuth callback)
        updateAccountSection();
    }

    @Override
    public boolean onOptionsItemSelected(@NonNull MenuItem item) {
        if (item.getItemId() == android.R.id.home) {
            getOnBackPressedDispatcher().onBackPressed();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }
}
