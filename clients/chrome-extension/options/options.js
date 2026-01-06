/**
 * LinkJot Chrome Extension - Options Page Script
 */

const DEFAULT_BACKEND_URL = 'http://localhost:5001';

// DOM Elements
const backendUrlInput = document.getElementById('backend-url');
const loggedOutEl = document.getElementById('logged-out');
const loggedInEl = document.getElementById('logged-in');
const logoutBtn = document.getElementById('logout-btn');
const saveBtn = document.getElementById('save-btn');
const statusMessage = document.getElementById('status-message');

/**
 * Initialize the options page
 */
async function init() {
  // Load current settings
  const storage = await chrome.storage.local.get(['backendUrl', 'sessionToken']);

  backendUrlInput.value = storage.backendUrl || DEFAULT_BACKEND_URL;

  // Update login status
  updateLoginStatus(!!storage.sessionToken);
}

/**
 * Update the login status display
 */
function updateLoginStatus(isLoggedIn) {
  if (isLoggedIn) {
    loggedInEl.classList.remove('hidden');
    loggedOutEl.classList.add('hidden');
  } else {
    loggedInEl.classList.add('hidden');
    loggedOutEl.classList.remove('hidden');
  }
}

/**
 * Save settings
 */
async function saveSettings() {
  const backendUrl = backendUrlInput.value.trim() || DEFAULT_BACKEND_URL;

  // Validate URL
  try {
    new URL(backendUrl);
  } catch {
    showStatus('Invalid URL format', 'error');
    return;
  }

  // Remove trailing slash
  const normalizedUrl = backendUrl.replace(/\/+$/, '');

  await chrome.storage.local.set({ backendUrl: normalizedUrl });

  showStatus('Settings saved!', 'success');
}

/**
 * Log out the user
 */
async function logout() {
  await chrome.storage.local.remove('sessionToken');
  updateLoginStatus(false);
  showStatus('Logged out successfully', 'info');
}

/**
 * Show status message
 */
function showStatus(message, type = 'info') {
  statusMessage.textContent = message;
  statusMessage.className = 'alert mt-4';

  switch (type) {
    case 'success':
      statusMessage.classList.add('alert-success');
      break;
    case 'error':
      statusMessage.classList.add('alert-error');
      break;
    case 'warning':
      statusMessage.classList.add('alert-warning');
      break;
    default:
      statusMessage.classList.add('alert-info');
  }

  statusMessage.classList.remove('hidden');

  // Hide after 3 seconds
  setTimeout(() => {
    statusMessage.classList.add('hidden');
  }, 3000);
}

// Event Listeners
saveBtn.addEventListener('click', saveSettings);
logoutBtn.addEventListener('click', logout);

// Save on Enter key in URL input
backendUrlInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    saveSettings();
  }
});

// Initialize
init();
