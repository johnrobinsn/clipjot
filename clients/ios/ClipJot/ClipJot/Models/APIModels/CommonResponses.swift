import Foundation

/// Generic success response for operations like delete, logout.
struct SuccessResponse: Codable {
    let success: Bool
    let message: String?
}

/// Response from delete endpoint.
/// Equivalent to Android's DeleteResponse.
typealias DeleteResponse = SuccessResponse

/// Response from logout endpoint.
/// Equivalent to Android's LogoutResponse.
typealias LogoutResponse = SuccessResponse

/// Response containing latest bookmark ID and update timestamp (for new links detection).
/// Equivalent to Android's LatestBookmarkResponse.
struct LatestBookmarkResponse: Codable {
    let id: Int?
    let lastUpdated: String?

    enum CodingKeys: String, CodingKey {
        case id
        case lastUpdated = "last_updated"
    }
}

// MARK: - User Profile

/// Response from user profile endpoint.
struct UserProfileResponse: Codable {
    let email: String
    let provider: String?
    let isPremium: Bool
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case email, provider
        case isPremium = "is_premium"
        case createdAt = "created_at"
    }
}

// MARK: - Invite Code Auth

/// Request body for invite code authentication.
struct InviteCodeAuthRequest: Codable {
    let code: String
    let clientName: String

    enum CodingKeys: String, CodingKey {
        case code
        case clientName = "client_name"
    }
}

/// User info returned from invite code authentication.
struct InviteCodeUser: Codable {
    let id: Int
    let email: String
}

/// Response from invite code authentication endpoint.
struct InviteCodeAuthResponse: Codable {
    let token: String
    let user: InviteCodeUser
}
