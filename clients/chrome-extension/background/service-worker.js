/**
 * ClipJot Chrome Extension - Background Service Worker
 *
 * Handles:
 * - Context menu registration
 * - Context menu click handling
 * - Message passing between popup and background
 */

const DEFAULT_BACKEND_URL = 'https://clipjot.net';

// Create context menu on install
chrome.runtime.onInstalled.addListener(() => {
  createContextMenus();
});

// Update context menus when storage changes (e.g., login/logout)
chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName === 'local' && changes.sessionToken) {
    updateSignOutMenu(!!changes.sessionToken.newValue);
  }
});

/**
 * Create all context menus
 */
function createContextMenus() {
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

  // Create context menu for extension icon to open settings
  chrome.contextMenus.create({
    id: 'open-clipjot-settings',
    title: 'Settings...',
    contexts: ['action'],
  });

  // Check auth state and add sign out menu if logged in
  chrome.storage.local.get(['sessionToken'], (result) => {
    if (result.sessionToken) {
      createSignOutMenu();
    }
  });
}

/**
 * Create Sign Out menu item
 */
function createSignOutMenu() {
  chrome.contextMenus.create({
    id: 'clipjot-sign-out',
    title: 'Sign Out',
    contexts: ['action'],
  });
}

/**
 * Update Sign Out menu based on auth state
 */
function updateSignOutMenu(isLoggedIn) {
  if (isLoggedIn) {
    // Try to create - will fail silently if already exists
    chrome.contextMenus.create({
      id: 'clipjot-sign-out',
      title: 'Sign Out',
      contexts: ['action'],
    }, () => chrome.runtime.lastError); // Suppress error if already exists
  } else {
    // Remove sign out menu
    chrome.contextMenus.remove('clipjot-sign-out', () => chrome.runtime.lastError);
  }
}

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  // Handle "View Links..." - open web UI
  if (info.menuItemId === 'open-clipjot-web') {
    const storage = await chrome.storage.local.get(['backendUrl']);
    const backendUrl = storage.backendUrl || DEFAULT_BACKEND_URL;
    chrome.tabs.create({ url: backendUrl });
    return;
  }

  // Handle "Settings..." - open options page
  if (info.menuItemId === 'open-clipjot-settings') {
    chrome.runtime.openOptionsPage();
    return;
  }

  // Handle "Sign Out"
  if (info.menuItemId === 'clipjot-sign-out') {
    await handleSignOut();
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

// Handle messages from popup or options page
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

  if (message.type === 'SIGN_OUT') {
    handleSignOut().then(sendResponse);
    return true;
  }

  if (message.type === 'GET_AUTH_STATE') {
    chrome.storage.local.get(['sessionToken'], (result) => {
      sendResponse({ isLoggedIn: !!result.sessionToken });
    });
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

/**
 * Handle sign out - revoke session on server and clear local storage
 */
async function handleSignOut() {
  try {
    const storage = await chrome.storage.local.get(['backendUrl', 'sessionToken']);
    const backendUrl = storage.backendUrl || DEFAULT_BACKEND_URL;
    const sessionToken = storage.sessionToken;

    if (sessionToken) {
      // Try to revoke session on server (don't wait for it)
      fetch(`${backendUrl}/api/v1/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${sessionToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      }).catch(() => {}); // Ignore errors
    }

    // Clear local session
    await chrome.storage.local.remove('sessionToken');

    return { success: true };
  } catch (error) {
    // Still clear local session even if server call fails
    await chrome.storage.local.remove('sessionToken');
    return { success: true };
  }
}
