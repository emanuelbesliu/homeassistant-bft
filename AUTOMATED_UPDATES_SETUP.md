# Automated Updates & Dependency Management - Complete Setup

## ✅ What's Been Implemented

Your BFT Home Assistant integration now has **fully automated update notifications and dependency management**!

### 🔔 Update Notifications for Users

**How users get notified when you release new versions:**

1. **HACS Integration (Automatic)**
   - HACS checks GitHub releases every ~12 hours
   - When you publish a new version, HACS detects it
   - Users see update notification in Home Assistant
   - One-click update via HACS UI

2. **What Users See:**
   ```
   🔔 Update available for BFT Gate Automation
   Current: v1.0.3
   Latest: v1.0.4
   
   [View Release Notes] [Update]
   ```

### 🤖 Dependabot (Automatic Dependency Updates)

**What Dependabot does automatically:**

1. **Monitors Dependencies**
   - Checks `requests` package weekly
   - Checks GitHub Actions weekly
   - Monitors security vulnerabilities daily

2. **Creates Pull Requests Automatically**
   - When `requests` has a new version → PR created
   - When GitHub Actions have updates → PR created
   - When security vulnerabilities found → **Urgent PR** created

3. **Example PR:**
   ```
   Title: deps: bump requests from 2.31.0 to 2.32.0
   
   Description:
   - Fixes SSL timeout issues
   - Improves connection pooling
   - Includes security fix CVE-2024-XXXXX
   
   [All CI checks passed ✅]
   [Safe to merge]
   ```

## 📁 Files Added to Repository

### Configuration Files

**`.github/dependabot.yml`**
```yaml
- Checks Python packages weekly on Mondays
- Checks GitHub Actions weekly
- Max 5 open PRs at once
- Auto-assigns to @emanuelbesliu
- Adds labels: dependencies, python
```

**`requirements.txt`**
```
requests>=2.31.0
```
- Tracks Python dependencies
- Used by Dependabot for monitoring
- Synced with manifest.json

### GitHub Actions Workflows

**`.github/workflows/dependencies.yml`**
- Validates dependency updates
- Runs on every PR that changes dependencies
- Tests: syntax, imports, security

**`.github/workflows/release.yml`**
- Validates new releases
- Checks version matches between tag and manifest
- Runs automatically when you create releases

### Documentation

**`UPDATE_NOTIFICATIONS.md`**
- Complete guide on update notifications
- How HACS works
- Release process documentation

**`DEPENDABOT.md`**
- Complete Dependabot guide
- How to handle PRs
- Configuration options
- Troubleshooting

**`info.md`**
- HACS integration info page
- Shown to users in HACS UI
- Installation instructions
- Configuration examples

## 🚀 How to Release New Versions

### Step-by-Step Release Process

**1. Update version and changelog:**
```bash
# Edit manifest.json
"version": "1.0.4"

# Edit CHANGELOG.md
## [1.0.4] - 2026-03-05
### Fixed
- Your changes here

git add .
git commit -m "Release v1.0.4: Brief description"
git push
```

**2. Create tag and release:**
```bash
git tag v1.0.4
git push origin v1.0.4

gh release create v1.0.4 \
  --title "v1.0.4 - Brief Title" \
  --notes "Release notes here"
```

**3. Upload release asset:**
```bash
cd /path/to/homeassistant-bft
zip -r homeassistant-bft-v1.0.4.zip custom_components/bft/*.py custom_components/bft/manifest.json
gh release upload v1.0.4 homeassistant-bft-v1.0.4.zip
```

**4. Automatic notifications:**
- ✅ GitHub Actions validates release
- ✅ HACS detects new version (within 1-12 hours)
- ✅ Users get update notification
- ✅ Users can one-click update via HACS

## 🤖 How Dependabot Works

### Weekly Dependency Checks

**Every Monday:**
```
Dependabot runs
    ↓
Checks PyPI for requests updates
    ↓
Checks GitHub for Actions updates
    ↓
If update available → Creates PR
    ↓
GitHub Actions validates PR
    ↓
You review and merge
```

