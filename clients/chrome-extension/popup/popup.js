/**
 * ClipJot Chrome Extension - Popup Script
 */

// Default backend URL
const DEFAULT_BACKEND_URL = 'http://localhost:5001';

// State
let backendUrl = DEFAULT_BACKEND_URL;
let sessionToken = null;
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
const formError = document.getElementById('form-error');
const formSuccess = document.getElementById('form-success');
const loginError = document.getElementById('login-error');

/**
 * Initialize the popup
 */
async function init() {
  // Load settings and session
  const storage = await chrome.storage.local.get(['backendUrl', 'sessionToken']);
  backendUrl = storage.backendUrl || DEFAULT_BACKEND_URL;
  sessionToken = storage.sessionToken || null;

  console.log('Init - backendUrl:', backendUrl);
  console.log('Init - sessionToken:', sessionToken ? 'present' : 'missing');

  if (sessionToken) {
    // Verify session is still valid
    console.log('Verifying session...');
    const isValid = await verifySession();
    console.log('Session valid:', isValid);
    if (isValid) {
      await showBookmarkView();
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
      // Reset form after success
      setTimeout(() => {
        selectedTags = [];
        renderSelectedTags();
        commentInput.value = '';
        hideMessages();
      }, 1500);
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

// Event Listeners
loginGoogleBtn.addEventListener('click', () => handleLogin('google'));
loginGithubBtn.addEventListener('click', () => handleLogin('github'));
openOptionsBtn.addEventListener('click', openOptions);
settingsBtn.addEventListener('click', openOptions);
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

// Initialize
init();
