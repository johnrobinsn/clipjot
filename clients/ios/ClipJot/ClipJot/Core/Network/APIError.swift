import Foundation

/// API error types for network operations.
/// Equivalent to Android's ApiError handling.
enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case unauthorized
    case serverError(statusCode: Int, message: String?)
    case networkError(Error)
    case decodingError(Error)
    case encodingError

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid server response"
        case .unauthorized:
            return "Session expired. Please log in again."
        case .serverError(let statusCode, let message):
            if let message = message {
                return message
            }
            return "Server error: \(statusCode)"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .decodingError(let error):
            return "Failed to parse response: \(error.localizedDescription)"
        case .encodingError:
            return "Failed to encode request"
        }
    }

    /// Whether this error indicates the user should be logged out
    var requiresLogout: Bool {
        if case .unauthorized = self {
            return true
        }
        return false
    }
}

/// Server error response structure
struct ServerErrorResponse: Codable {
    let error: String?
    let message: String?
    let errorCode: Int?

    enum CodingKeys: String, CodingKey {
        case error
        case message
        case errorCode = "error_code"
    }

    var displayMessage: String? {
        error ?? message
    }
}
