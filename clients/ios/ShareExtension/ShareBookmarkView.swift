import SwiftUI

/// SwiftUI view for Share Extension bookmark form.
/// Handles both logged-in (save bookmark) and logged-out (store pending) states.
struct ShareBookmarkView: View {
    let url: String
    let title: String?
    let onComplete: () -> Void
    let onCancel: () -> Void

    @State private var bookmarkTitle: String = ""
    @State private var comment: String = ""
    @State private var tags: [String] = []
    @State private var availableTags: [Tag] = []

    @State private var isLoading = false
    @State private var isSaving = false
    @State private var error: String?
    @State private var saveSuccess = false

    // Check login state
    private var isLoggedIn: Bool {
        TokenManager.shared.isLoggedIn
    }

    // Quick save mode
    private var quickSaveEnabled: Bool {
        SettingsManager.shared.quickSaveEnabled
    }

    // Brand color
    private let primaryColor = Color(red: 99/255, green: 102/255, blue: 241/255) // #6366f1

    var body: some View {
        NavigationStack {
            if !isLoggedIn {
                notLoggedInView
            } else if quickSaveEnabled && !saveSuccess && error == nil {
                quickSaveView
            } else if saveSuccess {
                successView
            } else {
                formView
            }
        }
        .task {
            await initialize()
        }
    }

    // MARK: - Views

    private var formView: some View {
        Form {
            Section("URL") {
                Text(url)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }

            Section("Title") {
                TextField("Title (optional)", text: $bookmarkTitle)
            }

            Section("Notes") {
                TextField("Add a note (optional)", text: $comment, axis: .vertical)
                    .lineLimit(3...6)
            }

            Section("Tags") {
                TagInputView(
                    selectedTags: $tags,
                    availableTags: availableTags
                )
            }

            if let error = error {
                Section {
                    Text(error)
                        .foregroundColor(.red)
                }
            }
        }
        .navigationTitle("Save Bookmark")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button("Cancel") {
                    onCancel()
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
            if isLoading || isSaving {
                Color.black.opacity(0.2)
                    .ignoresSafeArea()
                ProgressView()
            }
        }
    }

    private var quickSaveView: some View {
        VStack(spacing: 20) {
            Spacer()

            ProgressView()
                .scaleEffect(1.5)

            Text("Saving...")
                .font(.headline)

            Text(url)
                .font(.caption)
                .foregroundColor(.secondary)
                .lineLimit(1)
                .padding(.horizontal)

            Spacer()

            Button("Edit") {
                // Disable quick save for this session
                // This will show the form view
            }
            .padding(.bottom, 32)
        }
        .navigationTitle("Save Bookmark")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button("Cancel") {
                    onCancel()
                }
            }
        }
    }

    private var successView: some View {
        VStack(spacing: 20) {
            Spacer()

            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 64))
                .foregroundColor(.green)

            Text("Saved!")
                .font(.headline)

            Spacer()
        }
        .onAppear {
            // Auto-dismiss after delay
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                onComplete()
            }
        }
    }

    private var notLoggedInView: some View {
        VStack(spacing: 20) {
            Spacer()

            Image(systemName: "person.crop.circle.badge.exclamationmark")
                .font(.system(size: 64))
                .foregroundColor(.orange)

            Text("Not Logged In")
                .font(.headline)

            Text("Open the ClipJot app to sign in, then try again.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            Spacer()

            Button("Save for Later") {
                savePendingBookmark()
            }
            .buttonStyle(.borderedProminent)
            .tint(primaryColor)

            Text("The bookmark will be saved when you sign in")
                .font(.caption)
                .foregroundColor(.secondary)

            Spacer()
        }
        .navigationTitle("Save Bookmark")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button("Cancel") {
                    onCancel()
                }
            }
        }
    }

    // MARK: - Actions

    private func initialize() async {
        bookmarkTitle = title ?? ""

        if isLoggedIn {
            // Load available tags
            isLoading = true
            do {
                let response = try await APIClient.shared.listTags()
                availableTags = response.tags
            } catch {
                // Non-fatal: continue without suggestions
            }
            isLoading = false

            // Auto-save if quick save mode
            if quickSaveEnabled {
                await saveBookmark()
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
            saveSuccess = true

            // If not quick save mode, complete after short delay
            if !quickSaveEnabled {
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                    onComplete()
                }
            }
        } catch let apiError as APIError {
            error = apiError.localizedDescription
        } catch {
            self.error = error.localizedDescription
        }

        isSaving = false
    }

    private func savePendingBookmark() {
        SettingsManager.shared.setPendingBookmark(url: url, title: title)
        onComplete()
    }
}

