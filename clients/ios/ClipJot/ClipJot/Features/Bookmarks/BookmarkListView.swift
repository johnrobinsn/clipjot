import SwiftUI

/// Main bookmark list screen with search, infinite scroll, and selection mode.
/// Equivalent to Android's MyLinksActivity.
struct BookmarkListView: View {
    @StateObject private var viewModel = BookmarkListViewModel()
    @State private var selectedBookmarks: Set<Bookmark> = []
    @State private var isSelectionMode = false
    @State private var showSettings = false
    @State private var showAddBookmark = false
    @State private var editingBookmark: Bookmark?
    @State private var showDeleteConfirmation = false
    @State private var showAbout = false
    @State private var lastClickedBookmarkId: Int? = nil
    @Environment(\.scenePhase) private var scenePhase

    // Brand color
    private let primaryColor = AppTheme.primary

    var body: some View {
        NavigationStack {
            ScrollViewReader { scrollProxy in
                ZStack {
                    // Main list
                    listContent(scrollProxy: scrollProxy)

                    // New links banner
                    if viewModel.hasNewLinks {
                        newLinksBanner
                    }

                    // Loading overlay for initial load
                    if viewModel.isLoading && viewModel.bookmarks.isEmpty {
                        ProgressView()
                    }
                }
                .onChange(of: scenePhase) { _, newPhase in
                    if newPhase == .active {
                        // Scroll to last clicked item when returning from browser
                        if let bookmarkId = lastClickedBookmarkId {
                            withAnimation {
                                scrollProxy.scrollTo(bookmarkId, anchor: .center)
                            }
                        }
                        Task {
                            await viewModel.silentRefresh()
                        }
                    }
                }
            }
            .navigationTitle("")
            .navigationBarTitleDisplayMode(.inline)
            .navigationBarBackButtonHidden(true)
            .searchable(
                text: $viewModel.searchQuery,
                placement: .navigationBarDrawer(displayMode: .always),
                prompt: "Search bookmarks"
            )
            .refreshable {
                await viewModel.refresh()
            }
            .toolbar {
                toolbarContent
            }
            .sheet(isPresented: $showSettings) {
                SettingsView()
            }
            .sheet(isPresented: $showAbout) {
                AboutView()
            }
            .sheet(isPresented: $showAddBookmark) {
                BookmarkFormView(mode: .add) {
                    await viewModel.refresh()
                }
            }
            .sheet(item: $editingBookmark) { bookmark in
                BookmarkFormView(mode: .edit(bookmark)) {
                    await viewModel.refresh()
                }
            }
            .alert("Delete Bookmarks", isPresented: $showDeleteConfirmation) {
                Button("Cancel", role: .cancel) {}
                Button("Delete", role: .destructive) {
                    Task {
                        await viewModel.deleteBookmarks(selectedBookmarks)
                        selectedBookmarks.removeAll()
                        isSelectionMode = false
                    }
                }
            } message: {
                Text("Are you sure you want to delete \(selectedBookmarks.count) bookmark(s)?")
            }
            .sheet(isPresented: .init(
                get: { viewModel.error != nil },
                set: { if !$0 { viewModel.clearError() } }
            )) {
                if let error = viewModel.error {
                    NavigationStack {
                        ScrollView {
                            Text(error)
                                .font(.system(.body, design: .monospaced))
                                .textSelection(.enabled)
                                .padding()
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                        .navigationTitle("Error")
                        .navigationBarTitleDisplayMode(.inline)
                        .toolbar {
                            ToolbarItem(placement: .cancellationAction) {
                                Button("Dismiss") { viewModel.clearError() }
                            }
                            ToolbarItem(placement: .confirmationAction) {
                                Button("Copy") {
                                    UIPasteboard.general.string = error
                                }
                            }
                        }
                    }
                    .presentationDetents([.medium])
                }
            }
        }
        .task {
            await viewModel.loadBookmarks()
        }
    }

    // MARK: - Subviews

    @ViewBuilder
    private func listContent(scrollProxy: ScrollViewProxy) -> some View {
        List(selection: isSelectionMode ? $selectedBookmarks : nil) {
            if viewModel.bookmarks.isEmpty && !viewModel.isLoading {
                // Empty state inside the List so pull-to-refresh works
                VStack(spacing: 16) {
                    Image(systemName: "bookmark")
                        .font(.system(size: 48))
                        .foregroundColor(.secondary)

                    if viewModel.searchQuery.isEmpty {
                        Text("No bookmarks yet")
                            .font(.headline)
                        Text("Tap + to add your first bookmark")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    } else {
                        Text("No results found")
                            .font(.headline)
                        Text("Try a different search term")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 80)
                .listRowSeparator(.hidden)
            } else {
                ForEach(viewModel.bookmarks) { bookmark in
                    BookmarkRowView(
                        bookmark: bookmark,
                        isSelected: selectedBookmarks.contains(bookmark),
                        isLastClicked: bookmark.id == lastClickedBookmarkId,
                        onEdit: { editingBookmark = bookmark }
                    )
                    .id(bookmark.id)
                    .onTapGesture {
                        if isSelectionMode {
                            toggleSelection(bookmark)
                        } else {
                            lastClickedBookmarkId = bookmark.id
                            openURL(bookmark.url)
                        }
                    }
                    .onLongPressGesture {
                        if !isSelectionMode {
                            isSelectionMode = true
                            selectedBookmarks.insert(bookmark)
                        }
                    }
                    .onAppear {
                        // Infinite scroll: load more when near end
                        if bookmark == viewModel.bookmarks.last {
                            Task {
                                await viewModel.loadMore()
                            }
                        }
                    }
                }

                // Loading more indicator
                if viewModel.isLoadingMore {
                    HStack {
                        Spacer()
                        ProgressView()
                        Spacer()
                    }
                    .listRowSeparator(.hidden)
                }
            }
        }
        .listStyle(.plain)
        .environment(\.editMode, .constant(isSelectionMode ? .active : .inactive))
    }

    private var newLinksBanner: some View {
        VStack {
            Button {
                Task {
                    await viewModel.refresh()
                }
            } label: {
                HStack {
                    Image(systemName: "arrow.clockwise")
                    Text("New bookmarks available")
                }
                .font(.subheadline)
                .fontWeight(.medium)
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(primaryColor)
                .foregroundColor(.white)
                .cornerRadius(20)
                .shadow(radius: 4)
            }
            .padding(.top, 8)

            Spacer()
        }
    }

    @ToolbarContentBuilder
    private var toolbarContent: some ToolbarContent {
        ToolbarItem(placement: .topBarLeading) {
            if isSelectionMode {
                Button("Cancel") {
                    isSelectionMode = false
                    selectedBookmarks.removeAll()
                }
            } else {
                HStack(spacing: 8) {
                    BookmarkLogoShape()
                        .fill(primaryColor)
                        .frame(width: 22, height: 22)
                    Text("ClipJot Links")
                        .font(.system(size: 20, weight: .semibold))
                }
                .fixedSize()
                .padding(.horizontal, 8)
            }
        }

        ToolbarItemGroup(placement: .navigationBarTrailing) {
            if isSelectionMode {
                Button {
                    showDeleteConfirmation = true
                } label: {
                    Image(systemName: "trash")
                }
                .disabled(selectedBookmarks.isEmpty)
            } else {
                Button {
                    showAddBookmark = true
                } label: {
                    Image(systemName: "plus")
                }

                Menu {
                    Button {
                        showSettings = true
                    } label: {
                        Label("Settings", systemImage: "gearshape")
                    }

                    Button {
                        showAbout = true
                    } label: {
                        Label("About", systemImage: "info.circle")
                    }

                    Button(role: .destructive) {
                        Task {
                            await AuthManager.shared.logout()
                        }
                    } label: {
                        Label("Sign Out", systemImage: "rectangle.portrait.and.arrow.right")
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                }
            }
        }
    }

    // MARK: - Helpers

    private func toggleSelection(_ bookmark: Bookmark) {
        if selectedBookmarks.contains(bookmark) {
            selectedBookmarks.remove(bookmark)
        } else {
            selectedBookmarks.insert(bookmark)
        }
    }

    private func openURL(_ urlString: String) {
        guard let url = URL(string: urlString) else { return }
        UIApplication.shared.open(url)
    }
}

#Preview {
    BookmarkListView()
}
