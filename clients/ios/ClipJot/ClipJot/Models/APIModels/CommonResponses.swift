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
    private let isPremiumRaw: IntOrBool
    let createdAt: String

    var isPremium: Bool { isPremiumRaw.boolValue }

    enum CodingKeys: String, CodingKey {
        case email, provider
        case isPremiumRaw = "is_premium"
        case createdAt = "created_at"
    }
}

/// Decodes both JSON `true`/`false` and `0`/`1` as a boolean.
struct IntOrBool: Codable {
    let boolValue: Bool

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let boolVal = try? container.decode(Bool.self) {
            boolValue = boolVal
        } else if let intVal = try? container.decode(Int.self) {
            boolValue = intVal != 0
        } else {
            boolValue = false
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        try container.encode(boolValue)
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
