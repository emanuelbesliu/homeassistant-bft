# Dependabot Configuration

This repository uses GitHub Dependabot to automatically keep dependencies up-to-date.

## What Gets Updated

### 1. Python Dependencies (`requirements.txt`)
- **Package**: `requests` (currently >=2.31.0)
- **Frequency**: Weekly on Mondays
- **What happens**: Dependabot creates PRs when new versions are available

### 2. GitHub Actions
- **Actions**: All workflows in `.github/workflows/`
- **Frequency**: Weekly on Mondays  
- **What happens**: Dependabot updates action versions (e.g., `actions/checkout@v4` → `@v5`)

## How It Works

```
Monday morning
    ↓
Dependabot checks for updates
    ↓
Finds new version (e.g., requests 2.32.0)
    ↓
Creates PR automatically
    ↓
Runs CI validation workflows
    ↓
✅ Tests pass → Ready to merge
❌ Tests fail → Investigate before merging
    ↓
Maintainer reviews and merges
    ↓
Updated package in next release
```

## Automatic PR Creation

When a dependency update is available, Dependabot will:

1. **Create a Pull Request** with:
   - Updated `requirements.txt`
   - Clear title: `deps: bump requests from 2.31.0 to 2.32.0`
   - Changelog from package maintainer
   - Compatibility score

2. **Run Validations**:
   - GitHub Actions workflows run automatically
   - Validates Python syntax
   - Tests dependency imports
   - Checks for security vulnerabilities

3. **Add Labels**:
   - `dependencies` - All dependency updates
   - `python` - Python package updates
   - `github-actions` - GitHub Actions updates

4. **Assign**: PRs are assigned to `@emanuelbesliu`

## Configuration Files

### `.github/dependabot.yml`
Main configuration file that controls:
- Update frequency (weekly)
- Package ecosystems to monitor
- PR limits (max 5 open at once)
- Labels and assignees
- Commit message format

### `requirements.txt`
Lists Python dependencies to track:
```
requests>=2.31.0
```

### `.github/workflows/dependencies.yml`
Validates dependency updates:
- Installs updated dependencies
- Verifies imports work
- Checks manifest.json matches requirements.txt
- Runs security vulnerability scan

## Handling Dependabot PRs

### ✅ When to Merge

Merge immediately if:
- ✅ All CI checks pass
- ✅ Patch/minor version bump (2.31.0 → 2.31.1 or 2.32.0)
- ✅ No breaking changes in changelog
- ✅ Security vulnerability fix

### ⚠️ When to Review Carefully

Review before merging if:
- ⚠️ Major version bump (2.x.x → 3.0.0)
- ⚠️ Breaking changes mentioned in changelog
- ⚠️ Tests fail in CI
- ⚠️ Changes API compatibility

### ❌ When to Close

Close without merging if:
- ❌ Breaking changes require code updates
- ❌ Update not compatible with Home Assistant
- ❌ Security issues reported with new version

## Manual Dependency Updates

If you need to update dependencies manually:

```bash
# Update requirements.txt
echo "requests>=2.32.0" > requirements.txt

# Update manifest.json
# Edit custom_components/bft/manifest.json
"requirements": ["requests>=2.32.0"]

# Test locally
pip install -r requirements.txt
python -m py_compile custom_components/bft/cover.py

# Commit changes
git add requirements.txt custom_components/bft/manifest.json
git commit -m "deps: update requests to 2.32.0"
git push
```

## Security Updates

Dependabot also monitors for **security vulnerabilities**:

### Security Advisories
- Checks CVE databases
- Monitors GitHub Security Advisories
- Creates **urgent PRs** for critical vulnerabilities

### Security PR Example
```
🚨 Security: bump requests from 2.30.0 to 2.31.0

Critical vulnerability CVE-2023-XXXXX fixed in requests 2.31.0
Severity: HIGH
Impact: SSL certificate validation bypass

→ Merge immediately after CI passes
```

## Customizing Dependabot

### Change Update Frequency

Edit `.github/dependabot.yml`:
```yaml
schedule:
  interval: "daily"  # Options: daily, weekly, monthly
  day: "monday"      # For weekly: monday-sunday
  time: "09:00"      # Optional: specific time
```

### Limit Update Scope

```yaml
# Only security updates
open-pull-requests-limit: 0
security-updates-only: true
```

### Group Updates

```yaml
# Group all patch updates into single PR
groups:
  patch-updates:
    applies-to: version-updates
    update-types:
      - "patch"
```

### Ignore Specific Updates

```yaml
ignore:
  - dependency-name: "requests"
    versions: ["2.30.x"]  # Skip 2.30.x versions
```

## Benefits

✅ **Security**: Automatic security vulnerability fixes  
✅ **Maintenance**: Stay current with latest features  
✅ **Compatibility**: Avoid deprecated package versions  
✅ **Automation**: Reduces manual dependency management  
✅ **Transparency**: Clear changelog in PRs  

## Monitoring

### Check Dependabot Status

1. **Repository → Insights → Dependency graph → Dependabot**
   - View all dependency PRs
   - See update schedule
   - Check security alerts

2. **Security → Dependabot alerts**
   - View security vulnerabilities
   - See recommended fixes
   - Track remediation status

### Enable Email Notifications

Settings → Notifications → Dependabot:
- ✅ Send email on new PR
- ✅ Send email on security alert
- ✅ Daily/weekly digest

## Troubleshooting

### Dependabot Not Creating PRs

**Check:**
1. Dependabot enabled: Settings → Security → Dependabot
2. Permissions: Dependabot has write access
3. File syntax: Validate `.github/dependabot.yml`
4. Update schedule: Next run time shown in Insights

### CI Failing on Dependabot PRs

**Common causes:**
- Import compatibility issues
- Breaking API changes
- Missing transitive dependencies

**Solution:**
```bash
# Test locally first
git checkout dependabot/pip/requests-2.32.0
pip install -r requirements.txt
python -m py_compile custom_components/bft/cover.py
```

### Too Many Open PRs

Adjust PR limit in `.github/dependabot.yml`:
```yaml
open-pull-requests-limit: 3  # Default: 5
```

## Example Dependabot PR

**Title**: `deps: bump requests from 2.31.0 to 2.31.3`

**Description**:
```markdown
Bumps requests from 2.31.0 to 2.31.3.

Release notes:
- Fixed SSL handshake timeout issue
- Improved connection pooling
- Security fix for CVE-2024-XXXXX

Changelog: https://github.com/psf/requests/blob/main/CHANGELOG.md

---
✅ All checks passed
🔒 Includes security fixes
⬆️ Patch update (safe to merge)
```

## Resources

- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [dependabot.yml Reference](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file)
- [Semantic Versioning](https://semver.org/)
- [Python Package Index (PyPI)](https://pypi.org/project/requests/)
