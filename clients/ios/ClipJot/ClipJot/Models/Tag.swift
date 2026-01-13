import Foundation

/// Tag model for bookmark categorization.
/// Equivalent to Android's Tag.
struct Tag: Identifiable, Codable, Equatable, Hashable {
    let id: Int
    let name: String

    // Identifiable conformance using name as identifier
    // (tags are unique by name within a user's account)
}
