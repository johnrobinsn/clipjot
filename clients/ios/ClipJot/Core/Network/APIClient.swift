import Foundation

/// API client for ClipJot backend communication.
/// Equivalent to Android's ApiClient + ClipJotApi.
/// Uses actor for thread-safe async operations.
actor APIClient {
    static let shared = APIClient()

    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    private var baseURL: URL {
        // Force unwrap is safe here as SettingsManager always returns a valid URL
        URL(string: SettingsManager.shared.backendUrl)!
    }

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 30
        self.session = URLSession(configuration: config)

        self.decoder = JSONDecoder()
        self.encoder = JSONEncoder()
    }

    // MARK: - Bookmark Endpoints

    /// Add a new bookmark
    func addBookmark(_ request: BookmarkAddRequest) async throws -> Bookmark {
        try await post(endpoint: "api/v1/bookmarks/add", body: request)
    }

    /// Edit an existing bookmark
    func editBookmark(_ request: BookmarkEditRequest) async throws -> Bookmark {
        try await post(endpoint: "api/v1/bookmarks/edit", body: request)
    }

    /// Delete a bookmark
    func deleteBookmark(id: Int) async throws -> DeleteResponse {
        let request = BookmarkDeleteRequest(id: id)
        return try await post(endpoint: "api/v1/bookmarks/delete", body: request)
    }

    /// Search/list bookmarks with pagination
    func searchBookmarks(_ request: BookmarkSearchRequest) async throws -> BookmarkSearchResponse {
        try await post(endpoint: "api/v1/bookmarks/search", body: request)
    }

    /// Get latest bookmark ID (for new links detection)
    func getLatestBookmarkId() async throws -> LatestBookmarkResponse {
        try await get(endpoint: "api/internal/latest-bookmark")
    }

    // MARK: - Tag Endpoints

    /// Get user's tags (also serves as session validation)
    func listTags() async throws -> TagsResponse {
        try await post(endpoint: "api/v1/tags/list", body: EmptyBody())
    }

    // MARK: - Auth Endpoints

    /// Logout and invalidate session
    func logout() async throws -> LogoutResponse {
        try await post(endpoint: "api/v1/logout", body: EmptyBody())
    }

    // MARK: - Private Request Methods

    private func get<T: Decodable>(endpoint: String) async throws -> T {
        let url = baseURL.appendingPathComponent(endpoint)
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        addAuthHeader(to: &request)

        return try await performRequest(request)
    }

    private func post<T: Decodable, B: Encodable>(endpoint: String, body: B) async throws -> T {
        let url = baseURL.appendingPathComponent(endpoint)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        addAuthHeader(to: &request)

        do {
            request.httpBody = try encoder.encode(body)
        } catch {
            throw APIError.encodingError
        }

        return try await performRequest(request)
    }

    private func performRequest<T: Decodable>(_ request: URLRequest) async throws -> T {
        let data: Data
        let response: URLResponse

        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw APIError.networkError(error)
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        // Handle 401 Unauthorized
        if httpResponse.statusCode == 401 {
            throw APIError.unauthorized
        }

        // Handle other error status codes
        guard 200..<300 ~= httpResponse.statusCode else {
            let errorResponse = try? decoder.decode(ServerErrorResponse.self, from: data)
            throw APIError.serverError(
                statusCode: httpResponse.statusCode,
                message: errorResponse?.displayMessage
            )
        }

        // Decode successful response
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    private func addAuthHeader(to request: inout URLRequest) {
        if let token = TokenManager.shared.getToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
    }
}

// MARK: - Helpers

/// Empty body for POST requests that don't need data
private struct EmptyBody: Encodable {}
