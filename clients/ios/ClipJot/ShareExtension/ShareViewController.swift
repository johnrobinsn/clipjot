import UIKit
import SwiftUI
import UniformTypeIdentifiers

/// Share Extension entry point (UIKit-based, required).
/// Hosts the SwiftUI ShareBookmarkView.
/// Equivalent to Android's ShareActivity.
class ShareViewController: UIViewController {

    override func viewDidLoad() {
        super.viewDidLoad()

        // Extract shared content
        extractSharedContent { [weak self] url, title in
            guard let self = self else { return }

            if let url = url {
                // Create and present the SwiftUI view
                let shareView = ShareBookmarkView(
                    url: url,
                    title: title,
                    onComplete: { [weak self] in
                        self?.completeRequest()
                    },
                    onCancel: { [weak self] in
                        self?.cancelRequest()
                    }
                )

                let hostingController = UIHostingController(rootView: shareView)
                hostingController.view.backgroundColor = .clear

                // Add as child view controller
                self.addChild(hostingController)
                self.view.addSubview(hostingController.view)
                hostingController.view.translatesAutoresizingMaskIntoConstraints = false

                NSLayoutConstraint.activate([
                    hostingController.view.topAnchor.constraint(equalTo: self.view.topAnchor),
                    hostingController.view.bottomAnchor.constraint(equalTo: self.view.bottomAnchor),
                    hostingController.view.leadingAnchor.constraint(equalTo: self.view.leadingAnchor),
                    hostingController.view.trailingAnchor.constraint(equalTo: self.view.trailingAnchor),
                ])

                hostingController.didMove(toParent: self)
            } else {
                // No valid URL found
                self.showError("No URL found in shared content")
            }
        }
    }

    // MARK: - Content Extraction

    private func extractSharedContent(completion: @escaping (String?, String?) -> Void) {
        guard let extensionItems = extensionContext?.inputItems as? [NSExtensionItem] else {
            completion(nil, nil)
            return
        }

        var foundURL: String?
        var foundTitle: String?

        let group = DispatchGroup()

        for item in extensionItems {
            // Try to get title from attributed content text
            if let attributedTitle = item.attributedContentText?.string {
                foundTitle = attributedTitle
            }

            guard let attachments = item.attachments else { continue }

            for provider in attachments {
                // Check for URL type
                if provider.hasItemConformingToTypeIdentifier(UTType.url.identifier) {
                    group.enter()
                    provider.loadItem(forTypeIdentifier: UTType.url.identifier, options: nil) { item, _ in
                        if let url = item as? URL {
                            foundURL = url.absoluteString
                        }
                        group.leave()
                    }
                }
                // Check for plain text (might contain URL)
                else if provider.hasItemConformingToTypeIdentifier(UTType.plainText.identifier) {
                    group.enter()
                    provider.loadItem(forTypeIdentifier: UTType.plainText.identifier, options: nil) { item, _ in
                        if let text = item as? String {
                            // Try to extract URL from text
                            if let extractedURL = URLValidator.extractURL(from: text) {
                                foundURL = extractedURL
                            } else if URLValidator.isValidURL(text) {
                                foundURL = text
                            }
                        }
                        group.leave()
                    }
                }
            }
        }

        group.notify(queue: .main) {
            completion(foundURL, foundTitle)
        }
    }

    // MARK: - Completion Handlers

    private func completeRequest() {
        extensionContext?.completeRequest(returningItems: nil)
    }

    private func cancelRequest() {
        extensionContext?.cancelRequest(withError: NSError(
            domain: "com.clipjot.share",
            code: 0,
            userInfo: [NSLocalizedDescriptionKey: "User cancelled"]
        ))
    }

    private func showError(_ message: String) {
        let alert = UIAlertController(
            title: "Error",
            message: message,
            preferredStyle: .alert
        )
        alert.addAction(UIAlertAction(title: "OK", style: .default) { [weak self] _ in
            self?.cancelRequest()
        })
        present(alert, animated: true)
    }
}

// MARK: - URL Validator (duplicated for Share Extension)
// Note: Share Extension is a separate target and cannot access main app code directly.
// In a real project, you would create a shared framework for common code.

private struct URLValidator {
    private static let urlPattern = try! NSRegularExpression(
        pattern: #"https?://[^\s<>\"\']+"#,
        options: [.caseInsensitive]
    )

    static func extractURL(from text: String) -> String? {
        let range = NSRange(text.startIndex..., in: text)
        guard let match = urlPattern.firstMatch(in: text, options: [], range: range),
              let matchRange = Range(match.range, in: text)
        else {
            return nil
        }
        return String(text[matchRange])
    }

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
}
