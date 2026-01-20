import SwiftUI

/// Login screen with OAuth provider buttons.
/// Equivalent to Android's LoginActivity.
struct LoginView: View {
    @StateObject private var authManager = AuthManager.shared
    @State private var showSettings = false

    // Brand color
    private let primaryColor = Color(red: 99/255, green: 102/255, blue: 241/255) // #6366f1

    var body: some View {
        NavigationStack {
            VStack(spacing: 32) {
                Spacer()

                // Logo and title
                VStack(spacing: 16) {
                    Image(systemName: "bookmark.fill")
                        .font(.system(size: 64))
                        .foregroundColor(primaryColor)

                    Text("ClipJot")
                        .font(.largeTitle)
                        .fontWeight(.bold)

                    Text("Save and organize your bookmarks")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }

                Spacer()

                // OAuth buttons
                VStack(spacing: 16) {
                    // Google Sign In
                    Button {
                        authManager.startOAuth(provider: .google)
                    } label: {
                        HStack(spacing: 12) {
                            GoogleIcon(size: 20)
                            Text("Continue with Google")
                                .fontWeight(.medium)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color(.systemBackground))
                        .foregroundColor(.primary)
                        .cornerRadius(12)
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(Color(.separator), lineWidth: 1)
                        )
                    }
                    .disabled(authManager.isAuthenticating)

                    // GitHub Sign In
                    Button {
                        authManager.startOAuth(provider: .github)
                    } label: {
                        HStack(spacing: 12) {
                            GitHubIcon(size: 20, color: .primary)
                            Text("Continue with GitHub")
                                .fontWeight(.medium)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color(.systemGray6))
                        .foregroundColor(.primary)
                        .cornerRadius(12)
                    }
                    .disabled(authManager.isAuthenticating)
                }
                .padding(.horizontal, 32)

                // Loading indicator
                if authManager.isAuthenticating {
                    ProgressView()
                        .padding()
                }

                // Error message
                if let error = authManager.authError {
                    Text(error)
                        .font(.caption)
                        .foregroundColor(.red)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }

                Spacer()

                // Settings button (for backend URL configuration)
                Button {
                    showSettings = true
                } label: {
                    HStack {
                        Image(systemName: "gearshape")
                        Text("Settings")
                    }
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                }
                .padding(.bottom, 32)
            }
            .navigationBarHidden(true)
            .sheet(isPresented: $showSettings) {
                SettingsView()
            }
        }
    }
}

#Preview {
    LoginView()
}
