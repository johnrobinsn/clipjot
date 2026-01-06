/**
 * ClipJot Chrome Extension - Background Service Worker
 *
 * Handles:
 * - Context menu registration
 * - Context menu click handling
 * - Message passing between popup and background
 */

const DEFAULT_BACKEND_URL = 'http://localhost:5001';

// Create context menu on install
chrome.runtime.onInstalled.addListener(() => {
  // Create context menu for links
  chrome.contextMenus.create({
    id: 'save-link-to-clipjot',
    title: 'Save to ClipJot',
    contexts: ['link'],
  });

  // Create context menu for page
  chrome.contextMenus.create({
    id: 'save-page-to-clipjot',
    title: 'Save page to ClipJot',
    contexts: ['page'],
  });

  // Create context menu for extension icon to open web UI
  chrome.contextMenus.create({
    id: 'open-clipjot-web',
    title: 'View Links...',
    contexts: ['action'],
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  // Handle "View Links..." - open web UI
  if (info.menuItemId === 'open-clipjot-web') {
    const storage = await chrome.storage.local.get(['backendUrl']);
    const backendUrl = storage.backendUrl || DEFAULT_BACKEND_URL;
    chrome.tabs.create({ url: backendUrl });
    return;
  }

  let url, title;

  if (info.menuItemId === 'save-link-to-clipjot') {
    url = info.linkUrl;
    // Try to get link text by injecting a script to find the link element
    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: (linkUrl) => {
          // Find the link element with matching href
          const links = document.querySelectorAll('a[href]');
          for (const link of links) {
            if (link.href === linkUrl) {
              return link.textContent?.trim() || link.title || null;
            }
          }
          return null;
        },
        args: [url],
      });
      title = results[0]?.result || info.linkText || url;
    } catch (e) {
      // Script injection may fail on some pages (chrome://, etc.)
      title = info.linkText || url;
    }
  } else if (info.menuItemId === 'save-page-to-clipjot') {
    url = tab.url;
    title = tab.title;
  }

  if (url) {
    // Store the URL and title for the popup to use
    await chrome.storage.local.set({
      pendingBookmark: { url, title },
    });

    // Open the popup by programmatically clicking the extension icon
    // Note: We can't directly open the popup, so we'll use a workaround
    // The popup will check for pending bookmarks on load
    chrome.action.openPopup().catch(() => {
      // If openPopup fails (not supported in all contexts), try creating a tab
      chrome.tabs.create({
        url: chrome.runtime.getURL('popup/popup.html'),
      });
    });
  }
});

// Handle messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_PENDING_BOOKMARK') {
    chrome.storage.local.get('pendingBookmark', (result) => {
      sendResponse(result.pendingBookmark || null);
      // Clear the pending bookmark
      chrome.storage.local.remove('pendingBookmark');
    });
    return true; // Keep the message channel open for async response
  }

  if (message.type === 'SAVE_BOOKMARK') {
    saveBookmark(message.data).then(sendResponse);
    return true;
  }
});

/**
 * Save a bookmark to the backend
 */
async function saveBookmark(data) {
  try {
    const storage = await chrome.storage.local.get(['backendUrl', 'sessionToken']);
    const backendUrl = storage.backendUrl || DEFAULT_BACKEND_URL;
    const sessionToken = storage.sessionToken;

    if (!sessionToken) {
      return { success: false, error: 'Not logged in' };
    }

    const response = await fetch(`${backendUrl}/api/v1/bookmarks/add`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${sessionToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: data.url,
        title: data.title,
        comment: data.comment,
        tags: data.tags || [],
        client_name: 'chrome-extension',
      }),
    });

    if (response.ok) {
      const result = await response.json();
      return { success: true, bookmark: result };
    } else {
      const error = await response.json();
      return { success: false, error: error.error || 'Failed to save' };
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
}
