import SwiftUI

/// Tag input with autocomplete suggestions and chip display.
/// Equivalent to Android's tag input in BookmarkBottomSheet.
struct TagInputView: View {
    @Binding var selectedTags: [String]
    let availableTags: [Tag]

    @State private var inputText = ""
    @FocusState private var isInputFocused: Bool

    // Brand color
    private let primaryColor = Color(red: 99/255, green: 102/255, blue: 241/255) // #6366f1

    /// Filtered suggestions based on input
    private var suggestions: [Tag] {
        guard !inputText.isEmpty else { return [] }

        let lowercasedInput = inputText.lowercased()
        return availableTags
            .filter { tag in
                // Don't suggest already selected tags
                !selectedTags.contains(tag.name) &&
                tag.name.lowercased().contains(lowercasedInput)
            }
            .prefix(5) // Limit suggestions
            .map { $0 }
    }

    /// Check if input is a new tag (not in available tags)
    private var isNewTag: Bool {
        guard !inputText.isEmpty else { return false }
        let lowercasedInput = inputText.lowercased()
        return !availableTags.contains { $0.name.lowercased() == lowercasedInput } &&
               !selectedTags.contains { $0.lowercased() == lowercasedInput }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Selected tags (chips)
            if !selectedTags.isEmpty {
                FlowLayout(spacing: 8) {
                    ForEach(selectedTags, id: \.self) { tag in
                        TagChip(name: tag) {
                            removeTag(tag)
                        }
                    }
                }
            }

            // Input field
            HStack {
                TextField("Add tags...", text: $inputText)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .focused($isInputFocused)
                    .onSubmit {
                        addCurrentInput()
                    }

                // Clear button
                if !inputText.isEmpty {
                    Button {
                        inputText = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.secondary)
                    }
                }
            }
            .padding(12)
            .background(Color(.systemGray6))
            .cornerRadius(8)

            // Suggestions
            if !suggestions.isEmpty || isNewTag {
                VStack(alignment: .leading, spacing: 0) {
                    // Existing tag suggestions
                    ForEach(suggestions) { tag in
                        Button {
                            addTag(tag.name)
                        } label: {
                            HStack {
                                Text(tag.name)
                                Spacer()
                            }
                            .padding(.horizontal, 12)
                            .padding(.vertical, 10)
                        }
                        .foregroundColor(.primary)

                        Divider()
                    }

                    // Create new tag option
                    if isNewTag {
                        Button {
                            addCurrentInput()
                        } label: {
                            HStack {
                                Image(systemName: "plus.circle")
                                    .foregroundColor(primaryColor)
                                Text("Create \"\(inputText)\"")
                                Spacer()
                            }
                            .padding(.horizontal, 12)
                            .padding(.vertical, 10)
                        }
                        .foregroundColor(.primary)
                    }
                }
                .background(Color(.systemBackground))
                .cornerRadius(8)
                .shadow(color: .black.opacity(0.1), radius: 4, y: 2)
            }
        }
    }

    // MARK: - Actions

    private func addTag(_ tag: String) {
        let trimmed = tag.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty,
              !selectedTags.contains(where: { $0.lowercased() == trimmed.lowercased() })
        else { return }

        selectedTags.append(trimmed)
        inputText = ""
    }

    private func addCurrentInput() {
        addTag(inputText)
    }

    private func removeTag(_ tag: String) {
        selectedTags.removeAll { $0 == tag }
    }
}

/// Individual tag chip with remove button
struct TagChip: View {
    let name: String
    let onRemove: () -> Void

    // Brand color
    private let primaryColor = Color(red: 99/255, green: 102/255, blue: 241/255) // #6366f1

    var body: some View {
        HStack(spacing: 4) {
            Text(name)
                .font(.subheadline)

            Button {
                onRemove()
            } label: {
                Image(systemName: "xmark")
                    .font(.caption)
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(primaryColor)
        .foregroundColor(.white)
        .cornerRadius(16)
    }
}

/// Simple flow layout for tags (horizontal wrap)
struct FlowLayout: Layout {
    var spacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = FlowResult(
            in: proposal.replacingUnspecifiedDimensions().width,
            subviews: subviews,
            spacing: spacing
        )
        return result.size
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = FlowResult(
            in: bounds.width,
            subviews: subviews,
            spacing: spacing
        )

        for (index, subview) in subviews.enumerated() {
            subview.place(at: CGPoint(
                x: bounds.minX + result.positions[index].x,
                y: bounds.minY + result.positions[index].y
            ), proposal: .unspecified)
        }
    }

    struct FlowResult {
        var size: CGSize = .zero
        var positions: [CGPoint] = []

        init(in maxWidth: CGFloat, subviews: Subviews, spacing: CGFloat) {
            var currentX: CGFloat = 0
            var currentY: CGFloat = 0
            var lineHeight: CGFloat = 0

            for subview in subviews {
                let size = subview.sizeThatFits(.unspecified)

                if currentX + size.width > maxWidth && currentX > 0 {
                    currentX = 0
                    currentY += lineHeight + spacing
                    lineHeight = 0
                }

                positions.append(CGPoint(x: currentX, y: currentY))
                lineHeight = max(lineHeight, size.height)
                currentX += size.width + spacing
            }

            self.size = CGSize(
                width: maxWidth,
                height: currentY + lineHeight
            )
        }
    }
}

#Preview {
    struct PreviewWrapper: View {
        @State private var tags = ["swift", "ios"]

        var body: some View {
            TagInputView(
                selectedTags: $tags,
                availableTags: [
                    Tag(id: 1, name: "swift"),
                    Tag(id: 2, name: "ios"),
                    Tag(id: 3, name: "development"),
                    Tag(id: 4, name: "tutorial"),
                ]
            )
            .padding()
        }
    }

    return PreviewWrapper()
}
