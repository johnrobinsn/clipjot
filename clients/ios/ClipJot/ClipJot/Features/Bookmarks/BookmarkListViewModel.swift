import Foundation
import Combine

/// View model for bookmark list with search, pagination, and refresh.
/// Equivalent to Android's MyLinksActivity logic.
@MainActor
final class BookmarkListViewModel: ObservableObject {
    // MARK: - Published State

    @Published var bookmarks: [Bookmark] = []
    @Published var searchQuery: String = ""
    @Published var isLoading = false
    @Published var isLoadingMore = false
    @Published var error: String?
    @Published var hasMore = true
    @Published var hasNewLinks = false

    // MARK: - Private State

    private var currentPage = 1
    private let pageSize = 30
    private var latestKnownBookmarkId: Int?
    private var searchDebounceTask: Task<Void, Never>?
    private var newLinksPollingTask: Task<Void, Never>?

    // MARK: - Initialization

    init() {
        // Start observing search query changes
        setupSearchDebounce()
    }

    deinit {
        searchDebounceTask?.cancel()
        newLinksPollingTask?.cancel()
    }

    // MARK: - Public Methods

    /// Load initial bookmarks
    func loadBookmarks() async {
        guard !isLoading else { return }

        isLoading = true
        error = nil
        currentPage = 1

        do {
            let request = BookmarkSearchRequest(
                query: searchQuery.isEmpty ? nil : searchQuery,
                page: currentPage,
                pageSize: pageSize
            )
            let response = try await APIClient.shared.searchBookmarks(request)

            bookmarks = response.bookmarks
            hasMore = response.hasMore

            // Track latest bookmark for new links detection
            if searchQuery.isEmpty, let firstBookmark = bookmarks.first {
                latestKnownBookmarkId = firstBookmark.id
            }

            // Start polling for new links (only on first page, no search)
            if searchQuery.isEmpty {
                startNewLinksPolling()
            }
        } catch let apiError as APIError {
            // Ignore cancellation errors (from debounce cancelling previous requests)
            if !apiError.isCancelled {
                error = apiError.localizedDescription
                if apiError.requiresLogout {
                    await handleUnauthorized()
                }
            }
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }

    /// Load more bookmarks (pagination)
    func loadMore() async {
        guard !isLoadingMore, !isLoading, hasMore else { return }

        isLoadingMore = true
        currentPage += 1

        do {
            let request = BookmarkSearchRequest(
                query: searchQuery.isEmpty ? nil : searchQuery,
                page: currentPage,
                pageSize: pageSize
            )
            let response = try await APIClient.shared.searchBookmarks(request)

            bookmarks.append(contentsOf: response.bookmarks)
            hasMore = response.hasMore
        } catch let apiError as APIError {
            // Revert page on error
            currentPage -= 1
            if apiError.requiresLogout {
                await handleUnauthorized()
            }
        } catch {
            currentPage -= 1
        }

        isLoadingMore = false
    }

    /// Refresh bookmarks (pull-to-refresh)
    func refresh() async {
        hasNewLinks = false
        await loadBookmarks()
    }

    /// Delete a bookmark
    func deleteBookmark(_ bookmark: Bookmark) async -> Bool {
        do {
            _ = try await APIClient.shared.deleteBookmark(id: bookmark.id)
            bookmarks.removeAll { $0.id == bookmark.id }
            return true
        } catch let apiError as APIError {
            error = apiError.localizedDescription
            if apiError.requiresLogout {
                await handleUnauthorized()
            }
            return false
        } catch {
            self.error = error.localizedDescription
            return false
        }
    }

    /// Delete multiple bookmarks
    func deleteBookmarks(_ bookmarksToDelete: Set<Bookmark>) async -> Bool {
        var allSuccess = true

        for bookmark in bookmarksToDelete {
            let success = await deleteBookmark(bookmark)
            if !success {
                allSuccess = false
            }
        }

        return allSuccess
    }

    /// Clear error message
    func clearError() {
        error = nil
    }

    // MARK: - Private Methods

    private func setupSearchDebounce() {
        // Observe searchQuery changes with debounce
        $searchQuery
            .removeDuplicates()
            .sink { [weak self] query in
                self?.searchDebounceTask?.cancel()
                self?.searchDebounceTask = Task { [weak self] in
                    // 300ms debounce
                    try? await Task.sleep(nanoseconds: 300_000_000)
                    guard !Task.isCancelled else { return }
                    await self?.loadBookmarks()
                }
            }
            .store(in: &cancellables)
    }

    private var cancellables = Set<AnyCancellable>()

    private func startNewLinksPolling() {
        newLinksPollingTask?.cancel()

        newLinksPollingTask = Task { [weak self] in
            while !Task.isCancelled {
                // Poll every 60 seconds
                try? await Task.sleep(nanoseconds: 60_000_000_000)
                guard !Task.isCancelled else { return }

                await self?.checkForNewLinks()
            }
        }
    }

    private func checkForNewLinks() async {
        // Only check if on first page with no search
        guard searchQuery.isEmpty, let latestKnown = latestKnownBookmarkId else { return }

        do {
            let response = try await APIClient.shared.getLatestBookmarkId()
            if let latestId = response.latestId, latestId > latestKnown {
                hasNewLinks = true
            }
        } catch {
            // Silently ignore polling errors
        }
    }

    private func handleUnauthorized() async {
        TokenManager.shared.clearToken()
        SettingsManager.shared.clearUserData()
    }
}
