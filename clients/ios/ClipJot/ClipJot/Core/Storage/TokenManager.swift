import Foundation
import Security

/// Manages secure token storage using iOS Keychain.
/// Equivalent to Android's TokenManager with EncryptedSharedPreferences.
final class TokenManager {
    static let shared = TokenManager()

    private let service = "com.clipjot.ios"
    private let account = "session_token"

    // Access group for sharing with Share Extension
    // Format: $(AppIdentifierPrefix)com.clipjot.shared
    // The AppIdentifierPrefix is added automatically by Xcode
    private let accessGroup: String? = "com.clipjot.shared"

    private init() {}

    // MARK: - Public Interface

    /// Check if user is logged in (has valid token)
    var isLoggedIn: Bool {
        getToken() != nil
    }

    /// Save session token to Keychain
    /// - Parameter token: The session token to store
    /// - Throws: KeychainError if save fails
    func saveToken(_ token: String) throws {
        guard let data = token.data(using: .utf8) else {
            throw KeychainError.encodingFailed
        }

        // Delete existing token first
        try? deleteToken()

        var query = baseQuery()
        query[kSecValueData as String] = data
        query[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly

        let status = SecItemAdd(query as CFDictionary, nil)

        guard status == errSecSuccess else {
            throw KeychainError.saveFailed(status)
        }
    }

    /// Retrieve session token from Keychain
    /// - Returns: The stored token, or nil if not found
    func getToken() -> String? {
        var query = baseQuery()
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let token = String(data: data, encoding: .utf8)
        else {
            return nil
        }

        return token
    }

    /// Delete session token from Keychain (logout)
    /// - Throws: KeychainError if deletion fails (ignores "not found" errors)
    func deleteToken() throws {
        let query = baseQuery()
        let status = SecItemDelete(query as CFDictionary)

        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw KeychainError.deleteFailed(status)
        }
    }

    /// Clear token (convenience method that doesn't throw)
    func clearToken() {
        try? deleteToken()
    }

    // MARK: - Private Helpers

    private func baseQuery() -> [String: Any] {
        var query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]

        // Add access group for sharing with Share Extension
        if let accessGroup = accessGroup {
            query[kSecAttrAccessGroup as String] = accessGroup
        }

        return query
    }
}

// MARK: - Errors

enum KeychainError: LocalizedError {
    case encodingFailed
    case saveFailed(OSStatus)
    case deleteFailed(OSStatus)

    var errorDescription: String? {
        switch self {
        case .encodingFailed:
            return "Failed to encode token data"
        case .saveFailed(let status):
            return "Failed to save to Keychain: \(status)"
        case .deleteFailed(let status):
            return "Failed to delete from Keychain: \(status)"
        }
    }
}
