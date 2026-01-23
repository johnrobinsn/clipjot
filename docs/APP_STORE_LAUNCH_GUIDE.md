# ClipJot Mobile App Store Launch Guide

This guide covers the complete process for launching ClipJot on the Google Play Store (Android) and Apple App Store (iOS).

---

## Part 1: Google Play Store (Android)

### Pre-Launch Readiness Checklist

**Critical Fixes (Must Do)**
- [ ] Remove `android:usesCleartextTraffic="true"` from `AndroidManifest.xml`
- [ ] Create release signing keystore (`.jks` file)
- [ ] Configure signing in `app/build.gradle`
- [ ] Store keystore securely (NOT in git repo)

**Content & Assets Preparation**
- [ ] App icon: Already provided ✓
- [ ] Feature graphic (1024x500 px) for store listing
- [ ] Screenshots: Phone (min 2) + 7" tablet + 10" tablet
- [ ] Short description (80 chars max)
- [ ] Full description (4000 chars max)
- [ ] Privacy policy URL (required - host on clipjot.net)
- [ ] App category selection (Productivity or Tools)

**Testing**
- [ ] Run full test suite: `./gradlew test connectedAndroidTest`
- [ ] Test on API 29, 31, 33, 34 (min SDK through target)
- [ ] Test OAuth flows with production backend
- [ ] Test Share intent from Chrome, Twitter, etc.
- [ ] Test deep link `clipjot://oauth/callback`

### Google Play Developer Account Setup

1. **Create Account** at https://play.google.com/console
   - One-time $25 registration fee
   - Requires Google account
   - Identity verification (takes 1-2 days for individuals)

2. **Complete Developer Profile**
   - Developer name (shown on store)
   - Contact email (public)
   - Physical address (required, can be hidden)
   - Phone number for verification

3. **Accept Agreements**
   - Google Play Developer Distribution Agreement
   - App content policies

### Release Build & Signing

**Create Keystore (one-time)**
```bash
keytool -genkey -v -keystore clipjot-release.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias clipjot
```

**Configure `app/build.gradle`**
```groovy
android {
    signingConfigs {
        release {
            storeFile file('../clipjot-release.jks')
            storePassword System.getenv('KEYSTORE_PASSWORD')
            keyAlias 'clipjot'
            keyPassword System.getenv('KEY_PASSWORD')
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
            // existing minification config
        }
    }
}
```

**Build Release Bundle**
```bash
./gradlew bundleRelease
# Output: app/build/outputs/bundle/release/app-release.aab
```

### Submission Steps

1. Create new app in Play Console
2. Complete store listing (description, screenshots, etc.)
3. Set up content rating questionnaire
4. Configure pricing (Free)
5. Select target countries
6. Upload AAB (Android App Bundle)
7. Submit for review (typically 1-3 days)

---

## Part 2: App Store (iOS)

### Pre-Launch Readiness Checklist

**Critical Fixes (Must Do)**
- [ ] Fix iOS deployment target: Change from `18.5` to `15.0` or `16.0`
- [ ] Fix App Group inconsistency:
  - Main app: `group.net.clipjot.shared`
  - Share Extension: `group.com.clipjot.shared` ← Change to `group.net.clipjot.shared`
- [ ] Update Keychain access groups in ShareExtension.entitlements to match

**Content & Assets Preparation**
- [ ] App icon: Already provided ✓
- [ ] Screenshots for each device size:
  - iPhone 6.9" (iPhone 16 Pro Max)
  - iPhone 6.7" (iPhone 15 Pro Max)
  - iPhone 6.5" (iPhone 14 Plus)
  - iPhone 5.5" (iPhone 8 Plus - optional)
  - iPad Pro 12.9" (6th gen)
  - iPad Pro 11" (optional)
- [ ] App previews (optional but recommended - 15-30 sec video)
- [ ] Description, keywords, support URL
- [ ] Privacy policy URL (required)
- [ ] App category: Productivity

**Testing**
- [ ] Test on iPhone (various sizes)
- [ ] Test on iPad (verify layouts work)
- [ ] Test Share Extension from Safari, Twitter, etc.
- [ ] Test OAuth flows with production backend
- [ ] Run test suite: `xcodebuild test -scheme ClipJot`

### Apple Developer Account Setup

1. **Enroll at** https://developer.apple.com/programs/
   - $99/year membership fee
   - Requires Apple ID
   - Identity verification (D-U-N-S for organizations, or government ID for individuals)
   - Approval takes 24-48 hours

2. **Set Up App Store Connect**
   - Access at https://appstoreconnect.apple.com
   - Create app record with bundle ID `net.clipjot.ClipJot`
   - Register App Groups capability in developer portal

