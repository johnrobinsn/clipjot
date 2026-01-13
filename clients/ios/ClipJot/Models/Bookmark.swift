import Foundation

/// Bookmark model representing a saved link.
/// Equivalent to Android's BookmarkResponse.
struct Bookmark: Identifiable, Codable, Equatable {
    let id: Int
    let url: String
    let title: String?
    let comment: String?
    let tags: [String]
    let clientName: String?
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id
        case url
        case title
        case comment
        case tags
        case clientName = "client_name"
        case createdAt = "created_at"
    }

    /// Display title - uses title if available, otherwise URL
    var displayTitle: String {
        if let title = title, !title.isEmpty {
            return title
        }
        return url
    }

    /// Formatted domain for display
    var domain: String? {
        guard let urlObj = URL(string: url),
              let host = urlObj.host else {
            return nil
        }
        // Remove www. prefix
        return host.hasPrefix("www.") ? String(host.dropFirst(4)) : host
    }
}
