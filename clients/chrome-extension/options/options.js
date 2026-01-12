/**
 * ClipJot Chrome Extension - Options Page Script
 */

const DEFAULT_BACKEND_URL = 'https://clipjot.net';

// DOM Elements
const backendUrlInput = document.getElementById('backend-url');
const saveBtn = document.getElementById('save-btn');
const statusMessage = document.getElementById('status-message');

/**
 * Initialize the options page
 */
async function init() {
  // Load current settings
  const storage = await chrome.storage.local.get(['backendUrl']);
  backendUrlInput.value = storage.backendUrl || DEFAULT_BACKEND_URL;
}

/**
 * Save settings
 */
async function saveSettings() {
  const backendUrl = backendUrlInput.value.trim() || DEFAULT_BACKEND_URL;

  // Validate URL format
  try {
    new URL(backendUrl);
  } catch {
    showStatus('Invalid URL format', 'error');
    return;
  }

  // Remove trailing slash
  const normalizedUrl = backendUrl.replace(/\/+$/, '');

  // Test connection to backend by calling the tags API
  // An unauthenticated request should return 401 with ClipJot's error format
  saveBtn.disabled = true;
  saveBtn.textContent = 'Testing...';

  try {
    const response = await fetch(`${normalizedUrl}/api/v1/tags/list`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });

    // We expect either:
    // - 401 with JSON error (unauthenticated but it's ClipJot)
    // - 200 if somehow authenticated
    const data = await response.json();

    // Check for ClipJot's error format (has "code" field) or success (has "tags" field)
    if (!data.code && !data.tags) {
      throw new Error('Server responded but does not appear to be ClipJot');
    }
  } catch (error) {
    saveBtn.disabled = false;
    saveBtn.textContent = 'Save Settings';
    if (error.message.includes('ClipJot')) {
      showStatus(error.message, 'error');
    } else if (error.name === 'TypeError') {
      showStatus('Cannot connect to server - check the URL', 'error');
    } else {
      showStatus(`Connection failed: ${error.message}`, 'error');
    }
    // Don't save URL or clear token on failure - keep old settings
    return;
  }

  // Connection test passed - save URL and clear token to force re-login
  await chrome.storage.local.set({ backendUrl: normalizedUrl });
  await chrome.storage.local.remove('sessionToken');

  saveBtn.disabled = false;
  saveBtn.textContent = 'Save Settings';
  showStatus('Settings saved! Please log in again.', 'success');
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

// Save on Enter key in URL input
backendUrlInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    saveSettings();
  }
});

// Reset to defaults
document.getElementById('reset-defaults').addEventListener('click', async (e) => {
  e.preventDefault();
  backendUrlInput.value = DEFAULT_BACKEND_URL;
  await chrome.storage.local.set({ backendUrl: DEFAULT_BACKEND_URL });
  await chrome.storage.local.remove('sessionToken');
  showStatus('Reset to defaults', 'success');
});

// Initialize
init();
