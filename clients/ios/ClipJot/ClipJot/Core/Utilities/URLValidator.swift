import Foundation

/// URL validation and extraction utilities.
/// Equivalent to Android's UrlValidator.
struct URLValidator {
    /// Regular expression pattern for URL matching
    private static let urlPattern = try! NSRegularExpression(
        pattern: #"https?://[^\s<>\"\']+"#,
        options: [.caseInsensitive]
    )

    /// Extract the first URL from a text string
    /// - Parameter text: Text that may contain a URL
    /// - Returns: The first URL found, or nil
    static func extractURL(from text: String) -> String? {
        let range = NSRange(text.startIndex..., in: text)
        guard let match = urlPattern.firstMatch(in: text, options: [], range: range),
              let matchRange = Range(match.range, in: text)
        else {
            return nil
        }
        return String(text[matchRange])
    }

    /// Check if a string is a valid URL
    /// - Parameter urlString: String to validate
    /// - Returns: true if valid URL
    static func isValidURL(_ urlString: String) -> Bool {
        guard let url = URL(string: urlString),
              let scheme = url.scheme?.lowercased(),
              (scheme == "http" || scheme == "https"),
              url.host != nil
        else {
            return false
        }
        return true
    }

    /// Normalize a URL (ensure https, remove trailing slash)
    /// - Parameter urlString: URL to normalize
    /// - Returns: Normalized URL string
    static func normalizeURL(_ urlString: String) -> String {
        var normalized = urlString.trimmingCharacters(in: .whitespacesAndNewlines)

        // Add https if no scheme
        if !normalized.lowercased().hasPrefix("http://") &&
           !normalized.lowercased().hasPrefix("https://") {
            normalized = "https://" + normalized
        }

        // Remove trailing slash
        if normalized.hasSuffix("/") {
            normalized = String(normalized.dropLast())
        }

        return normalized
    }

    /// Check if URL uses HTTPS
    /// - Parameter urlString: URL to check
    /// - Returns: true if HTTPS
    static func isHTTPS(_ urlString: String) -> Bool {
        urlString.lowercased().hasPrefix("https://")
    }
}
