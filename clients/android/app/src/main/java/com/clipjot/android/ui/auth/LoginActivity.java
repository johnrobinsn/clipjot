package com.clipjot.android.ui.auth;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputFilter;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.browser.auth.AuthTabIntent;

import com.clipjot.android.BuildConfig;
import com.clipjot.android.R;
import com.clipjot.android.data.api.ApiClient;
import com.clipjot.android.data.api.model.InviteCodeAuthResponse;
import com.clipjot.android.data.api.model.InviteCodeRequest;
import com.clipjot.android.data.prefs.SettingsManager;
import com.clipjot.android.data.prefs.TokenManager;
import com.clipjot.android.ui.links.MyLinksActivity;
import com.clipjot.android.ui.settings.SettingsActivity;
import com.google.android.material.button.MaterialButton;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Login activity with OAuth provider buttons.
 *
 * Uses Chrome Auth Tab API (Chrome 137+) for OAuth, which automatically
 * intercepts the custom scheme redirect and closes the tab. Falls back
 * to regular Custom Tabs on older Chrome, where OAuthCallbackActivity
 * handles the redirect via intent filter.
 */
public class LoginActivity extends AppCompatActivity {

    private static final String CALLBACK_URI = BuildConfig.OAUTH_SCHEME + "://oauth/callback";

    private SettingsManager settingsManager;
    private TokenManager tokenManager;

    // Auth Tab launcher — handles OAuth result when Chrome 137+ is available.
    // On older Chrome, this receives RESULT_CANCELED and the existing
    // OAuthCallbackActivity handles the redirect instead.
    private final ActivityResultLauncher<Intent> authLauncher =
            AuthTabIntent.registerActivityResultLauncher(this, this::handleAuthResult);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        // Hide action bar - we have a custom header in the layout
        if (getSupportActionBar() != null) {
            getSupportActionBar().hide();
        }

        settingsManager = new SettingsManager(this);
        tokenManager = new TokenManager(this);

        // Check if already logged in
        if (tokenManager.hasToken()) {
            navigateToMyLinks();
            return;
        }

        setupButtons();

        // Check for OAuth error passed from OAuthCallbackActivity
        checkForOAuthError(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        // Handle OAuth error when activity is reused
        checkForOAuthError(intent);
    }

    private void checkForOAuthError(Intent intent) {
        if (intent != null && intent.hasExtra("oauth_error")) {
            String error = intent.getStringExtra("oauth_error");
            intent.removeExtra("oauth_error"); // Don't show again on rotation
            if (error != null && !error.isEmpty()) {
                showOAuthErrorDialog(error);
            }
        }
    }

    private void showOAuthErrorDialog(String error) {
        String message = error + "\n\n" + getString(R.string.login_error_retry_hint);
        new AlertDialog.Builder(this)
                .setTitle(R.string.login_error_title)
                .setMessage(message)
                .setPositiveButton(android.R.string.ok, null)
                .show();
    }

    private void setupButtons() {
        MaterialButton googleButton = findViewById(R.id.googleLoginButton);
        MaterialButton githubButton = findViewById(R.id.githubLoginButton);
        MaterialButton settingsButton = findViewById(R.id.settingsButton);
        TextView inviteCodeLink = findViewById(R.id.inviteCodeLink);

        googleButton.setOnClickListener(v -> startOAuth("google"));
        githubButton.setOnClickListener(v -> startOAuth("github"));
        settingsButton.setOnClickListener(v -> openSettings());
        inviteCodeLink.setOnClickListener(v -> showInviteCodeDialog());
    }

