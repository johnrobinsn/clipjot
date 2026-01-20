import Foundation
import AuthenticationServices

/// Authentication provider types
enum AuthProvider: String {
    case google
    case github
}

/// Manages OAuth authentication flow.
/// Equivalent to Android's LoginActivity OAuth handling.
@MainActor
final class AuthManager: NSObject, ObservableObject {
    static let shared = AuthManager()

    @Published var isAuthenticating = false
    @Published var authError: String?
    @Published var isLoggedIn: Bool = TokenManager.shared.isLoggedIn

    private var authSession: ASWebAuthenticationSession?
    private var presentationAnchor: ASPresentationAnchor?

    private let callbackScheme = "clipjot"

    private override init() {
        super.init()
    }

    /// Set the presentation anchor (window) for the auth session
    func setPresentationAnchor(_ anchor: ASPresentationAnchor) {
        self.presentationAnchor = anchor
    }

    /// Start OAuth authentication with the specified provider
    /// - Parameter provider: The OAuth provider (Google or GitHub)
    func startOAuth(provider: AuthProvider) {
        guard !isAuthenticating else { return }

        isAuthenticating = true
        authError = nil

        let backendUrl = SettingsManager.shared.backendUrl
        let redirectUri = "\(callbackScheme)://oauth/callback"

        guard let authURL = URL(string: "\(backendUrl)/auth/\(provider.rawValue)?redirect_uri=\(redirectUri)") else {
            authError = "Invalid authentication URL"
            isAuthenticating = false
            return
        }

        authSession = ASWebAuthenticationSession(
            url: authURL,
            callbackURLScheme: callbackScheme
        ) { [weak self] callbackURL, error in
            Task { @MainActor in
                self?.handleAuthCallback(callbackURL: callbackURL, error: error)
            }
        }

        authSession?.presentationContextProvider = self
        authSession?.prefersEphemeralWebBrowserSession = false

        if !authSession!.start() {
            authError = "Failed to start authentication"
            isAuthenticating = false
        }
    }

    /// Handle the OAuth callback
    private func handleAuthCallback(callbackURL: URL?, error: Error?) {
        isAuthenticating = false

        if let error = error as? ASWebAuthenticationSessionError {
            // User cancelled - not an error
            if error.code == .canceledLogin {
                return
            }
            authError = error.localizedDescription
            return
        }

        guard let callbackURL = callbackURL else {
            authError = "No callback received"
            return
        }

        // Extract token from callback URL
        // Expected format: clipjot://oauth/callback?token=xxx
        guard let components = URLComponents(url: callbackURL, resolvingAgainstBaseURL: false),
              let token = components.queryItems?.first(where: { $0.name == "token" })?.value,
              !token.isEmpty
        else {
            authError = "Invalid authentication response"
            return
        }

        // Save token
        do {
            try TokenManager.shared.saveToken(token)
            isLoggedIn = true
        } catch {
            authError = "Failed to save session: \(error.localizedDescription)"
            return
        }

        // Optionally extract user email if provided
        if let email = components.queryItems?.first(where: { $0.name == "email" })?.value {
            SettingsManager.shared.userEmail = email
        }
    }

    /// Handle deep link URL (called from app's onOpenURL)
    /// Returns true if the URL was handled
    func handleDeepLink(_ url: URL) -> Bool {
        guard url.scheme == callbackScheme,
              url.host == "oauth",
              url.path == "/callback"
        else {
            return false
        }

        handleAuthCallback(callbackURL: url, error: nil)
        return true
    }

    /// Logout the current user
    func logout() async {
        // Try to invalidate session on server
        do {
            _ = try await APIClient.shared.logout()
        } catch {
            // Continue with local logout even if server call fails
            print("Server logout failed: \(error)")
        }

        // Clear local data
        TokenManager.shared.clearToken()
        SettingsManager.shared.clearUserData()
        isLoggedIn = false
    }

    /// Clear any authentication error
    func clearError() {
        authError = nil
    }
}

// MARK: - ASWebAuthenticationPresentationContextProviding

extension AuthManager: ASWebAuthenticationPresentationContextProviding {
    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        // Return the saved anchor, or try to find the key window
        if let anchor = presentationAnchor {
            return anchor
        }

        // Fallback: find the key window
        let scenes = UIApplication.shared.connectedScenes
        let windowScene = scenes.first as? UIWindowScene
        return windowScene?.windows.first { $0.isKeyWindow } ?? UIWindow()
    }
}
