# TODO

## Before Release

- [ ] Remove `android:usesCleartextTraffic="true"` from `AndroidManifest.xml` - this was added for local development/emulator testing and should be removed for production (or replaced with a proper network security config that only allows cleartext for specific debug hosts)
