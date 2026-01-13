import Foundation

/// Manages app settings using UserDefaults with App Group for Share Extension access.
/// Equivalent to Android's SettingsManager with SharedPreferences.
final class SettingsManager {
    static let shared = SettingsManager()

    // App Group identifier for sharing with Share Extension
    private let appGroupIdentifier = "group.com.clipjot.shared"

    // Keys
    private enum Keys {
        static let backendUrl = "backend_url"
        static let userEmail = "user_email"
        static let quickSaveEnabled = "quick_save_enabled"
        static let formExpanded = "form_expanded"
        static let pendingBookmarkUrl = "pending_bookmark_url"
        static let pendingBookmarkTitle = "pending_bookmark_title"
    }

    // Default values
    private let defaultBackendUrl = "https://clipjot.net"

    // Use shared UserDefaults for App Group
    private var defaults: UserDefaults {
        UserDefaults(suiteName: appGroupIdentifier) ?? .standard
    }

    private init() {}

    // MARK: - Backend URL

    /// The backend server URL
    var backendUrl: String {
        get {
            let url = defaults.string(forKey: Keys.backendUrl) ?? defaultBackendUrl
            // Remove trailing slash for consistency
            return url.hasSuffix("/") ? String(url.dropLast()) : url
        }
        set {
            // Remove trailing slash before saving
            let url = newValue.hasSuffix("/") ? String(newValue.dropLast()) : newValue
            defaults.set(url, forKey: Keys.backendUrl)
        }
    }

    /// Reset backend URL to default
    func resetBackendUrl() {
        defaults.removeObject(forKey: Keys.backendUrl)
    }

    // MARK: - User Info

    /// Currently logged in user's email (for display purposes)
    var userEmail: String? {
        get { defaults.string(forKey: Keys.userEmail) }
        set { defaults.set(newValue, forKey: Keys.userEmail) }
    }

    // MARK: - Feature Toggles

    /// Quick save mode - save immediately without showing edit form
    var quickSaveEnabled: Bool {
        get { defaults.bool(forKey: Keys.quickSaveEnabled) }
        set { defaults.set(newValue, forKey: Keys.quickSaveEnabled) }
    }

    /// Whether the bookmark form is expanded (remembers last state)
    var formExpanded: Bool {
        get { defaults.bool(forKey: Keys.formExpanded) }
        set { defaults.set(newValue, forKey: Keys.formExpanded) }
    }

    // MARK: - Pending Bookmark (for Share Extension when not logged in)

    /// Store a pending bookmark when user shares but isn't logged in
    func setPendingBookmark(url: String, title: String?) {
        defaults.set(url, forKey: Keys.pendingBookmarkUrl)
        defaults.set(title, forKey: Keys.pendingBookmarkTitle)
    }

    /// Get pending bookmark if one exists
    func getPendingBookmark() -> (url: String, title: String?)? {
        guard let url = defaults.string(forKey: Keys.pendingBookmarkUrl) else {
            return nil
        }
        let title = defaults.string(forKey: Keys.pendingBookmarkTitle)
        return (url, title)
    }

    /// Check if there's a pending bookmark
    var hasPendingBookmark: Bool {
        defaults.string(forKey: Keys.pendingBookmarkUrl) != nil
    }

    /// Clear pending bookmark after it's been saved
    func clearPendingBookmark() {
        defaults.removeObject(forKey: Keys.pendingBookmarkUrl)
        defaults.removeObject(forKey: Keys.pendingBookmarkTitle)
    }

    // MARK: - Logout

    /// Clear all user-related settings (called on logout)
    func clearUserData() {
        userEmail = nil
        clearPendingBookmark()
    }

    /// Reset all settings to defaults
    func resetAll() {
        let keys = [
            Keys.backendUrl,
            Keys.userEmail,
            Keys.quickSaveEnabled,
            Keys.formExpanded,
            Keys.pendingBookmarkUrl,
            Keys.pendingBookmarkTitle,
        ]
        keys.forEach { defaults.removeObject(forKey: $0) }
    }
}
