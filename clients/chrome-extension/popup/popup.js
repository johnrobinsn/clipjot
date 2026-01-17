/**
 * ClipJot Chrome Extension - Popup Script
 */

// Default backend URL
const DEFAULT_BACKEND_URL = 'https://clipjot.net';

// State
let backendUrl = DEFAULT_BACKEND_URL;
let sessionToken = null;
let quickSave = false;
let userTags = [];
let selectedTags = [];

// DOM Elements
const loadingEl = document.getElementById('loading');
const loginViewEl = document.getElementById('login-view');
const bookmarkViewEl = document.getElementById('bookmark-view');
const loginGoogleBtn = document.getElementById('login-google');
const loginGithubBtn = document.getElementById('login-github');
const openOptionsBtn = document.getElementById('open-options');
const settingsBtn = document.getElementById('settings-btn');
const bookmarkForm = document.getElementById('bookmark-form');
const urlInput = document.getElementById('bookmark-url');
const titleInput = document.getElementById('bookmark-title');
const tagInput = document.getElementById('tag-input');
const tagsContainer = document.getElementById('tags-container');
const tagSuggestions = document.getElementById('tag-suggestions');
const commentInput = document.getElementById('bookmark-comment');
const saveBtn = document.getElementById('save-btn');
const logoutBtn = document.getElementById('logout-btn');
const formError = document.getElementById('form-error');
const formSuccess = document.getElementById('form-success');
const loginError = document.getElementById('login-error');

/**
 * Initialize the popup
 */
async function init() {
  // Load settings and session
  const storage = await chrome.storage.local.get(['backendUrl', 'sessionToken', 'quickSave']);
  backendUrl = storage.backendUrl || DEFAULT_BACKEND_URL;
  sessionToken = storage.sessionToken || null;
  quickSave = storage.quickSave || false;

  console.log('Init - backendUrl:', backendUrl);
  console.log('Init - sessionToken:', sessionToken ? 'present' : 'missing');
  console.log('Init - quickSave:', quickSave);

  if (sessionToken) {
    // Verify session is still valid
    console.log('Verifying session...');
    const isValid = await verifySession();
    console.log('Session valid:', isValid);
    if (isValid) {
      // Check for pending bookmark from context menu
      const pending = await chrome.storage.local.get('pendingBookmark');

      if (quickSave) {
        // Quick save mode - save immediately without showing form
        await performQuickSave(pending.pendingBookmark);
      } else {
        await showBookmarkView();
      }
    } else {
      // Session expired, clear it
      await chrome.storage.local.remove('sessionToken');
      sessionToken = null;
      showLoginView();
    }
  } else {
    showLoginView();
  }
}

/**
 * Verify the session token is still valid
 */
async function verifySession() {
  try {
    console.log('Calling API to verify session...');
    const response = await fetch(`${backendUrl}/api/v1/tags/list`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${sessionToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });
    console.log('Verify response status:', response.status);
    return response.ok;
  } catch (error) {
    console.error('Session verification failed:', error);
    return false;
  }
}

/**
 * Show the login view
 */
function showLoginView() {
  loadingEl.classList.add('hidden');
  loginViewEl.classList.remove('hidden');
  bookmarkViewEl.classList.add('hidden');
}

/**
 * Show the bookmark form view
 */
async function showBookmarkView() {
  loadingEl.classList.add('hidden');
  loginViewEl.classList.add('hidden');
  bookmarkViewEl.classList.remove('hidden');

  // Check for pending bookmark from context menu
  const pending = await chrome.storage.local.get('pendingBookmark');
  if (pending.pendingBookmark) {
    urlInput.value = pending.pendingBookmark.url || '';
    titleInput.value = pending.pendingBookmark.title || '';
    // Clear the pending bookmark
    await chrome.storage.local.remove('pendingBookmark');
  } else {
    // Get current tab info
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      urlInput.value = tab.url || '';
      titleInput.value = tab.title || '';
    }
  }

  // Load user's tags
  await loadTags();
}

/**
 * Perform quick save - save bookmark immediately without showing form
 */
