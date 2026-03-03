import Foundation

/// Tag model for bookmark categorization.
/// Equivalent to Android's Tag.
struct Tag: Identifiable, Codable, Equatable, Hashable {
    let id: Int
    let name: String
    let bookmarkCount: Int?

    enum CodingKeys: String, CodingKey {
        case id, name
        case bookmarkCount = "bookmark_count"
    }

    init(id: Int, name: String, bookmarkCount: Int? = nil) {
        self.id = id
        self.name = name
        self.bookmarkCount = bookmarkCount
    }
}
