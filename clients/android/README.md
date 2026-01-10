# ClipJot Android Client

Android app for saving bookmarks to your ClipJot server.

## Features

- **Share Intent Receiver**: Save URLs from any app using Android's share sheet
- **Bottom Sheet UI**: Quick capture with expandable form
- **Tag Support**: Autocomplete from your tag vocabulary, create new tags on-the-fly
- **OAuth Authentication**: Sign in with Google or GitHub
- **Secure Token Storage**: Uses Android EncryptedSharedPreferences
- **Configurable Backend**: Connect to self-hosted or hosted ClipJot instance

## Requirements

- Android 10 (API 29) or higher
- ClipJot backend server

## Building

### Prerequisites

- Android Studio Hedgehog (2023.1.1) or later
- JDK 17

### Build Steps

1. Open the project in Android Studio:
   ```
   File > Open > clients/android
   ```

2. Sync Gradle files when prompted

3. Build the debug APK:
   ```bash
   ./gradlew assembleDebug
   ```
   The APK will be at `app/build/outputs/apk/debug/app-debug.apk`

4. For release builds:
   ```bash
   ./gradlew assembleRelease
   ```

### Running on Emulator

For local development with the backend running on localhost:

1. The app uses `http://localhost:5001` as the default backend URL
2. On Android emulator, localhost refers to the emulator itself, not your host machine
3. Set up reverse port forwarding so the emulator can reach your host's localhost:
   ```bash
   adb reverse tcp:5001 tcp:5001
   ```
   This maps `localhost:5001` inside the emulator to `localhost:5001` on your host machine.

4. Install and launch the app:
   ```bash
   ./gradlew installDebug
   adb shell am start -a android.intent.action.SEND -t "text/plain" \
       --es android.intent.extra.TEXT "https://example.com" \
       -n com.clipjot.android/.ui.share.ShareActivity
   ```

**Note**: The `adb reverse` mapping is required for OAuth flows to work correctly, since GitHub/Google redirect back to `localhost:5001`.

**Alternative**: Instead of `adb reverse`, you can change the backend URL in the app's Settings to `http://10.0.2.2:5001` (the special Android emulator IP that routes to the host). However, this won't work for OAuth redirects.

## Usage

### First Time Setup

1. Install the app on your Android device
2. Open Settings and configure your backend URL
3. Tap "Test Connection" to verify connectivity
4. Return to the app and sign in with Google or GitHub

### Saving Bookmarks

1. Find a URL you want to save in any app (browser, Twitter, etc.)
2. Tap the Share button
3. Select "ClipJot" from the share sheet
4. Add a title, tags, and optional comment
5. Tap "Save"

### Managing Settings

- Open the app directly to access Settings
- Configure backend URL
- View account information
- Log out

## Project Structure

```
app/src/main/
├── java/com/clipjot/android/
│   ├── ClipJotApplication.java     # Application class
│   ├── data/
│   │   ├── api/                    # Retrofit API client
│   │   │   ├── ClipJotApi.java     # API interface
│   │   │   ├── ApiClient.java      # Retrofit singleton
│   │   │   ├── AuthInterceptor.java
│   │   │   └── model/              # Request/response models
│   │   └── prefs/                  # Preferences
│   │       ├── TokenManager.java   # Secure token storage
│   │       └── SettingsManager.java
│   ├── ui/
│   │   ├── auth/                   # Login & OAuth
│   │   ├── share/                  # Share intent handling
│   │   └── settings/               # Settings screen
│   └── util/
│       └── UrlValidator.java
└── res/
    ├── layout/                     # XML layouts
    ├── values/                     # Strings, colors, themes
    └── drawable/                   # Icons
```

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/bookmarks/add` | Save new bookmark |
| `POST /api/v1/tags/list` | Fetch user's tags |
| `GET /auth/google` | Start Google OAuth |
| `GET /auth/github` | Start GitHub OAuth |

## Deep Link

The app registers a deep link handler for OAuth callbacks:

```
clipjot://oauth/callback?token={session_token}
```

## Dependencies

- **AndroidX**: AppCompat, Material, Browser, Security
- **Retrofit**: HTTP client
- **Gson**: JSON parsing
- **OkHttp**: HTTP logging

## License

Same as the main ClipJot project.
