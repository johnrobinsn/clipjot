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
            .navigationTitle("ClipJot")
            .navigationBarTitleDisplayMode(.large)
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
            .alert("Error", isPresented: .init(
                get: { viewModel.error != nil },
                set: { if !$0 { viewModel.clearError() } }
            )) {
                Button("OK") { viewModel.clearError() }
            } message: {
                if let error = viewModel.error {
                    Text(error)
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
        if viewModel.bookmarks.isEmpty && !viewModel.isLoading {
            emptyState
        } else {
            List(selection: isSelectionMode ? $selectedBookmarks : nil) {
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
            .listStyle(.plain)
            .environment(\.editMode, .constant(isSelectionMode ? .active : .inactive))
        }
    }

    private var emptyState: some View {
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
        ToolbarItem(placement: .navigationBarLeading) {
            if isSelectionMode {
                Button("Cancel") {
                    isSelectionMode = false
                    selectedBookmarks.removeAll()
                }
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
