# Branch Protection Quick Start

This is a quick reference for repository administrators to set up branch protection for the skill-fleet repository.

## Prerequisites

✅ Repository administrator access
✅ GitHub CLI installed (`gh`) - [Install guide](https://cli.github.com/)
✅ Authenticated with GitHub (`gh auth login`)

## Quick Setup (Recommended)

Run the interactive setup script:

```bash
./scripts/setup_branch_protection.sh
```

This script will guide you through:
1. Viewing current protection rules
2. Applying recommended settings
3. Verifying the configuration

## Manual Setup via GitHub UI

If you prefer to configure via the web interface:

1. Go to: https://github.com/Qredence/skill-fleet/settings/branches
2. Click **Add rule** (or edit existing rule for `main`)
3. Configure the following settings:

### Essential Settings

| Setting | Value |
|---------|-------|
| Branch name pattern | `main` |
| Require pull request before merging | ✅ Enabled |
| Required approving reviews | `1` |
| Dismiss stale reviews | ✅ Enabled |
| Require status checks to pass | ✅ Enabled |
| Require branches up to date | ✅ Enabled |
| Require conversation resolution | ✅ Enabled |
| Require linear history | ✅ Enabled |
| Include administrators | ✅ Enabled |
| Allow force pushes | ❌ Disabled |
| Allow deletions | ❌ Disabled |

### Required Status Checks

Add these exact check names (case-sensitive):
- `lint / Lint with Ruff`
- `test / Run Tests (3.12)`
- `test / Run Tests (3.13)`
- `build / Build Verification`
- `security / Security Checks`
- `all-checks / All Checks Passed`

4. Click **Save changes**

## Using GitHub CLI

Quick one-liner to apply all settings:

```bash
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/Qredence/skill-fleet/branches/main/protection \
  -f required_status_checks[strict]=true \
  -f required_status_checks[contexts][]='lint / Lint with Ruff' \
  -f required_status_checks[contexts][]='test / Run Tests (3.12)' \
  -f required_status_checks[contexts][]='test / Run Tests (3.13)' \
  -f required_status_checks[contexts][]='build / Build Verification' \
  -f required_status_checks[contexts][]='security / Security Checks' \
  -f required_status_checks[contexts][]='all-checks / All Checks Passed' \
  -F enforce_admins=true \
  -f required_pull_request_reviews[dismiss_stale_reviews]=true \
  -f required_pull_request_reviews[required_approving_review_count]=1 \
  -F required_linear_history=true \
  -F allow_force_pushes=false \
  -F allow_deletions=false \
  -F required_conversation_resolution=true
```

## Using REST API with curl

Using the JSON configuration file:

```bash
curl -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/Qredence/skill-fleet/branches/main/protection \
  -d @.github/branch-protection-config.json
```

Replace `YOUR_GITHUB_TOKEN` with a personal access token that has `repo` scope.

## Verification

After setup, verify the configuration:

```bash
# Check current settings
gh api repos/Qredence/skill-fleet/branches/main/protection | jq

# Or use the setup script
./scripts/setup_branch_protection.sh
# Select option 3: Verify configuration
```

## Testing

Create a test PR to ensure:
1. ✅ Status checks run and appear on the PR
2. ✅ Merge is blocked until checks pass
3. ✅ At least 1 approval is required
4. ✅ Conversations must be resolved

## Troubleshooting

### Status checks not appearing?
- Ensure the CI workflow has run at least once on a branch
- Check workflow file syntax: `.github/workflows/ci.yml`
- Verify the check names match exactly (case-sensitive)

### Can't apply settings?
- Verify you have admin access to the repository
- Check your GitHub token has `repo` scope
- Try logging in again: `gh auth login`

### Need to bypass temporarily?
Repository admins can:
1. Temporarily disable specific rules in Settings → Branches
2. Merge the urgent change
3. Re-enable rules immediately after
4. Document the bypass in the PR description

## Next Steps

After setting up branch protection:

1. ✅ Test with a sample PR
2. ✅ Notify team members about the new workflow
3. ✅ Update internal documentation if needed
4. ✅ Monitor first few PRs to ensure smooth operation

## Support

- **Full documentation**: [.github/BRANCH_PROTECTION.md](.github/BRANCH_PROTECTION.md)
- **GitHub docs**: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches
- **Issues**: Open an issue in the repository if you encounter problems

---

Last updated: 2026-01-13
