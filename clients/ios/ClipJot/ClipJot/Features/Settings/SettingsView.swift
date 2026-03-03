import SwiftUI

/// Settings screen for backend URL configuration and account management.
/// Equivalent to Android's SettingsActivity.
struct SettingsView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var authManager = AuthManager.shared

    @State private var backendUrl: String = ""
    @State private var quickSaveEnabled: Bool = false
    @State private var isTestingConnection = false
    @State private var connectionStatus: ConnectionStatus?
    @State private var profile: UserProfileResponse?
    @State private var profileError: String?
    @State private var isLoadingProfile = false
    @State private var showAdvanced = false

    // Brand color
    private let primaryColor = AppTheme.primary

    enum ConnectionStatus {
        case success
        case failure(String)
    }

    var body: some View {
        NavigationStack {
            Form {
                // Quick Save Section
                Section {
                    Toggle("Quick Save Mode", isOn: $quickSaveEnabled)
                } footer: {
                    Text("When enabled, links shared from other apps will be saved immediately without showing the edit form")
                }

                // Account Section
                if TokenManager.shared.isLoggedIn {
                    Section("Account") {
                        if isLoadingProfile {
                            HStack {
                                Text("Loading profile...")
                                    .foregroundColor(.secondary)
                                Spacer()
                                ProgressView()
                            }
                        }

                        // Email — show from profile or cached value
                        if let email = profile?.email ?? SettingsManager.shared.userEmail {
                            HStack {
                                Text("Email")
                                Spacer()
                                Text(email)
                                    .foregroundColor(.secondary)
                            }
                        }

                        // Profile details (from API)
                        if let profile = profile {
                            if let provider = profile.provider {
                                HStack {
                                    Text("Sign-in")
                                    Spacer()
                                    Text(provider.capitalized)
                                        .foregroundColor(.secondary)
                                }
                            }
                            HStack {
                                Text("Account type")
                                Spacer()
                                Text(profile.isPremium ? "Premium" : "Free")
                                    .foregroundColor(.secondary)
                            }
                            HStack {
                                Text("Member since")
                                Spacer()
                                Text(String(profile.createdAt.prefix(10)))
                                    .foregroundColor(.secondary)
                            }
                        }

                        if let error = profileError {
                            Text(error)
                                .font(.caption)
                                .foregroundColor(.red)
                        }

                        Button(role: .destructive) {
                            Task {
                                await authManager.logout()
                                dismiss()
                            }
                        } label: {
                            HStack {
                                Spacer()
                                Label("Sign Out", systemImage: "rectangle.portrait.and.arrow.right")
                                Spacer()
                            }
                        }
                    }
                } else {
                    Section("Account") {
                        Text("Not signed in")
                            .foregroundColor(.secondary)

                        Button {
                            authManager.startOAuth(provider: .google)
                        } label: {
                            HStack {
                                Image(systemName: "g.circle.fill")
                                Text("Sign in with Google")
                            }
                        }

                        Button {
                            authManager.startOAuth(provider: .github)
                        } label: {
                            HStack {
                                Image(systemName: "chevron.left.forwardslash.chevron.right")
                                Text("Sign in with GitHub")
                            }
                        }
                    }
                }

                // About Section
                Section("About") {
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                }

                // Advanced Section
                Section {
                    Button {
                        withAnimation {
                            showAdvanced.toggle()
                        }
                    } label: {
                        HStack {
                            Text("Advanced")
                                .foregroundColor(.primary)
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.caption)
                                .foregroundColor(.secondary)
                                .rotationEffect(.degrees(showAdvanced ? 90 : 0))
                        }
                    }
                }

                if showAdvanced {
                    // Backend URL Section
                    Section {
                        TextField("Backend URL", text: $backendUrl)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            .keyboardType(.URL)

                        Button {
                            Task {
                                await testConnection()
                            }
                        } label: {
                            HStack {
                                Text("Test Connection")
                                Spacer()
                                if isTestingConnection {
                                    ProgressView()
                                } else if let status = connectionStatus {
                                    switch status {
                                    case .success:
                                        Image(systemName: "checkmark.circle.fill")
                                            .foregroundColor(.green)
                                    case .failure:
                                        Image(systemName: "xmark.circle.fill")
                                            .foregroundColor(.red)
                                    }
                                }
                            }
                        }
                        .disabled(backendUrl.isEmpty || isTestingConnection)

                        Button("Reset to Default") {
                            backendUrl = "https://clipjot.net"
                            connectionStatus = nil
                        }
                        .foregroundColor(.secondary)
                    } header: {
                        Text("Server")
                    } footer: {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("The URL of your ClipJot server")

                            if !backendUrl.isEmpty && !URLValidator.isHTTPS(backendUrl) {
                                Text("Warning: Non-HTTPS connections are not secure")
                                    .foregroundColor(.orange)
                            }

                            if case .failure(let message) = connectionStatus {
                                Text(message)
                                    .foregroundColor(.red)
                            }
                        }
                    }
                }
            }
            .presentationDetents([.medium, .large])
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        saveSettings()
                        dismiss()
                    }
                }
            }
            .onAppear {
                loadSettings()
            }
            .task {
                await loadProfile()
            }
        }
    }

    // MARK: - Actions

    private func loadSettings() {
        backendUrl = SettingsManager.shared.backendUrl
        quickSaveEnabled = SettingsManager.shared.quickSaveEnabled
    }

    private func saveSettings() {
        SettingsManager.shared.backendUrl = backendUrl
        SettingsManager.shared.quickSaveEnabled = quickSaveEnabled
    }

    private func loadProfile() async {
        guard TokenManager.shared.isLoggedIn else { return }
        isLoadingProfile = true
        profileError = nil
        do {
            profile = try await APIClient.shared.getUserProfile()
        } catch {
            profileError = "Profile load failed: \(error.localizedDescription)"
            print("Failed to load profile: \(error)")
        }
        isLoadingProfile = false
    }

    private func testConnection() async {
        isTestingConnection = true
        connectionStatus = nil

        // Temporarily save the URL for the API call
        let originalUrl = SettingsManager.shared.backendUrl
        SettingsManager.shared.backendUrl = backendUrl

        do {
            _ = try await APIClient.shared.listTags()
            connectionStatus = .success
        } catch let apiError as APIError {
            connectionStatus = .failure(apiError.localizedDescription)
        } catch {
            connectionStatus = .failure(error.localizedDescription)
        }

        // Restore original URL if test failed
        if case .failure = connectionStatus {
            SettingsManager.shared.backendUrl = originalUrl
        }

        isTestingConnection = false
    }
}

#Preview {
    SettingsView()
}