### Handling Dependabot PRs

**✅ Merge Immediately If:**
- All CI checks pass
- Patch/minor version (2.31.0 → 2.31.1)
- No breaking changes
- Security fix

**⚠️ Review Carefully If:**
- Major version bump (2.x → 3.x)
- Breaking changes mentioned
- CI checks fail

**Example Dependabot PR:**
```
deps: bump requests from 2.31.0 to 2.32.0

What's Changed:
- Fixed SSL handshake timeout
- Improved connection pooling
- Security: Fixed CVE-2024-12345

Compatibility: ✅ 100% (based on your codebase)
Security: 🔒 Includes security fixes
Change type: Minor (safe to merge)

Files changed:
✓ requirements.txt
✓ (manifest.json will be updated manually)
```

## 📊 Monitoring & Status

### Check Dependabot Status

**On GitHub:**
```
Repository → Insights → Dependency graph → Dependabot

Shows:
- Active dependencies
- Open PRs
- Security alerts
- Next scheduled run
```

### View Workflows

**On GitHub:**
```
Repository → Actions

Workflows:
- Validate Dependencies (runs on PR)
- Validate Release (runs on new release)
```

## 🔒 Security Updates

**Dependabot monitors for vulnerabilities:**

1. **Daily security checks**
2. **Immediate PR creation for critical issues**
3. **Email notifications for security alerts**

**Example Security PR:**
```
🚨 Security: bump requests from 2.30.0 to 2.31.0

Critical: CVE-2023-12345
Severity: HIGH
Impact: SSL certificate validation bypass

This MUST be merged immediately!
```

## 🎯 What This Gives You

### For Maintainers (You)

✅ **Automatic dependency updates** - No manual checking needed  
✅ **Security alerts** - Get notified of vulnerabilities  
✅ **Automated testing** - CI validates all changes  
✅ **Easy merging** - One-click merge for safe updates  
✅ **Release validation** - Catches version mismatches  

### For Users

✅ **Update notifications** - Know when new versions available  
✅ **One-click updates** - Easy update via HACS  
✅ **Release notes** - See what's new  
✅ **Automatic discovery** - No manual checking needed  
✅ **Security fixes** - Get notified of security updates  

## 🧪 Testing Update Notifications

### Test HACS Detection

**1. Add to HACS (if not already):**
```
HACS → Integrations → ⋮ → Custom repositories
Add: https://github.com/emanuelbesliu/homeassistant-bft
Category: Integration
```

**2. Install from HACS:**
```
HACS → Integrations → Search "BFT"
Click "Download"
```

**3. Create test release:**
```bash
# Bump version to test version
git tag v1.0.99-test
git push origin v1.0.99-test
gh release create v1.0.99-test --prerelease
```

**4. Wait for HACS to detect:**
```
HACS → Integrations → Reload data
Wait 5-10 minutes
Should show "Update available: v1.0.99-test"
```

**5. Clean up:**
```bash
gh release delete v1.0.99-test
git push --delete origin v1.0.99-test
```

## 📚 Documentation Files

All documentation is now in the repository:

- **README.md** - Main project documentation
- **CHANGELOG.md** - Version history
- **UPDATE_NOTIFICATIONS.md** - Update system guide
- **DEPENDABOT.md** - Dependency management guide
- **info.md** - HACS display page

## 🎉 Summary

You now have a **professional-grade automated update system**:

1. **Dependabot** monitors dependencies weekly
2. **GitHub Actions** validates all changes automatically
3. **HACS** notifies users of new releases
4. **Security updates** handled automatically
5. **Complete documentation** for maintainers and users

**Next new release:**
```bash
# Just do this:
git tag v1.0.4 && git push origin v1.0.4
gh release create v1.0.4 --title "v1.0.4" --notes "What's new"

# Everything else happens automatically:
✅ Release validated by GitHub Actions
✅ HACS detects new version
✅ Users get notifications
✅ Easy one-click update
```

**No additional configuration needed - everything is ready to go!** 🚀