async function performQuickSave(pendingBookmark) {
  // Get URL and title from pending bookmark or current tab
  let url, title;

  if (pendingBookmark) {
    url = pendingBookmark.url || '';
    title = pendingBookmark.title || '';
    // Clear the pending bookmark
    await chrome.storage.local.remove('pendingBookmark');
  } else {
    // Get current tab info
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      url = tab.url || '';
      title = tab.title || '';
    }
  }

  if (!url) {
    // No URL to save, fall back to showing the form
    await showBookmarkView();
    return;
  }

  // Show a quick saving indicator
  loadingEl.innerHTML = '<span class="loading loading-spinner loading-lg"></span><p style="margin-top: 0.5rem; font-size: 0.875rem;">Saving...</p>';

  try {
    const response = await fetch(`${backendUrl}/api/v1/bookmarks/add`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${sessionToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url,
        title: title || undefined,
        client_name: 'chrome-extension',
      }),
    });

    if (response.ok) {
      // Show success with title or URL, then close
      const displayText = title || url;
      const truncated = displayText.length > 45 ? displayText.substring(0, 45) + '...' : displayText;
      const escaped = truncated.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      loadingEl.innerHTML = `
        <div>
          <div class="brand-header" style="margin-bottom: 0.75rem;">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="brand-icon" style="width: 1.5rem; height: 1.5rem;"><path fill-rule="evenodd" d="M6.32 2.577a49.255 49.255 0 0 1 11.36 0c1.497.174 2.57 1.46 2.57 2.93V21a.75.75 0 0 1-1.085.67L12 18.089l-7.165 3.583A.75.75 0 0 1 3.75 21V5.507c0-1.47 1.073-2.756 2.57-2.93Z" clip-rule="evenodd" /></svg>
            <span style="font-size: 1.125rem; font-weight: bold;">ClipJot</span>
          </div>
          <p style="font-size: 1rem; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 1rem;">${escaped}</p>
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width: 2rem; height: 2rem; color: oklch(var(--su));"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <p style="font-size: 1.125rem;">Saved!</p>
          </div>
        </div>`;
      setTimeout(() => window.close(), 1500);
    } else {
      const data = await response.json();
      // On error, fall back to showing the form with the error
      await showBookmarkView();
      showError(data.error || 'Failed to save bookmark');
    }
  } catch (error) {
    console.error('Quick save error:', error);
    // On error, fall back to showing the form
    await showBookmarkView();
    showError('Failed to connect to server');
  }
}

/**
 * Load user's tags from the backend
 */
async function loadTags() {
  try {
    const response = await fetch(`${backendUrl}/api/v1/tags/list`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${sessionToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });

    if (response.ok) {
      const data = await response.json();
      userTags = data.tags || [];
    }
  } catch (error) {
    console.error('Failed to load tags:', error);
  }
}

/**
 * Handle OAuth login
 */
async function handleLogin(provider) {
  // Generate a unique redirect URI for the extension
  const redirectUri = chrome.identity.getRedirectURL('oauth');

  // Build the OAuth URL (use standard auth route with redirect_uri for extension flow)
  const authUrl = `${backendUrl}/auth/${provider}?redirect_uri=${encodeURIComponent(redirectUri)}`;

  try {
    // Use Chrome's identity API to handle the OAuth flow
    console.log('Starting OAuth flow with URL:', authUrl);
    const responseUrl = await chrome.identity.launchWebAuthFlow({
      url: authUrl,
      interactive: true,
    });
    console.log('OAuth response URL:', responseUrl);

    // Parse the response URL to get the token
    const url = new URL(responseUrl);
    const token = url.searchParams.get('token');
    const error = url.searchParams.get('error');
    console.log('Parsed token:', token ? 'present' : 'missing', 'error:', error);

    if (error) {
      showLoginError(`Login failed: ${error}`);
      return;
    }

    if (token) {
      sessionToken = token;
      await chrome.storage.local.set({ sessionToken: token });
      console.log('Token saved successfully');
      // Show success briefly, then close
      loginError.textContent = 'Login successful!';
      loginError.classList.remove('hidden');
      loginError.classList.remove('alert-error');
      loginError.classList.add('alert-success');
      setTimeout(() => window.close(), 1000);
    } else {
      showLoginError(`No token in response. URL: ${responseUrl}`);
    }
  } catch (error) {
    console.error('OAuth error:', error);
    showLoginError(`Login failed: ${error.message}`);
  }
}

/**
 * Render selected tags
 */
function renderSelectedTags() {
  tagsContainer.innerHTML = '';
  selectedTags.forEach((tagName, index) => {
    const chip = document.createElement('span');
    chip.className = 'tag-chip';
    chip.innerHTML = `
      ${tagName}
      <button type="button" data-index="${index}">&times;</button>
    `;
    chip.querySelector('button').addEventListener('click', () => {
      selectedTags.splice(index, 1);
      renderSelectedTags();
    });
    tagsContainer.appendChild(chip);
  });
}

/**
 * Show tag suggestions
 */
function showTagSuggestions(query) {
  const filtered = userTags
    .filter(tag =>
      tag.name.toLowerCase().includes(query.toLowerCase()) &&
      !selectedTags.includes(tag.name)
    )
    .slice(0, 5);

  if (filtered.length === 0 && query.trim()) {
    // Show option to create new tag
    tagSuggestions.innerHTML = `
      <div class="suggestion-item" data-create="${query}">
        Create "${query}"
      </div>
    `;
    tagSuggestions.classList.remove('hidden');
  } else if (filtered.length > 0) {
    tagSuggestions.innerHTML = filtered
      .map(tag => `<div class="suggestion-item" data-name="${tag.name}">${tag.name}</div>`)
      .join('');
    tagSuggestions.classList.remove('hidden');
  } else {
    tagSuggestions.classList.add('hidden');
  }
}

