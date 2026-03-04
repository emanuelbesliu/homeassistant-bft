# Auto-Versioning Workflow

## Overview

The BFT integration now includes **automatic version bumping** when Dependabot PRs are merged! This workflow automatically handles all version management tasks, so you don't have to manually update versions for dependency updates.

## How It Works

```
Dependabot creates PR
  (e.g., "deps: bump requests from 2.31.0 to 2.32.0")
         ↓
You review and merge PR
         ↓
🤖 Auto-version workflow triggers
         ↓
Automatically performs:
  ✅ Bumps version (1.0.3 → 1.0.4)
  ✅ Updates manifest.json
  ✅ Syncs requirements in manifest.json
  ✅ Updates CHANGELOG.md
  ✅ Creates release zip file
  ✅ Commits changes to main
  ✅ Creates git tag (v1.0.4)
  ✅ Publishes GitHub release
         ↓
HACS detects new release
         ↓
Users get update notification
```

## Version Bump Strategy

The workflow automatically determines the version bump type based on the PR title:

### Patch Bump (default)
**Pattern:** Most dependency updates  
**Example:** `deps: bump requests from 2.31.0 to 2.31.3`  
**Result:** `1.0.3` → `1.0.4`

### Minor Bump
**Pattern:** PR title contains "minor" or "feature"  
**Example:** `deps(minor): bump requests to 2.32.0`  
**Result:** `1.0.3` → `1.1.0`

### Major Bump
**Pattern:** PR title contains "major" or "breaking"  
**Example:** `deps(major): bump requests to 3.0.0`  
**Result:** `1.0.3` → `2.0.0`

## What Gets Updated Automatically

### 1. `manifest.json`
```json
{
  "version": "1.0.4",  // ✅ Auto-updated
  "requirements": ["requests>=2.32.0"]  // ✅ Auto-synced from requirements.txt
}
```

### 2. `CHANGELOG.md`
```markdown
## [1.0.4] - 2026-03-05

### Changed
- deps: bump requests from 2.31.0 to 2.32.0 (#5)
- Dependency updates from Dependabot
```

### 3. Release Artifacts
- ✅ Creates `homeassistant-bft-v1.0.4.zip`
- ✅ Git tag `v1.0.4`
- ✅ GitHub release with notes

## Workflow Configuration

The workflow is defined in `.github/workflows/auto-version-bump.yml` and:

- **Triggers:** When a PR is closed on `main` branch
- **Condition:** Only runs if:
  - PR was merged (not just closed)
  - PR was created by `dependabot[bot]`
  - OR PR branch starts with `dependabot/`
- **Permissions:** 
  - `contents: write` - To push commits and tags
  - `pull-requests: write` - To read PR details

## Example Workflow Run

### Trigger Event
```
PR #5: "deps: bump requests from 2.31.0 to 2.32.0"
Status: Merged to main
Author: dependabot[bot]
```

### Automatic Actions
```bash
1. Checkout code with full history
2. Get current version: 1.0.3
3. Calculate new version: 1.0.4 (patch bump)
4. Update manifest.json: version → 1.0.4
5. Sync requirements: requests>=2.32.0
6. Update CHANGELOG.md with new entry
7. Create homeassistant-bft-v1.0.4.zip
8. Commit: "chore: bump version to 1.0.4"
9. Create tag: v1.0.4
10. Publish release with notes and zip file
```

### Result
- ✅ New release: https://github.com/emanuelbesliu/homeassistant-bft/releases/tag/v1.0.4
- ✅ HACS will detect update within 1-12 hours
- ✅ Users get notification in Home Assistant

## Manual Version Bumps

For changes that **aren't** from Dependabot (like feature additions or bug fixes), you still need to bump versions manually:

```bash
# 1. Update version in manifest.json
# Edit: custom_components/bft/manifest.json
"version": "1.1.0"

# 2. Update CHANGELOG.md
## [1.1.0] - 2026-03-05
### Added
- New feature description

# 3. Commit, tag, and release
git add .
git commit -m "feat: add new feature"
git push

git tag v1.1.0
git push origin v1.1.0

# 4. Create release with zip
zip -r homeassistant-bft-v1.1.0.zip custom_components/bft/*.py custom_components/bft/manifest.json
gh release create v1.1.0 --title "v1.1.0 - Feature Name" --notes "Release notes" homeassistant-bft-v1.1.0.zip
```

## Customizing the Workflow

### Change Version Bump Logic

Edit `.github/workflows/auto-version-bump.yml` step "Calculate new version":

