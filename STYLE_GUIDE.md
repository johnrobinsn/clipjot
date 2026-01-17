# ClipJot Style Guide

This document provides guidance on design, terminology, and UX patterns for ClipJot across all platforms (Web, Chrome Extension, iOS, Android).

## Visual Style Guide

See the interactive HTML style guides in the `style_guide/` directory:

- **[index.html](style_guide/index.html)** - Overview and platform comparison
- **[colors.html](style_guide/colors.html)** - Color palette and semantic colors
- **[typography.html](style_guide/typography.html)** - Font families and scale
- **[buttons.html](style_guide/buttons.html)** - Button styles and variants
- **[forms.html](style_guide/forms.html)** - Inputs, selects, and controls
- **[cards.html](style_guide/cards.html)** - Cards and containers
- **[tags.html](style_guide/tags.html)** - Labels, badges, and chips
- **[alerts.html](style_guide/alerts.html)** - Notifications and feedback
- **[icons.html](style_guide/icons.html)** - Icon library and usage
- **[components.html](style_guide/components.html)** - Full component examples

## Terminology

Use consistent language across all platforms and clients.

### Preferred Terms

| Use | Don't Use | Notes |
|-----|-----------|-------|
| Settings | Options | Chrome shows "Options" in context menu (can't change), but all our UI should say "Settings" |
| Links | Bookmarks | User-facing term for saved items (internal code can use "bookmark") |
| Save | Add | Primary action for saving a link |
| Tags | Labels, Categories | For organizing links |
| Sign in | Log in | For authentication actions |
| Sign out | Log out | For ending a session |

### Feature Names

| Feature | Description |
|---------|-------------|
| Quick Save | Save links immediately without showing the edit form |

## Branding

### App Name
- **ClipJot** (one word, capital C and J)
- Never: Clip Jot, clipjot, CLIPJOT

### Logo/Icon
- Use the filled bookmark icon from Heroicons
- Primary color: Indigo (#6366f1)

```html
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
  <path fill-rule="evenodd" d="M6.32 2.577a49.255 49.255 0 0 1 11.36 0c1.497.174 2.57 1.46 2.57 2.93V21a.75.75 0 0 1-1.085.67L12 18.089l-7.165 3.583A.75.75 0 0 1 3.75 21V5.507c0-1.47 1.073-2.756 2.57-2.93Z" clip-rule="evenodd" />
</svg>
```

## Platform-Specific Notes

### Chrome Extension
- Chrome's context menu shows "Options" - this is controlled by Chrome and cannot be changed
- All UI we control should use "Settings"
- The `options_page` manifest key is required by Chrome's API

### Android
- Follow Material 3 guidelines where they don't conflict with ClipJot's design system
- Use "Settings" in all navigation and UI elements

### iOS
- Follow Human Interface Guidelines where they don't conflict with ClipJot's design system
- Use "Settings" in all navigation and UI elements

### Web
- DaisyUI 4 + Tailwind CSS
- Follow the visual style guide for component patterns
