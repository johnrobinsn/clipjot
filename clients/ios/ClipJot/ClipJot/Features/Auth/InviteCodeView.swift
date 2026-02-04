import SwiftUI

/// Sheet view for entering an invite code.
/// Minimal UI for App Store reviewers and beta testers.
struct InviteCodeView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var authManager: AuthManager

    @State private var code = ""
    @State private var isSubmitting = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                // Instructions
                Text("Enter your invite code to sign in")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.top)

                // Code input field
                TextField("Invite Code", text: $code)
                    .textFieldStyle(.roundedBorder)
                    .textInputAutocapitalization(.characters)
                    .autocorrectionDisabled()
                    .font(.system(.body, design: .monospaced))
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
                    .onChange(of: code) { _, newValue in
                        // Auto-uppercase and limit to 8 characters
                        let filtered = newValue.uppercased().filter { $0.isLetter || $0.isNumber }
                        if filtered != newValue || filtered.count > 8 {
                            code = String(filtered.prefix(8))
                        }
                    }

                // Error message
                if let error = errorMessage ?? authManager.authError {
                    Text(error)
                        .font(.caption)
                        .foregroundColor(.red)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }

                // Submit button
                Button {
                    submitCode()
                } label: {
                    if isSubmitting {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                            .padding()
                    } else {
                        Text("Sign In")
                            .fontWeight(.medium)
                            .frame(maxWidth: .infinity)
                            .padding()
                    }
                }
                .background(code.count == 8 ? Color.accentColor : Color.gray.opacity(0.3))
                .foregroundColor(.white)
                .cornerRadius(12)
                .disabled(code.count != 8 || isSubmitting)
                .padding(.horizontal)

                Spacer()
            }
            .navigationTitle("Invite Code")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
        }
    }

    private func submitCode() {
        guard code.count == 8, !isSubmitting else { return }

        isSubmitting = true
        errorMessage = nil

        Task {
            do {
                try await authManager.authenticateWithInviteCode(code)
                // Success - AuthManager will update isLoggedIn
                await MainActor.run {
                    dismiss()
                }
            } catch {
                await MainActor.run {
                    isSubmitting = false
                    // Error message is set by AuthManager
                }
            }
        }
    }
}

#Preview {
    InviteCodeView(authManager: AuthManager.shared)
}
