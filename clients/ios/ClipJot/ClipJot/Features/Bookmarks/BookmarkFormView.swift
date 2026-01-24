import SwiftUI

/// Form mode: add new bookmark or edit existing
enum BookmarkFormMode: Identifiable {
    case add
    case edit(Bookmark)

    var id: String {
        switch self {
        case .add: return "add"
        case .edit(let bookmark): return "edit-\(bookmark.id)"
        }
    }

    var isEdit: Bool {
        if case .edit = self { return true }
        return false
    }

    var bookmark: Bookmark? {
        if case .edit(let bookmark) = self { return bookmark }
        return nil
    }
}

/// Bookmark creation/editing form.
/// Equivalent to Android's BookmarkBottomSheet and EditBookmarkBottomSheet.
struct BookmarkFormView: View {
    let mode: BookmarkFormMode
    let onSave: () async -> Void

    @Environment(\.dismiss) private var dismiss

    @State private var url: String = ""
    @State private var title: String = ""
    @State private var comment: String = ""
    @State private var tags: [String] = []
    @State private var availableTags: [Tag] = []

    @State private var isLoading = false
    @State private var isSaving = false
    @State private var error: String?
    @State private var showDeleteConfirmation = false

    // Brand color
    private let primaryColor = Color(red: 99/255, green: 102/255, blue: 241/255) // #6366f1

    var body: some View {
        NavigationStack {
            Form {
                // URL Section
                Section {
                    if mode.isEdit {
                        // URL is read-only in edit mode
                        Text(url)
                            .foregroundColor(.secondary)
                    } else {
                        TextField("URL", text: $url)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            .keyboardType(.URL)
                    }
                } header: {
                    Text("URL")
                } footer: {
                    if !mode.isEdit && !url.isEmpty && !URLValidator.isValidURL(url) {
                        Text("Please enter a valid URL")
                            .foregroundColor(.red)
                    }
                }

                // Title Section
                Section("Title") {
                    TextField("Title (optional)", text: $title)
                }

                // Comment Section
                Section("Notes") {
                    TextField("Add a note (optional)", text: $comment, axis: .vertical)
                        .lineLimit(3...6)
                }

                // Tags Section
                Section("Tags") {
                    TagInputView(
                        selectedTags: $tags,
                        availableTags: availableTags
                    )
                }

                // Delete button (edit mode only)
                if mode.isEdit {
                    Section {
                        Button(role: .destructive) {
                            showDeleteConfirmation = true
                        } label: {
                            HStack {
                                Spacer()
                                Label("Delete Bookmark", systemImage: "trash")
                                Spacer()
                            }
                        }
                    }
                }
            }
            .navigationTitle(mode.isEdit ? "Edit Bookmark" : "Add Bookmark")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        Task {
                            await save()
                        }
                    }
                    .disabled(!canSave || isSaving)
                }
            }
            .overlay {
                if isLoading || isSaving {
                    Color.black.opacity(0.2)
                        .ignoresSafeArea()
                    ProgressView()
                }
            }
            .alert("Error", isPresented: .init(
                get: { error != nil },
                set: { if !$0 { error = nil } }
            )) {
                Button("OK") { error = nil }
            } message: {
                if let error = error {
                    Text(error)
                }
            }
            .alert("Delete Bookmark", isPresented: $showDeleteConfirmation) {
                Button("Cancel", role: .cancel) {}
                Button("Delete", role: .destructive) {
                    Task {
                        await delete()
                    }
                }
            } message: {
                Text("Are you sure you want to delete this bookmark?")
            }
        }
        .interactiveDismissDisabled(isSaving)
        .task {
            await loadData()
        }
    }

    // MARK: - Computed Properties

    private var canSave: Bool {
        !url.isEmpty && URLValidator.isValidURL(url)
    }

    // MARK: - Actions

    private func loadData() async {
        isLoading = true

        // Load available tags
        do {
            let response = try await APIClient.shared.listTags()
            availableTags = response.tags
        } catch {
            // Non-fatal: continue without tag suggestions
            print("Failed to load tags: \(error)")
        }

        // Populate form for edit mode
        if let bookmark = mode.bookmark {
            url = bookmark.url
            title = bookmark.title ?? ""
            comment = bookmark.comment ?? ""
            tags = bookmark.tags
        }

        isLoading = false
    }

    private func save() async {
        guard canSave else { return }

        isSaving = true
        error = nil

        do {
            if let existingBookmark = mode.bookmark {
                // Edit existing
                let request = BookmarkEditRequest(
                    id: existingBookmark.id,
                    url: url,
                    title: title.isEmpty ? nil : title,
                    comment: comment.isEmpty ? nil : comment,
                    tags: tags
                )
                _ = try await APIClient.shared.editBookmark(request)
            } else {
                // Add new
                let request = BookmarkAddRequest(
                    url: url,
                    title: title.isEmpty ? nil : title,
                    comment: comment.isEmpty ? nil : comment,
                    tags: tags
                )
                _ = try await APIClient.shared.addBookmark(request)
            }

            await onSave()
            dismiss()
        } catch let apiError as APIError {
            error = apiError.localizedDescription
        } catch {
            self.error = error.localizedDescription
        }

        isSaving = false
    }

    private func delete() async {
        guard let bookmark = mode.bookmark else { return }

        isSaving = true
        error = nil

        do {
            _ = try await APIClient.shared.deleteBookmark(id: bookmark.id)
            await onSave()
            dismiss()
        } catch let apiError as APIError {
            error = apiError.localizedDescription
        } catch {
            self.error = error.localizedDescription
        }

        isSaving = false
    }
}

#Preview("Add") {
    BookmarkFormView(mode: .add) {}
}

#Preview("Edit") {
    BookmarkFormView(
        mode: .edit(Bookmark(
            id: 1,
            url: "https://example.com",
            title: "Example",
            comment: "A note",
            tags: ["test"],
            clientName: "ios",
            createdAt: "2024-01-15",
            updatedAt: nil
        ))
    ) {}
}
