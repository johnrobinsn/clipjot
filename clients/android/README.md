# ClipJot for Android

Save bookmarks to [ClipJot](https://clipjot.net) from any app.

## Features

- **Share from anywhere** - Save links from any app using Android's share sheet
- **Quick capture** - Bottom sheet UI for fast saving
- **Tag support** - Add tags with autocomplete
- **Direct Share** - Quick share targets for one-tap saving
- **Secure** - Encrypted token storage, HTTPS-only

## Installation

### Download APK

1. Go to the [latest release](https://github.com/johnrobinsn/clipjot/releases/tag/android-v1.0.0)
2. Download `app-release.apk`
3. On your Android device, open the APK file
4. If prompted, allow installation from unknown sources
5. Tap **Install**

> **Note:** Requires Android 10 or higher.

### Sign In

1. Open ClipJot from your app drawer
2. Sign in with **Google** or **GitHub**
3. You're ready to save bookmarks!

## Usage

### Save a Link

1. Find something you want to save (in a browser, Twitter, etc.)
2. Tap the **Share** button
3. Select **ClipJot** from the share sheet
4. Add tags or a comment (optional)
5. Tap **Save**

### Quick Save with Direct Share

After saving a few bookmarks, ClipJot appears in your Direct Share targets for even faster saving:

1. Tap **Share** on any content
2. Look for the ClipJot icon in the top row
3. Tap to save instantly

### View Your Bookmarks

1. Open the ClipJot app
2. Browse or search your saved links
3. Tap any bookmark to open it

## Settings

Open the app and tap the **gear icon** to access settings:

- **Backend URL** - Server address (default: `https://clipjot.net`)
- **Account** - View logged-in account
- **Sign Out** - Log out of your account

## Troubleshooting

**"Session expired" or signed out?**
- Open the app and sign in again

**App not appearing in share sheet?**
- Make sure you're sharing text/URL content
- Try restarting your device

**Can't install APK?**
- Go to Settings > Security > Install unknown apps
- Enable for your file manager or browser

---

## For Developers

### Building from Source

**Requirements:**
- Android Studio Hedgehog (2023.1.1) or later
- JDK 17

**Build debug APK:**
```bash
cd clients/android
./gradlew assembleDebug
```

**Build release APK** (requires signing configuration):
```bash
./gradlew assembleRelease
```

### Release Signing

1. Create `keystore.properties` in the android directory:
   ```properties
   storeFile=path/to/your-keystore.jks
   storePassword=your-store-password
   keyAlias=your-key-alias
   keyPassword=your-key-password
   ```

2. Build the release APK:
   ```bash
   ./gradlew assembleRelease
   ```

### Project Structure

```
app/src/main/java/com/clipjot/android/
├── data/api/          # API client (Retrofit)
├── data/prefs/        # Token & settings storage
├── ui/auth/           # Login screens
├── ui/share/          # Share sheet handling
├── ui/links/          # Bookmark list
└── ui/settings/       # Settings screen
```

### Local Development

For testing with a local backend:
```bash
# Forward emulator port to host
adb reverse tcp:5001 tcp:5001
```

Then set backend URL to `http://localhost:5001` in Settings.