```yaml
# Example: Always do minor bumps for dependency updates
if [[ "$PR_TITLE" == *"deps"* ]]; then
  MINOR=$((MINOR + 1))
  PATCH=0
fi
```

### Skip Auto-Versioning for Specific PRs

Add `[skip-version]` to PR title:

```
deps: bump requests from 2.31.0 to 2.32.0 [skip-version]
```

Then update the workflow condition:

```yaml
if: |
  github.event.pull_request.merged == true &&
  !contains(github.event.pull_request.title, '[skip-version]') &&
  (github.event.pull_request.user.login == 'dependabot[bot]' ||
   startsWith(github.event.pull_request.head.ref, 'dependabot/'))
```

### Bundle Multiple Dependency Updates

To avoid creating a release for every single dependency update:

1. **Don't auto-merge** Dependabot PRs immediately
2. **Wait** for multiple PRs to accumulate
3. **Merge them together** in a batch
4. The workflow will create **one release** with all updates

## Monitoring

### Check Workflow Status

```bash
# View recent workflow runs
gh run list --workflow=auto-version-bump.yml

# View specific run details
gh run view <run-id>

# View workflow logs
gh run view <run-id> --log
```

### GitHub UI

1. Go to: **Repository → Actions → Auto Version Bump on Dependency Updates**
2. View recent runs and their status
3. Check logs for any errors

## Troubleshooting

### Workflow Doesn't Trigger

**Check:**
1. PR was created by Dependabot
2. PR was merged (not closed without merging)
3. PR targeted the `main` branch
4. Workflow file exists in main branch

**Debug:**
```bash
# Check if workflow is active
gh workflow list

# View workflow details
gh workflow view auto-version-bump.yml
```

### Version Bump Failed

**Common issues:**

1. **Permission Error:**
   - Ensure GitHub Actions has write permissions
   - Settings → Actions → General → Workflow permissions → "Read and write permissions"

2. **Merge Conflict:**
   - Someone manually updated manifest.json between merge and workflow run
   - Manually resolve and re-run workflow

3. **Invalid Version Format:**
   - Current version must be semver (X.Y.Z)
   - Check manifest.json version format

### Release Creation Failed

**Common issues:**

1. **Tag Already Exists:**
   - Delete the tag: `git push --delete origin v1.0.4`
   - Re-run the workflow

2. **Zip File Missing:**
   - Check workflow logs for zip creation step
   - Ensure all required files exist

## Benefits

### For Maintainers
✅ **Zero manual work** for dependency updates  
✅ **Consistent versioning** - No human errors  
✅ **Automated releases** - No forgotten steps  
✅ **Complete audit trail** - All changes tracked  
✅ **Time savings** - Focus on features, not releases

### For Users
✅ **Faster updates** - Releases published immediately  
✅ **Better security** - Security fixes released quickly  
✅ **Transparency** - Clear changelog for every release  
✅ **Reliability** - Automated testing before release

## Comparison: Before vs After

### Before (Manual)
```
Dependabot PR merged
  ↓
⏰ Wait for maintainer to notice
  ↓
👤 Manually update manifest.json
  ↓
👤 Manually update CHANGELOG.md
  ↓
👤 Manually create zip file
  ↓
👤 Manually create git tag
  ↓
👤 Manually create GitHub release
  ↓
⏰ 1-7 days later: Release published
```

### After (Automated)
```
Dependabot PR merged
  ↓
🤖 Workflow runs automatically
  ↓
✅ 2 minutes later: Release published
```

## Future Enhancements

Potential improvements to consider:

1. **Changelog Parsing:** Extract detailed changes from Dependabot PR body
2. **Security Alerts:** Special handling for security vulnerability fixes
3. **Rollback Support:** Auto-rollback if release fails validation
4. **Slack/Discord Notifications:** Alert team when auto-release happens
5. **Bundle Updates:** Group multiple dependency updates into single release

## Related Documentation

- [DEPENDABOT.md](DEPENDABOT.md) - Dependabot configuration
- [UPDATE_NOTIFICATIONS.md](UPDATE_NOTIFICATIONS.md) - How users get notified
- [AUTOMATED_UPDATES_SETUP.md](AUTOMATED_UPDATES_SETUP.md) - Complete automation guide
- [CHANGELOG.md](CHANGELOG.md) - Version history

## Summary

This workflow provides **fully automated version management** for dependency updates:

- ✅ Automatically bumps version on Dependabot PR merge
- ✅ Updates all necessary files (manifest, changelog, zip)
- ✅ Creates git tags and GitHub releases
- ✅ Notifies users via HACS
- ✅ Zero manual intervention required

**Just merge the Dependabot PR, and everything else happens automatically!** 🎉
