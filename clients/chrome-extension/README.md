# ClipJot Chrome Extension

Save bookmarks to [ClipJot](https://clipjot.net) with one click.

## Features

- **One-click save** - Save the current page instantly
- **Quick Save mode** - Save without showing the form (enable in Settings)
- **Right-click to save** - Save any link from the context menu
- **Tag management** - Add tags with autocomplete from your existing tags
- **Keyboard shortcut** - Press `Alt+Shift+J` to open the extension
- **Works with clipjot.net** - Ready to use with the production server

## Installation

### Option A: Chrome Web Store (easiest)

1. Visit the [ClipJot extension page](https://chromewebstore.google.com/detail/ocaphhejpkkbiinjcbfpocgempolhdfd) on the Chrome Web Store
2. Click **Add to Chrome**
3. The ClipJot icon will appear in your toolbar

### Option B: Download ZIP from GitHub

1. Go to the [latest release](https://github.com/johnrobinsn/clipjot/releases/tag/chrome-v1.0.0)
2. Under "Assets", download `Source code (zip)`
3. Extract the ZIP file
4. The extension is in the `clients/chrome-extension` folder
5. Open Chrome and go to `chrome://extensions/`
6. Turn on **Developer mode** (toggle in the top right corner)
7. Click **Load unpacked** and select the `chrome-extension` folder

### Option C: Clone with Git

```bash
git clone https://github.com/johnrobinsn/clipjot.git
cd clipjot/clients/chrome-extension
```

Then load unpacked in Chrome (see Option B, steps 5-7).

> **Tip:** Click the puzzle piece icon in Chrome's toolbar and pin ClipJot for easy access.

### Sign In

1. Click the ClipJot icon in your toolbar
2. Sign in with **Google** or **GitHub**
3. You're ready to save bookmarks!

## Usage

### Save the Current Page
1. Click the ClipJot icon (or press `Alt+Shift+J`)
2. Add tags or a comment (optional)
3. Click **Save Bookmark**

### Save Any Link
1. Right-click any link on a page
2. Select **Save to ClipJot**
3. Add tags and click Save

### Quick Save Mode
Want to save pages instantly without seeing the form?
1. Click the **gear icon** to open Settings
2. Enable **Quick Save**
3. Now clicking the extension saves immediately!

## Settings

Click the gear icon in the extension popup to access settings:

- **Backend URL** - Server address (default: `https://clipjot.net`)
- **Quick Save** - Save instantly without showing the form
- **Keyboard Shortcuts** - Link to customize `Alt+Shift+J`

## Troubleshooting

**"Invalid token" or signed out unexpectedly?**
- Click Sign Out, then sign in again

**Extension not appearing?**
- Make sure Developer mode is enabled at `chrome://extensions/`
- Try clicking the puzzle piece icon and pinning ClipJot

**Can't connect to server?**
- Check your internet connection
- Verify the backend URL in Settings is correct

## Updating

To update to a new version:
1. Download the latest release
2. Go to `chrome://extensions/`
3. Click the refresh icon on the ClipJot extension
4. Or remove and re-add the extension

---

## For Developers

### Project Structure

```
chrome-extension/
├── manifest.json           # Extension manifest (V3)
├── popup/                  # Main popup UI
├── options/                # Settings page
├── background/             # Service worker
└── icons/                  # Extension icons
```

### Permissions

- `activeTab` - Read current tab's URL and title
- `contextMenus` - Add right-click menu item
- `storage` - Store session and settings
- `identity` - Handle OAuth flows
- `host_permissions` - Communicate with ClipJot server

### Chrome Web Store

For publishing to the Chrome Web Store:

```bash
zip -r clipjot-extension.zip chrome-extension/
```

Upload to the [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole/).
