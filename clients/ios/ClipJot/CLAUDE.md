# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Run

This is an Xcode project. Open `ClipJot.xcodeproj` in Xcode.

- **Build**: ⌘B or `xcodebuild -scheme ClipJot -sdk iphonesimulator build`
- **Run**: ⌘R (requires Xcode GUI)
- **Test**: ⌘U or `xcodebuild test -scheme ClipJot -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 16'`

Requirements: iOS 15.0+, Xcode 15.0+

## Architecture

SwiftUI app using MVVM pattern with `@StateObject` and `@ObservableObject`. All async operations use `async/await`. No external dependencies.

### Core Components

- **APIClient** (`Core/Network/APIClient.swift`): Actor-based URLSession client for all backend communication. All API methods are async throws.
- **TokenManager** (`Core/Storage/TokenManager.swift`): Keychain-based session token storage, shared with Share Extension via App Groups.
- **AuthManager** (`Features/Auth/AuthManager.swift`): OAuth flow via `ASWebAuthenticationSession`. Handles `clipjot://` URL scheme callbacks.
- **SettingsManager** (`Core/Storage/SettingsManager.swift`): UserDefaults wrapper for app settings and pending bookmarks.

### Data Flow

1. **Auth**: LoginView → AuthManager.startOAuth() → ASWebAuthenticationSession → Backend OAuth → `clipjot://oauth/callback?token=xxx` → TokenManager.saveToken()
2. **API calls**: Views call APIClient methods → Bearer token from TokenManager → JSON responses decoded to Models
3. **Share Extension**: Saves pending bookmarks via SettingsManager (App Groups) when logged out; main app processes them on next launch

### Key Patterns

- Singletons via `.shared` for managers (APIClient, TokenManager, AuthManager, SettingsManager)
- `@MainActor` for UI-bound managers
- `actor` for thread-safe APIClient
- Environment injection of AuthManager into view hierarchy

### Backend API

All endpoints use POST with JSON body. See `/docs/SPEC.md` in the root project for full API specification.

Key endpoints:
- `/api/v1/bookmarks/add`, `/edit`, `/delete`, `/search`
- `/api/v1/tags/list`, `/create`, `/update`, `/delete`
- `/auth/{google|github}` - OAuth initiation
