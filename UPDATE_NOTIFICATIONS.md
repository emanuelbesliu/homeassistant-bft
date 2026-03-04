# Update Notifications Setup

This document explains how update notifications work for the BFT Home Assistant integration.

## How It Works

The BFT integration supports **automatic update notifications** through HACS (Home Assistant Community Store). When you publish a new release, users get notified automatically.

### 🔔 For Users: How to Get Update Notifications

#### Method 1: HACS (Recommended)

**1. Add as HACS Custom Repository:**
```
HACS → Integrations → ⋮ (top-right) → Custom repositories
Repository: https://github.com/emanuelbesliu/homeassistant-bft
Category: Integration
Click Add
```

**2. Install:**
```
HACS → Integrations → Search "BFT Gate"
Click → Download
Restart Home Assistant
```

**3. Updates:**
- HACS checks GitHub releases every few hours
- When new version is available, you'll see:
  - Badge on HACS menu
  - Notification in Home Assistant
  - "Update available" in HACS integration list

**4. Apply Update:**
```
HACS → Integrations → BFT Gate Automation
Click "Update" button
Restart Home Assistant
```

#### Method 2: Manual Installation

If not using HACS, check releases manually:
- Visit: https://github.com/emanuelbesliu/homeassistant-bft/releases
- Download latest `homeassistant-bft-vX.X.X.zip`
- Extract to `custom_components/bft/`
- Restart Home Assistant

---

## 🚀 For Maintainers: Release Process

### Creating a New Release

**1. Update Version:**
```bash
# Edit manifest.json
"version": "1.0.4"

# Update CHANGELOG.md
## [1.0.4] - 2026-03-05
### Fixed
- Your changes here
```

**2. Commit and Tag:**
```bash
git add custom_components/bft/manifest.json CHANGELOG.md
git commit -m "Release v1.0.4: Brief description"
git push

git tag v1.0.4
git push origin v1.0.4
```

**3. Create GitHub Release:**
```bash
gh release create v1.0.4 \
  --title "v1.0.4 - Brief Title" \
  --notes "Release notes here"
  
# Upload release asset
zip -r homeassistant-bft-v1.0.4.zip custom_components/bft/*.py custom_components/bft/manifest.json
gh release upload v1.0.4 homeassistant-bft-v1.0.4.zip
```

**4. HACS Auto-Detection:**
- HACS monitors GitHub releases via API
- New tag triggers update notification
- Usually detected within 1-6 hours
- No additional configuration needed!

### Release Validation

The GitHub Actions workflow (`.github/workflows/release.yml`) automatically:
- ✅ Validates Python syntax
- ✅ Checks version matches between tag and manifest.json
- ✅ Validates HACS configuration
- ✅ Creates release summary

### Version Numbering

Follow Semantic Versioning (SemVer):
- **Major (1.x.x)**: Breaking changes
- **Minor (x.1.x)**: New features (backwards compatible)
- **Patch (x.x.1)**: Bug fixes

Examples:
- `1.0.4` → `1.0.5`: Bug fix
- `1.0.5` → `1.1.0`: New feature (e.g., add sensor)
- `1.1.0` → `2.0.0`: Breaking change (e.g., change config format)

---

## 🎯 Current Status

### ✅ What's Already Set Up

1. **HACS Ready**: `hacs.json` configured correctly
2. **Version Tracking**: `manifest.json` has version field
3. **GitHub Releases**: Using proper tagging (v1.0.x)
4. **Release Assets**: Zip files attached to releases
5. **Changelog**: `CHANGELOG.md` tracks all changes
6. **Info Page**: `info.md` for HACS display
7. **CI Validation**: GitHub Actions workflow validates releases

### 📋 How Updates are Detected

```
Developer publishes release
         ↓
   Creates git tag (v1.0.4)
         ↓
   Pushes to GitHub
         ↓
   HACS checks GitHub API
         ↓
   Detects new tag/release
         ↓
   Compares with installed version
         ↓
   Shows update notification
         ↓
   User clicks "Update"
         ↓
   HACS downloads new version
         ↓
   User restarts HA
```

### 🔄 Update Check Frequency

- **HACS**: Every 12 hours by default
- **Manual**: Click "Reload data" in HACS → Integrations
- **Immediate**: After HA restart

---

## 🎨 Customizing Notifications

### HACS Info Display

Edit `info.md` to customize what users see in HACS:
- Installation instructions
- Configuration examples
- Troubleshooting tips
- Update notes

### Release Notes Format

Use clear, user-friendly release notes:

```markdown
## 🔧 What's New in v1.0.4

### Fixed
- Resolved timeout issues with slow networks
- Fixed state detection for partially open gates

### Changed
- Increased default timeout to 30 seconds

### Security
- Updated SSL handling for better compatibility
```

---

## 🧪 Testing Update Notifications

**1. Install older version manually:**
```bash
# Install v1.0.2 for testing
git checkout v1.0.2
cp -r custom_components/bft /config/custom_components/
```

**2. Create test release:**
```bash
git checkout main
# Bump version to 1.0.99-test
git tag v1.0.99-test
git push origin v1.0.99-test
gh release create v1.0.99-test --prerelease --notes "Test release"
```

**3. Check HACS:**
```
HACS → Integrations → Reload data
Wait a few minutes
Should show "Update available"
```

**4. Clean up test release:**
```bash
gh release delete v1.0.99-test
git push --delete origin v1.0.99-test
git tag -d v1.0.99-test
```

---

## 📚 Additional Resources

- [HACS Documentation](https://hacs.xyz/docs/publish/integration)
- [Semantic Versioning](https://semver.org/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Home Assistant Integration Releases](https://developers.home-assistant.io/docs/creating_integration_manifest)

---

## ✨ Future Enhancements

Potential improvements for update notifications:

1. **Add Version Sensor**: Create a sensor entity showing current/latest version
2. **Update Binary Sensor**: Binary sensor indicating if update available
3. **Automation Trigger**: Fire event when update detected
4. **Persistent Notification**: Create HA notification for updates
5. **Discord/Slack Webhook**: Notify community of new releases

These would require adding a `sensor.py` platform to the integration.
