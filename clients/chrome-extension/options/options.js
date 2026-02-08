/**
 * ClipJot Chrome Extension - Options Page Script
 */

const DEFAULT_BACKEND_URL = 'https://clipjot.net';

// DOM Elements
const backendUrlInput = document.getElementById('backend-url');
const quickSaveToggle = document.getElementById('quick-save');
const shortcutDisplay = document.getElementById('shortcut-display');
const changeShortcutBtn = document.getElementById('change-shortcut');
const saveBtn = document.getElementById('save-btn');
const statusMessage = document.getElementById('status-message');
const accountSection = document.getElementById('account-section');
const profileInfo = document.getElementById('profile-info');
const profileEmail = document.getElementById('profile-email');
const profileType = document.getElementById('profile-type');
const profileSince = document.getElementById('profile-since');
const signOutBtn = document.getElementById('sign-out-btn');

/**
 * Initialize the options page
 */
async function init() {
  // Load current settings
  const storage = await chrome.storage.local.get(['backendUrl', 'quickSave', 'sessionToken']);
  backendUrlInput.value = storage.backendUrl || DEFAULT_BACKEND_URL;
  quickSaveToggle.checked = storage.quickSave || false;

  // Show/hide account section based on auth state
  updateAccountSection(!!storage.sessionToken);

  // Load profile if logged in
  if (storage.sessionToken) {
    await loadProfile(storage.backendUrl || DEFAULT_BACKEND_URL, storage.sessionToken);
  }

  // Load keyboard shortcut
  await loadShortcut();
}

/**
 * Update account section visibility based on auth state
 */
function updateAccountSection(isLoggedIn) {
  accountSection.style.display = isLoggedIn ? 'block' : 'none';
}

/**
 * Load and display user profile information
 */
async function loadProfile(backendUrl, sessionToken) {
  try {
    const response = await fetch(`${backendUrl}/api/v1/user/profile`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${sessionToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });
    if (!response.ok) return;
    const data = await response.json();
    profileEmail.textContent = data.email || '';
    profileType.textContent = data.is_premium ? 'Premium' : 'Free';
    profileSince.textContent = data.created_at ? data.created_at.slice(0, 10) : '';
    profileInfo.style.display = 'block';
  } catch (error) {
    // Silently fail - profile info is non-critical
  }
}

/**
 * Load and display the current keyboard shortcut
 */
async function loadShortcut() {
  try {
    const commands = await chrome.commands.getAll();
    const saveCommand = commands.find(cmd => cmd.name === '_execute_action');
    if (saveCommand && saveCommand.shortcut) {
      shortcutDisplay.textContent = saveCommand.shortcut;
    } else {
      shortcutDisplay.textContent = 'Not set';
    }
  } catch (error) {
    console.error('Failed to load shortcut:', error);
    shortcutDisplay.textContent = 'Unknown';
  }
}

/**
 * Open Chrome's extension shortcuts page
 */
function openShortcutsPage() {
  chrome.tabs.create({ url: 'chrome://extensions/shortcuts' });
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
  await chrome.storage.local.set({
    backendUrl: normalizedUrl,
    quickSave: quickSaveToggle.checked
  });
  await chrome.storage.local.remove('sessionToken');

  saveBtn.disabled = false;
  saveBtn.textContent = 'Save Settings';
  showStatus('Settings saved! Please log in again.', 'success');
}

/**
 * Save quick save setting immediately on toggle (no server test needed)
 */
async function saveQuickSave() {
  await chrome.storage.local.set({ quickSave: quickSaveToggle.checked });
  showStatus(quickSaveToggle.checked ? 'Quick Save enabled' : 'Quick Save disabled', 'success');
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

/**
 * Handle sign out
 */
async function handleSignOut() {
  signOutBtn.disabled = true;
  signOutBtn.textContent = 'Signing out...';

  try {
    await chrome.runtime.sendMessage({ type: 'SIGN_OUT' });
    showStatus('Signed out successfully', 'success');
    updateAccountSection(false);
  } catch (error) {
    showStatus('Failed to sign out', 'error');
  } finally {
    signOutBtn.disabled = false;
    signOutBtn.textContent = 'Sign Out';
  }
}

// Event Listeners
saveBtn.addEventListener('click', saveSettings);
quickSaveToggle.addEventListener('change', saveQuickSave);
changeShortcutBtn.addEventListener('click', openShortcutsPage);
signOutBtn.addEventListener('click', handleSignOut);

// Listen for storage changes to update UI
chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName === 'local' && changes.sessionToken) {
    updateAccountSection(!!changes.sessionToken.newValue);
  }
});

// Refresh shortcut display when returning to this tab
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    loadShortcut();
  }
});

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
