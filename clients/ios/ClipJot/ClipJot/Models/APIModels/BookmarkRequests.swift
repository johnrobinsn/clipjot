import Foundation

// MARK: - Add Bookmark

/// Request body for creating a new bookmark.
/// Equivalent to Android's BookmarkRequest.
struct BookmarkAddRequest: Codable {
    let url: String
    let title: String?
    let comment: String?
    let tags: [String]

    init(url: String, title: String? = nil, comment: String? = nil, tags: [String] = []) {
        self.url = url
        self.title = title
        self.comment = comment
        self.tags = tags
    }
}

// MARK: - Edit Bookmark

/// Request body for editing an existing bookmark.
/// Equivalent to Android's BookmarkEditRequest.
struct BookmarkEditRequest: Codable {
    let id: Int
    let url: String
    let title: String?
    let comment: String?
    let tags: [String]

    init(id: Int, url: String, title: String? = nil, comment: String? = nil, tags: [String] = []) {
        self.id = id
        self.url = url
        self.title = title
        self.comment = comment
        self.tags = tags
    }
}

// MARK: - Delete Bookmark

/// Request body for deleting a bookmark.
struct BookmarkDeleteRequest: Codable {
    let id: Int
}

// MARK: - Search Bookmarks

/// Request body for searching/listing bookmarks with pagination.
/// Equivalent to Android's BookmarkSearchRequest.
struct BookmarkSearchRequest: Codable {
    let query: String?
    let page: Int
    let pageSize: Int

    enum CodingKeys: String, CodingKey {
        case query
        case page
        case pageSize = "page_size"
    }

    init(query: String? = nil, page: Int = 1, pageSize: Int = 30) {
        self.query = query
        self.page = page
        self.pageSize = pageSize
    }
}

/// Response from bookmark search endpoint.
/// Equivalent to Android's BookmarkSearchResponse.
struct BookmarkSearchResponse: Codable {
    let bookmarks: [Bookmark]
    let hasMore: Bool

    enum CodingKeys: String, CodingKey {
        case bookmarks
        case hasMore = "has_more"
    }
}
