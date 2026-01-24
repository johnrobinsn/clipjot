import SwiftUI
import UniformTypeIdentifiers

/// Single bookmark row in the list.
/// Equivalent to Android's item_bookmark.xml layout.
struct BookmarkRowView: View {
    let bookmark: Bookmark
    let isSelected: Bool
    let onEdit: () -> Void

    // Brand color
    private let primaryColor = Color(red: 99/255, green: 102/255, blue: 241/255) // #6366f1

    @State private var showCopiedFeedback = false

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            // Selection indicator (shown in selection mode)
            if isSelected {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(primaryColor)
                    .font(.title2)
            }

            VStack(alignment: .leading, spacing: 6) {
                // Title
                Text(bookmark.displayTitle)
                    .font(.headline)
                    .lineLimit(2)

                // Domain
                if let domain = bookmark.domain {
                    Text(domain)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                // Comment (if present)
                if let comment = bookmark.comment, !comment.isEmpty {
                    HStack(spacing: 4) {
                        Image(systemName: "square.and.pencil")
                            .font(.caption2)
                        Text(comment)
                            .font(.caption)
                    }
                    .foregroundColor(.secondary)
                    .lineLimit(1)
                }

                // Tags
                if !bookmark.tags.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 6) {
                            ForEach(bookmark.tags, id: \.self) { tag in
                                Text(tag)
                                    .font(.caption2)
                                    .fontWeight(.medium)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(primaryColor)
                                    .foregroundColor(.white)
                                    .cornerRadius(12)
                            }
                        }
                    }
                }
            }

            Spacer()

            // Copy button
            Button {
                copyBookmark()
            } label: {
                Image(systemName: showCopiedFeedback ? "checkmark" : "doc.on.doc")
                    .font(.body)
                    .foregroundColor(showCopiedFeedback ? .green : .secondary)
                    .padding(8)
            }
            .buttonStyle(.plain)

            // Edit button
            Button {
                onEdit()
            } label: {
                Image(systemName: "pencil")
                    .font(.body)
                    .foregroundColor(.secondary)
                    .padding(8)
            }
            .buttonStyle(.plain)
        }
        .padding(.vertical, 8)
        .contentShape(Rectangle()) // Make entire row tappable
    }

    private func copyBookmark() {
        let url = bookmark.url
        let title = bookmark.title ?? url

        // Create HTML link
        let htmlContent = "<a href=\"\(url)\">\(title)</a>"

        // Set multiple representations on pasteboard
        let pasteboard = UIPasteboard.general
        pasteboard.items = [[
            UTType.plainText.identifier: url,
            UTType.html.identifier: htmlContent,
            UTType.url.identifier: URL(string: url) as Any
        ]]

        // Haptic feedback
        let generator = UIImpactFeedbackGenerator(style: .light)
        generator.impactOccurred()

        // Show brief visual feedback
        withAnimation {
            showCopiedFeedback = true
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
            withAnimation {
                showCopiedFeedback = false
            }
        }
    }
}

/// Non-selection mode row (simpler)
struct SimpleBookmarkRowView: View {
    let bookmark: Bookmark
    let onEdit: () -> Void

    var body: some View {
        BookmarkRowView(
            bookmark: bookmark,
            isSelected: false,
            onEdit: onEdit
        )
    }
}

#Preview {
    List {
        BookmarkRowView(
            bookmark: Bookmark(
                id: 1,
                url: "https://example.com/article",
                title: "Example Article Title That Might Be Long",
                comment: "This is a note about the bookmark",
                tags: ["swift", "ios", "development"],
                clientName: "ios",
                createdAt: "2024-01-15",
                updatedAt: nil
            ),
            isSelected: false,
            onEdit: {}
        )

        BookmarkRowView(
            bookmark: Bookmark(
                id: 2,
                url: "https://github.com/repo",
                title: nil,
                comment: nil,
                tags: [],
                clientName: "web",
                createdAt: "2024-01-14",
                updatedAt: nil
            ),
            isSelected: true,
            onEdit: {}
        )
    }
}
