package com.clipjot.android.ui.auth;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputFilter;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.browser.customtabs.CustomTabsIntent;

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
            navigateToMyLinks();
            return;
        }

        setupButtons();
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
        // Check if we got logged in while away (e.g., after OAuth callback)
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
