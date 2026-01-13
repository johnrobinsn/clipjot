import SwiftUI

/// Main app entry point.
/// Handles deep link callbacks and app-wide state.
@main
struct ClipJotApp: App {
    @StateObject private var authManager = AuthManager.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authManager)
                .onOpenURL { url in
                    handleDeepLink(url)
                }
                .onAppear {
                    setupAuthManager()
                }
        }
    }

    /// Handle incoming deep links (OAuth callbacks)
    private func handleDeepLink(_ url: URL) {
        // Try to handle as OAuth callback
        if authManager.handleDeepLink(url) {
            return
        }

        // Handle other deep link types if needed
        print("Unhandled deep link: \(url)")
    }

    /// Set up the auth manager with the window anchor
    private func setupAuthManager() {
        // Get the key window for presenting OAuth browser
        DispatchQueue.main.async {
            if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
               let window = windowScene.windows.first {
                authManager.setPresentationAnchor(window)
            }
        }
    }
}

/// Root content view - shows login or main app based on auth state
struct ContentView: View {
    @EnvironmentObject private var authManager: AuthManager
    @State private var showPendingBookmarkForm = false
    @State private var pendingBookmark: (url: String, title: String?)?

    var body: some View {
        Group {
            if TokenManager.shared.isLoggedIn {
                BookmarkListView()
                    .onAppear {
                        checkPendingBookmark()
                    }
                    .sheet(isPresented: $showPendingBookmarkForm) {
                        if let pending = pendingBookmark {
                            PendingBookmarkFormView(
                                url: pending.url,
                                title: pending.title
                            ) {
                                SettingsManager.shared.clearPendingBookmark()
                                pendingBookmark = nil
                            }
                        }
                    }
            } else {
                LoginView()
            }
        }
        // Re-render when auth state changes
        .id(TokenManager.shared.isLoggedIn)
    }

    /// Check for pending bookmark from Share Extension
    private func checkPendingBookmark() {
        if let pending = SettingsManager.shared.getPendingBookmark() {
            pendingBookmark = pending
            showPendingBookmarkForm = true
        }
    }
}

/// Form for saving a pending bookmark (shared while logged out)
struct PendingBookmarkFormView: View {
    let url: String
    let title: String?
    let onComplete: () -> Void

    @Environment(\.dismiss) private var dismiss

    @State private var bookmarkTitle: String = ""
    @State private var comment: String = ""
    @State private var tags: [String] = []
    @State private var availableTags: [Tag] = []
    @State private var isSaving = false
    @State private var error: String?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Text("You shared this link while logged out. Would you like to save it now?")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }

                Section("URL") {
                    Text(url)
                        .foregroundColor(.secondary)
                }

                Section("Title") {
                    TextField("Title (optional)", text: $bookmarkTitle)
                }

                Section("Notes") {
                    TextField("Add a note (optional)", text: $comment, axis: .vertical)
                        .lineLimit(3...6)
                }

                if let error = error {
                    Section {
                        Text(error)
                            .foregroundColor(.red)
                    }
                }
            }
            .navigationTitle("Save Pending Bookmark")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Discard") {
                        onComplete()
                        dismiss()
                    }
                }

                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        Task {
                            await saveBookmark()
                        }
                    }
                    .disabled(isSaving)
                }
            }
            .overlay {
                if isSaving {
                    ProgressView()
                }
            }
        }
        .onAppear {
            bookmarkTitle = title ?? ""
        }
        .task {
            // Load available tags
            do {
                let response = try await APIClient.shared.listTags()
                availableTags = response.tags
            } catch {
                // Non-fatal
            }
        }
    }

    private func saveBookmark() async {
        isSaving = true
        error = nil

        do {
            let request = BookmarkAddRequest(
                url: url,
                title: bookmarkTitle.isEmpty ? nil : bookmarkTitle,
                comment: comment.isEmpty ? nil : comment,
                tags: tags
            )
            _ = try await APIClient.shared.addBookmark(request)
            onComplete()
            dismiss()
        } catch let apiError as APIError {
            error = apiError.localizedDescription
        } catch {
            self.error = error.localizedDescription
        }

        isSaving = false
    }
}

#Preview {
    ContentView()
        .environmentObject(AuthManager.shared)
}
