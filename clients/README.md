# ClipJot Clients

Native apps and extensions for saving bookmarks to [ClipJot](https://clipjot.net).

## Platforms

| Client | Directory | Status |
|--------|-----------|--------|
| [iOS App](ios/) | `clients/ios/` | Production |
| [Android App](android/) | `clients/android/` | Production |
| [Chrome Extension](chrome-extension/) | `clients/chrome-extension/` | Production |

## iOS

Swift/SwiftUI app with Share Extension for saving links from any app.

- **Requirements:** Xcode 15+, iOS 17+
- **Auth:** Google OAuth, GitHub OAuth
- **Features:** Share Extension, offline queue, tag management

See [ios/README.md](ios/README.md) for build instructions.

## Android

Java app with share intent integration for the Android share sheet.

- **Requirements:** Android Studio, SDK 24+
- **Auth:** Google OAuth, GitHub OAuth
- **Features:** Share intent, Material Design, tag autocomplete

See [android/README.md](android/README.md) for build instructions.

## Chrome Extension

Browser extension for one-click bookmark saving.

- **Requirements:** Chrome/Chromium browser
- **Auth:** Google OAuth, GitHub OAuth
- **Features:** Keyboard shortcuts, popup UI, sync

See [chrome-extension/README.md](chrome-extension/README.md) for installation.

## API Integration

All clients communicate with the ClipJot backend via REST API:

- **Production API:** `https://clipjot.net/api/v1`
- **Documentation:** [../docs/api/v1.md](../docs/api/v1.md)

## Configuration

Each client requires OAuth credentials configured for your environment. See individual README files for setup details.