3. **Configure Certificates & Profiles**
   - Xcode handles automatically with "Automatically manage signing"
   - Ensure Team ID matches in project settings

### iPad-Specific Considerations

The app already supports iPad (Device Family `1,2`). Verify:
- [ ] All views adapt properly to larger screens
- [ ] Split view / multitasking works (iPadOS)
- [ ] Landscape orientation works correctly
- [ ] Keyboard shortcuts (optional enhancement)

### Build & Archive

```bash
# Archive for distribution
xcodebuild -scheme ClipJot -archivePath ClipJot.xcarchive archive

# Or use Xcode: Product → Archive
```

### Submission Steps

1. Create app record in App Store Connect
2. Complete app information (description, keywords, etc.)
3. Upload screenshots for all device sizes
4. Set up pricing (Free)
5. Complete App Privacy questionnaire
6. Upload build via Xcode (Distribute App → App Store Connect)
7. Submit for review (typically 1-2 days, can be longer)

---

## Part 3: Versioning Best Practices

### Semantic Versioning (SemVer)

Use **MAJOR.MINOR.PATCH** format:
- **MAJOR**: Breaking changes or major new features
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes

**Example progression**: 1.0.0 → 1.0.1 → 1.1.0 → 1.2.0 → 2.0.0

### Platform-Specific Version Fields

**Android** (`build.gradle`)
- `versionName`: User-visible (e.g., "1.2.3")
- `versionCode`: Internal integer, must increment for each upload (1, 2, 3...)

**iOS** (Xcode project)
- `MARKETING_VERSION`: User-visible (e.g., "1.2.3")
- `CURRENT_PROJECT_VERSION`: Build number, must increment (1, 2, 3...)

### Recommended Workflow

1. **Tag releases in git**: `git tag -a v1.0.0 -m "Release 1.0.0"`
2. **Keep versions in sync** across Android/iOS when possible
3. **Build numbers can differ** (Android versionCode vs iOS build) - that's OK
4. **Document changes** in CHANGELOG.md or GitHub Releases

---

## Part 4: GitHub Repository Management

### Repository Structure Options

**Option A: Monorepo (Current)**
```
LinkJot/
├── clients/
│   ├── android/
│   └── ios/
├── chrome-extension/
└── web/
```
- Pros: Single source of truth, easier cross-platform changes
- Cons: Larger clone size, mixed issues/PRs

**Option B: Separate Repos**
```
clipjot-android/
clipjot-ios/
clipjot-web/
```
- Pros: Platform-focused, cleaner issues, independent releases
- Cons: Harder to coordinate changes, duplicated CI config

**Recommendation**: Keep monorepo but use GitHub Releases with platform tags (e.g., `android-v1.0.0`, `ios-v1.0.0`).

### Release Process

1. **Create release branch** (optional): `release/android-1.0.0`
2. **Update version numbers** in build files
3. **Update CHANGELOG.md**
4. **Create git tag**: `git tag android-v1.0.0`
5. **Push tag**: `git push origin android-v1.0.0`
6. **Create GitHub Release**:
   - Attach signed APK/AAB for Android
   - Attach nothing for iOS (distributed via App Store only)
   - Include release notes

### CI/CD Recommendations

**GitHub Actions** for automated builds:
- Build on every PR to catch issues
- Create release artifacts on tag push
- Run tests automatically

### Open Source Considerations

- **LICENSE**: Ensure license is clear (MIT, Apache 2.0, etc.)
- **CONTRIBUTING.md**: Guidelines for contributors
- **Issue templates**: Bug reports, feature requests
- **Branch protection**: Require PR reviews for main branch

---

## Part 5: Pre-Launch Verification

### Android
1. Build release AAB: `./gradlew bundleRelease`
2. Install on test device via bundletool or internal testing track
3. Verify all features work with production backend
4. Check ProGuard didn't break anything

### iOS
1. Archive and upload to TestFlight
2. Test on physical iPhone and iPad
3. Verify Share Extension works
4. Test OAuth flow end-to-end

### Both Platforms
- Verify OAuth redirects work with `clipjot://` scheme
- Test offline/error states
- Verify backend URL is production (`https://clipjot.net`)

---

## Current App Status Summary

### Android App
- **Location**: `clients/android/`
- **Package**: `com.clipjot.android`
- **SDK**: Target 34 (Android 14), Min 29 (Android 10)
- **Status**: ~90% ready, needs signing setup and security fix

### iOS App
- **Location**: `clients/ios/`
- **Bundle ID**: `net.clipjot.ClipJot`
- **Supports**: iPhone + iPad
- **Status**: Needs deployment target fix and App Group alignment
