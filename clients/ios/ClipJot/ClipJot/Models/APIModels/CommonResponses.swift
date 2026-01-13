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

/// Response containing latest bookmark ID (for new links detection).
/// Equivalent to Android's LatestBookmarkResponse.
struct LatestBookmarkResponse: Codable {
    let latestId: Int?

    enum CodingKeys: String, CodingKey {
        case latestId = "latest_id"
    }
}
