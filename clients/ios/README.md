# ClipJot iOS Client

Native iOS app for ClipJot bookmark manager, built with Swift and SwiftUI.

## Features

- **Share Extension**: Save links from Safari, Twitter, and any app with share functionality
- **OAuth Authentication**: Sign in with Google or GitHub
- **Bookmark Management**: View, search, add, edit, and delete bookmarks
- **Tag Autocomplete**: Organize bookmarks with tags
- **Quick Save Mode**: Optionally save links instantly without showing the edit form
- **Offline Pending**: Share links while logged out, save them after signing in

## Requirements

- iOS 15.0+
- Xcode 15.0+
- Apple Developer account (for App Groups and Keychain Sharing capabilities)

## Project Setup (Mac Required)

Since Xcode projects can't be created without a Mac, follow these steps:

### 1. Create Xcode Project

1. Open Xcode
2. File → New → Project → iOS → App
3. Configure:
   - Product Name: `ClipJot`
   - Team: Your Apple ID or development team
   - Organization Identifier: `com.clipjot`
   - Interface: SwiftUI
   - Language: Swift
   - Uncheck "Include Tests" (add later if needed)
4. Save to `clients/ios/`

### 2. Add Share Extension Target

1. File → New → Target → iOS → Share Extension
2. Product Name: `ShareExtension`
3. Language: Swift
4. Don't activate the scheme when prompted

### 3. Configure Capabilities

#### Main App Target (ClipJot):
1. Select ClipJot target → Signing & Capabilities
2. Add capability: **App Groups**
   - Add: `group.com.clipjot.shared`
3. Add capability: **Keychain Sharing**
   - Add: `com.clipjot.shared`

#### Share Extension Target:
1. Select ShareExtension target → Signing & Capabilities
2. Add the same **App Groups** and **Keychain Sharing** capabilities

### 4. Add Source Files

1. Delete the template files Xcode created
2. Drag the following folders into the ClipJot group:
   - `ClipJot/Core/`
   - `ClipJot/Models/`
   - `ClipJot/Features/`
   - `ClipJot/ClipJotApp.swift`
3. Drag ShareExtension files into ShareExtension group:
   - `ShareExtension/ShareViewController.swift`
   - `ShareExtension/ShareBookmarkView.swift`
4. Ensure "Copy items if needed" is checked
5. Verify target membership is correct

### 5. Configure Info.plist

The `Info.plist` files are already configured. Make sure Xcode uses them:
- ClipJot target: `ClipJot/Info.plist`
- ShareExtension target: `ShareExtension/Info.plist`

### 6. Configure URL Scheme

1. Select ClipJot target → Info → URL Types
2. Click + and add:
   - Identifier: `com.clipjot.ios`
   - URL Schemes: `clipjot`

### 7. Build and Run

1. Select an iOS Simulator or device
2. Build (⌘B) to check for errors
3. Run (⌘R) to test

## Project Structure

```
ClipJot/
├── ClipJotApp.swift           # App entry point, deep link handling
├── Info.plist                  # URL schemes, permissions
├── ClipJot.entitlements       # App Groups, Keychain
│
├── Core/
│   ├── Network/
│   │   ├── APIClient.swift    # URLSession API client
│   │   └── APIError.swift     # Error types
│   ├── Storage/
│   │   ├── TokenManager.swift # Keychain token storage
│   │   └── SettingsManager.swift # UserDefaults settings
│   └── Utilities/
│       └── URLValidator.swift # URL validation
│
├── Models/
│   ├── Bookmark.swift
│   ├── Tag.swift
│   └── APIModels/             # Request/Response types
│
└── Features/
    ├── Auth/
    │   ├── LoginView.swift
    │   └── AuthManager.swift
    ├── Bookmarks/
    │   ├── BookmarkListView.swift
    │   ├── BookmarkListViewModel.swift
    │   ├── BookmarkRowView.swift
    │   ├── BookmarkFormView.swift
    │   └── TagInputView.swift
    └── Settings/
        └── SettingsView.swift

ShareExtension/
├── ShareViewController.swift  # UIKit entry point
├── ShareBookmarkView.swift    # SwiftUI form
├── Info.plist
└── ShareExtension.entitlements
```

## Configuration

### Backend URL

Default backend is `https://clipjot.net`. To change:
1. Open the app
2. Go to Settings
3. Enter your backend URL
4. Tap "Test Connection" to verify

### Local Development

For local backend testing:
1. Run your backend on `localhost:5001`
2. In Settings, enter `http://localhost:5001`
3. Note: Simulator can access localhost directly

## OAuth Flow

The app uses ASWebAuthenticationSession for OAuth:

1. User taps "Sign in with Google" or "Sign in with GitHub"
2. System browser opens `{backend}/auth/{provider}?redirect_uri=clipjot://oauth/callback`
3. User authenticates with provider
4. Backend redirects to `clipjot://oauth/callback?token={session_token}`
5. App receives callback via URL scheme
6. Token is saved to Keychain

## Share Extension

The Share Extension allows saving links from any app:

1. User shares a link from Safari, Twitter, etc.
2. "Save to ClipJot" appears in share sheet
3. If logged in: Shows bookmark form
4. If not logged in: Saves as "pending" bookmark
5. Pending bookmarks are saved when user logs in to main app

## Architecture

- **SwiftUI** for all UI (except Share Extension entry point)
- **MVVM** pattern with `@StateObject` and `@ObservableObject`
- **async/await** for all async operations
- **URLSession** for networking (no external dependencies)
- **Keychain** for secure token storage
- **App Groups** for data sharing with extension

## Troubleshooting

### Share Extension Not Appearing

1. Ensure ShareExtension target has correct activation rules in Info.plist
2. Check that App Group identifiers match exactly
3. Try restarting the simulator/device

### OAuth Callback Not Working

1. Verify URL scheme `clipjot` is registered in Info.plist
2. Check that backend redirect URI matches exactly
3. Ensure ASWebAuthenticationSession has a valid presentation anchor

### Keychain Errors

1. Verify Keychain Access Group matches in both targets
2. Check entitlements are properly configured
3. On device, ensure same team ID is used for both targets

## License

MIT License - see project root LICENSE file.