// MARK: - Tag Models (duplicated for Share Extension)
// Note: In a real project, create a shared framework

struct Tag: Identifiable, Codable, Equatable, Hashable {
    let id: Int
    let name: String
}

// MARK: - Simplified TagInputView for Share Extension

struct TagInputView: View {
    @Binding var selectedTags: [String]
    let availableTags: [Tag]

    @State private var inputText = ""

    private let primaryColor = Color(red: 99/255, green: 102/255, blue: 241/255)

    private var suggestions: [Tag] {
        guard !inputText.isEmpty else { return [] }
        let lowercasedInput = inputText.lowercased()
        return availableTags
            .filter { !selectedTags.contains($0.name) && $0.name.lowercased().contains(lowercasedInput) }
            .prefix(5)
            .map { $0 }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Selected tags
            if !selectedTags.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack {
                        ForEach(selectedTags, id: \.self) { tag in
                            HStack(spacing: 4) {
                                Text(tag)
                                Button {
                                    selectedTags.removeAll { $0 == tag }
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
                }
            }

            // Input
            TextField("Add tags...", text: $inputText)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .onSubmit {
                    addTag(inputText)
                }

            // Suggestions
            ForEach(suggestions) { tag in
                Button {
                    addTag(tag.name)
                } label: {
                    Text(tag.name)
                        .foregroundColor(.primary)
                }
            }
        }
    }

    private func addTag(_ tag: String) {
        let trimmed = tag.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty, !selectedTags.contains(trimmed) else { return }
        selectedTags.append(trimmed)
        inputText = ""
    }
}

// MARK: - Shared Code Access
// Note: These reference the shared App Group storage
// In a real project, create a shared framework

class TokenManager {
    static let shared = TokenManager()
    private let service = "com.clipjot.ios"
    private let account = "session_token"
    private let accessGroup = "com.clipjot.shared"

    var isLoggedIn: Bool { getToken() != nil }

    func getToken() -> String? {
        var query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecAttrAccessGroup as String: accessGroup,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let token = String(data: data, encoding: .utf8)
        else { return nil }

        return token
    }
}

class SettingsManager {
    static let shared = SettingsManager()
    private let appGroupIdentifier = "group.com.clipjot.shared"

    private var defaults: UserDefaults {
        UserDefaults(suiteName: appGroupIdentifier) ?? .standard
    }

    var backendUrl: String {
        defaults.string(forKey: "backend_url") ?? "https://clipjot.net"
    }

    var quickSaveEnabled: Bool {
        defaults.bool(forKey: "quick_save_enabled")
    }

    func setPendingBookmark(url: String, title: String?) {
        defaults.set(url, forKey: "pending_bookmark_url")
        defaults.set(title, forKey: "pending_bookmark_title")
    }
}

// MARK: - API Client (simplified for Share Extension)

actor APIClient {
    static let shared = APIClient()

    func addBookmark(_ request: BookmarkAddRequest) async throws -> Bookmark {
        try await post(endpoint: "api/v1/bookmarks/add", body: request)
    }

    func listTags() async throws -> TagsResponse {
        try await post(endpoint: "api/v1/tags/list", body: EmptyBody())
    }

    private func post<T: Decodable, B: Encodable>(endpoint: String, body: B) async throws -> T {
        let baseURL = URL(string: SettingsManager.shared.backendUrl)!
        var request = URLRequest(url: baseURL.appendingPathComponent(endpoint))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = TokenManager.shared.getToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              200..<300 ~= httpResponse.statusCode
        else {
            throw APIError.serverError
        }

        return try JSONDecoder().decode(T.self, from: data)
    }
}

struct EmptyBody: Encodable {}

struct BookmarkAddRequest: Codable {
    let url: String
    let title: String?
    let comment: String?
    let tags: [String]
}

struct Bookmark: Codable {
    let id: Int
    let url: String
}

struct TagsResponse: Codable {
    let tags: [Tag]
}

enum APIError: LocalizedError {
    case serverError
    var errorDescription: String? { "Server error" }
}