/**
 * Handle tag suggestion click
 */
function handleTagSuggestionClick(e) {
  const item = e.target.closest('.suggestion-item');
  if (!item) return;

  const tagName = item.dataset.name || item.dataset.create;
  if (tagName && !selectedTags.includes(tagName)) {
    selectedTags.push(tagName);
    renderSelectedTags();
  }
  tagInput.value = '';
  tagSuggestions.classList.add('hidden');
}

/**
 * Save the bookmark
 */
async function saveBookmark(e) {
  e.preventDefault();

  const url = urlInput.value.trim();
  const title = titleInput.value.trim();
  const comment = commentInput.value.trim();

  if (!url) {
    showError('URL is required');
    return;
  }

  saveBtn.classList.add('loading');
  saveBtn.disabled = true;
  hideMessages();

  try {
    const response = await fetch(`${backendUrl}/api/v1/bookmarks/add`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${sessionToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url,
        title: title || undefined,
        comment: comment || undefined,
        tags: selectedTags,
        client_name: 'chrome-extension',
      }),
    });

    if (response.ok) {
      showSuccess('Bookmark saved!');
      // Close popup after brief delay to show success message
      setTimeout(() => {
        window.close();
      }, 750);
    } else {
      const data = await response.json();
      showError(data.error || 'Failed to save bookmark');
    }
  } catch (error) {
    console.error('Save error:', error);
    showError('Failed to connect to server');
  } finally {
    saveBtn.classList.remove('loading');
    saveBtn.disabled = false;
  }
}

/**
 * Show error message in bookmark form
 */
function showError(message) {
  formError.textContent = message;
  formError.classList.remove('hidden');
  formSuccess.classList.add('hidden');
}

/**
 * Show error message in login view
 */
function showLoginError(message) {
  loginError.textContent = message;
  loginError.classList.remove('hidden');
}

/**
 * Show success message
 */
function showSuccess(message) {
  formSuccess.textContent = message;
  formSuccess.classList.remove('hidden');
  formError.classList.add('hidden');
}

/**
 * Hide all messages
 */
function hideMessages() {
  formError.classList.add('hidden');
  formSuccess.classList.add('hidden');
}

/**
 * Open options page
 */
function openOptions() {
  chrome.runtime.openOptionsPage();
}

/**
 * Handle logout - revoke session on server then clear local storage
 */
async function handleLogout() {
  logoutBtn.disabled = true;

  try {
    // Call the logout API to revoke the session on the server
    await fetch(`${backendUrl}/api/v1/logout`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${sessionToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });
  } catch (error) {
    // Even if the API call fails, we still want to clear local session
    console.error('Logout API error (continuing with local logout):', error);
  }

  // Clear local session regardless of API result
  await chrome.storage.local.remove('sessionToken');
  sessionToken = null;

  // Reset state
  selectedTags = [];
  userTags = [];

  logoutBtn.disabled = false;
  showLoginView();
}

// Event Listeners
loginGoogleBtn.addEventListener('click', () => handleLogin('google'));
loginGithubBtn.addEventListener('click', () => handleLogin('github'));
openOptionsBtn.addEventListener('click', openOptions);
settingsBtn.addEventListener('click', openOptions);
logoutBtn.addEventListener('click', handleLogout);
bookmarkForm.addEventListener('submit', saveBookmark);

tagInput.addEventListener('input', (e) => {
  const query = e.target.value;
  if (query.length > 0) {
    showTagSuggestions(query);
  } else {
    tagSuggestions.classList.add('hidden');
  }
});

tagInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    const query = tagInput.value.trim();
    if (query && !selectedTags.includes(query)) {
      selectedTags.push(query);
      renderSelectedTags();
      tagInput.value = '';
      tagSuggestions.classList.add('hidden');
    }
  } else if (e.key === 'Escape') {
    tagSuggestions.classList.add('hidden');
  }
});

tagSuggestions.addEventListener('click', handleTagSuggestionClick);

// Close suggestions when clicking outside
document.addEventListener('click', (e) => {
  if (!tagInput.contains(e.target) && !tagSuggestions.contains(e.target)) {
    tagSuggestions.classList.add('hidden');
  }
});

// Listen for storage changes (e.g., token cleared from options page)
chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName === 'local') {
    // If session token was removed, show login view
    if (changes.sessionToken && !changes.sessionToken.newValue) {
      sessionToken = null;
      showLoginView();
    }
    // If backend URL changed, update our local copy
    if (changes.backendUrl && changes.backendUrl.newValue) {
      backendUrl = changes.backendUrl.newValue;
    }
    // If quick save setting changed, update our local copy
    if (changes.quickSave !== undefined) {
      quickSave = changes.quickSave.newValue || false;
    }
  }
});

// Initialize
init();
