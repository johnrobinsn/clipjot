import Foundation

/// Response from tags list endpoint.
/// Equivalent to Android's TagsResponse.
struct TagsResponse: Codable {
    let tags: [Tag]
}
