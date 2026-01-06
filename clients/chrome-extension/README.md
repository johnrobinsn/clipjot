# LinkJot Chrome Extension

A Chrome extension for saving bookmarks to LinkJot.

## Features

- Save current page with one click
- Right-click any link to save it
- Auto-fill URL and title from the page
- Add tags from your existing vocabulary
- Add comments/notes to bookmarks
- Configurable backend URL

## Installation

### Development / Local Testing

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `clients/chrome-extension` directory

### Configuration

1. Click the extension icon in the toolbar
2. Click "Settings" (gear icon)
3. Enter your LinkJot server URL (default: `http://localhost:5001`)
4. Click "Save Settings"

## Usage

### Save Current Page
1. Navigate to any page you want to save
2. Click the LinkJot icon in the toolbar
3. (Optional) Edit the title, add tags, or add a comment
4. Click "Save Bookmark"

### Save a Link
1. Right-click any link on a page
2. Select "Save to LinkJot"
3. The popup will open with the link pre-filled
4. Add tags and comments as desired
5. Click "Save Bookmark"

## Authentication

The extension uses OAuth via your LinkJot server:

1. Click the extension icon
2. Click "Sign in with Google" or "Sign in with GitHub"
3. Complete the OAuth flow in the popup window
4. You'll be redirected back to the extension once authenticated

Your session is stored securely in Chrome's local storage.

## Permissions

The extension requires these permissions:

- `activeTab` - Access the current tab's URL and title
- `contextMenus` - Add "Save to LinkJot" to right-click menu
- `storage` - Store your session and settings
- `host_permissions (*://*/*)` - Communicate with your LinkJot server

## Development

### Structure

```
chrome-extension/
├── manifest.json           # Extension manifest (V3)
├── popup/
│   ├── popup.html          # Popup UI
│   ├── popup.css           # Popup styles
│   └── popup.js            # Popup logic
├── options/
│   ├── options.html        # Options page
│   ├── options.css         # Options styles
│   └── options.js          # Options logic
├── background/
│   └── service-worker.js   # Background script
├── icons/
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── README.md
```

### Backend Requirements

The extension uses the standard OAuth routes with a `redirect_uri` parameter:

- `GET /auth/google?redirect_uri=...` - Initiates Google OAuth for extension
- `GET /auth/github?redirect_uri=...` - Initiates GitHub OAuth for extension

When `redirect_uri` is provided, the backend encodes it in the OAuth state and redirects back to the extension with the session token after authentication.

### Building for Production

For publishing to the Chrome Web Store:

1. Update the version in `manifest.json`
2. Zip the extension directory:
   ```bash
   zip -r linkjot-extension.zip chrome-extension/
   ```
3. Upload to the Chrome Web Store Developer Dashboard
