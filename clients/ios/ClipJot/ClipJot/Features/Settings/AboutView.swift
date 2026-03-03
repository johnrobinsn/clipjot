import SwiftUI

struct AboutView: View {
    @Environment(\.dismiss) private var dismiss

    private let primaryColor = AppTheme.primary

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 16) {
                // Header: Logo + Name
                HStack(spacing: 10) {
                    BookmarkLogoShape()
                        .fill(primaryColor)
                        .frame(width: 36, height: 36)
                    Text("ClipJot")
                        .font(.system(size: 28, weight: .bold))
                }

                // Version
                Text("Version \(appVersion)")
                    .font(.subheadline)
                    .foregroundColor(.secondary)

                // Description
                Text("ClipJot is your personal bookmark manager. Save links from any app on your device by using the share button — just look for ClipJot in the share sheet.\n\nOrganize your bookmarks with tags, add notes, and access your collection from anywhere. Whether you're saving articles to read later, collecting recipes, or bookmarking resources for work, ClipJot keeps everything in one place.")
                    .font(.body)
                    .lineSpacing(4)

                // Website link
                Link("clipjot.net", destination: URL(string: "https://clipjot.net")!)
                    .font(.body)
                    .foregroundColor(primaryColor)

                Spacer()
            }
            .padding(24)
            .navigationTitle("About")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }

    private var appVersion: String {
        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0"
    }
}

#Preview {
    AboutView()
}