    private void startOAuth(String provider) {
        try {
            String backendUrl = settingsManager.getBackendUrl();
            String redirectUri = URLEncoder.encode(CALLBACK_URI, "UTF-8");
            String authUrl = backendUrl + "/auth/" + provider + "?redirect_uri=" + redirectUri;

            // Use Auth Tab API (Chrome 137+) — automatically intercepts the
            // custom scheme redirect and closes the tab. Falls back to regular
            // Custom Tabs on older Chrome.
            AuthTabIntent authTabIntent = new AuthTabIntent.Builder().build();
            authTabIntent.launch(authLauncher, Uri.parse(authUrl), BuildConfig.OAUTH_SCHEME);

        } catch (UnsupportedEncodingException e) {
            Toast.makeText(this, R.string.error_oauth_failed, Toast.LENGTH_SHORT).show();
        }
    }

    private void handleAuthResult(AuthTabIntent.AuthResult result) {
        if (result.resultCode == AuthTabIntent.RESULT_OK && result.resultUri != null) {
            // Auth Tab intercepted the redirect — extract token directly
            String token = result.resultUri.getQueryParameter("token");
            String error = result.resultUri.getQueryParameter("error");

            if (token != null && !token.isEmpty()) {
                tokenManager.saveToken(token);
                Toast.makeText(this, R.string.login_success, Toast.LENGTH_SHORT).show();
                navigateToMyLinks();
            } else if (error != null && !error.isEmpty()) {
                showOAuthErrorDialog(error);
            }
        }
        // For RESULT_CANCELED: either user closed the tab, or Auth Tab isn't
        // supported and it fell back to Custom Tabs. In the fallback case,
        // OAuthCallbackActivity handles the redirect and onResume() picks it up.
    }

    private void openSettings() {
        Intent intent = new Intent(this, SettingsActivity.class);
        startActivity(intent);
    }

    private void showInviteCodeDialog() {
        EditText input = new EditText(this);
        input.setHint(R.string.invite_code_hint);
        input.setFilters(new InputFilter[]{
                new InputFilter.AllCaps(),
                new InputFilter.LengthFilter(8)
        });
        input.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS);

        int padding = (int) (16 * getResources().getDisplayMetrics().density);
        input.setPadding(padding, padding, padding, padding);

        new AlertDialog.Builder(this)
                .setTitle(R.string.invite_code_title)
                .setView(input)
                .setPositiveButton(R.string.submit, (dialog, which) -> {
                    String code = input.getText().toString().trim().toUpperCase();
                    if (code.length() == 8) {
                        authenticateWithInviteCode(code);
                    } else {
                        Toast.makeText(this, "Please enter a valid 8-character code", Toast.LENGTH_SHORT).show();
                    }
                })
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    private void authenticateWithInviteCode(String code) {
        InviteCodeRequest request = new InviteCodeRequest(code);

        ApiClient.getApiWithoutAuth(this)
                .authenticateWithInviteCode(request)
                .enqueue(new Callback<InviteCodeAuthResponse>() {
                    @Override
                    public void onResponse(Call<InviteCodeAuthResponse> call, Response<InviteCodeAuthResponse> response) {
                        if (response.isSuccessful() && response.body() != null) {
                            InviteCodeAuthResponse authResponse = response.body();
                            tokenManager.saveToken(authResponse.getToken());
                            if (authResponse.getUser() != null) {
                                settingsManager.setUserEmail(authResponse.getUser().getEmail());
                            }
                            Toast.makeText(LoginActivity.this, R.string.login_success, Toast.LENGTH_SHORT).show();
                            navigateToMyLinks();
                        } else {
                            String errorMessage = "Invalid invite code";
                            Toast.makeText(LoginActivity.this, errorMessage, Toast.LENGTH_SHORT).show();
                        }
                    }

                    @Override
                    public void onFailure(Call<InviteCodeAuthResponse> call, Throwable t) {
                        Toast.makeText(LoginActivity.this, R.string.error_network, Toast.LENGTH_SHORT).show();
                    }
                });
    }

    @Override
    protected void onResume() {
        super.onResume();
        // Fallback: check if OAuthCallbackActivity saved a token (Custom Tabs flow)
        if (tokenManager.hasToken()) {
            navigateToMyLinks();
        }
    }

    private void navigateToMyLinks() {
        Intent intent = new Intent(this, MyLinksActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }
}
