# CLAUDE.md

This repository contains the ClipJot clients and API documentation.

**Note:** The backend server is in a separate private repository (`clipjot-backend`).

## Repository Structure

```
clipjot/
├── clients/
│   ├── ios/        # iOS app (Swift/SwiftUI)
│   ├── android/    # Android app (Java)
│   └── chrome/     # Chrome extension
└── docs/
    ├── api/        # API specification (source of truth)
    └── examples/   # API client examples
```

## Clients

Each client has its own CLAUDE.md with build/test instructions:
- `clients/ios/ClipJot/CLAUDE.md`
- `clients/android/CLAUDE.md`
- `clients/chrome/CLAUDE.md`

## API Documentation

The API specification lives in `docs/api/`:
- `docs/api/v1.md` - Full API specification
- `docs/api/changelog.md` - Version history

## Style Guide

See [STYLE_GUIDE.md](STYLE_GUIDE.md) for terminology, branding, and design guidelines.

Visual style guides are in the `style_guide/` directory.
