# Branch Protection Configuration Guide

This document provides instructions for configuring branch protection rules for the skill-fleet repository to maintain code quality, security, and collaboration standards.

## Overview

Branch protection rules help maintain the integrity of the main branch by:
- Requiring code reviews before merging
- Ensuring all automated tests pass
- Preventing accidental force pushes or deletions
- Enforcing a consistent development workflow

## Recommended Branch Protection Rules for `main`

### Required Configuration

#### 1. Require Pull Request Reviews Before Merging
- **Setting**: Enable "Require a pull request before merging"
- **Required approving reviews**: 1 minimum
- **Dismiss stale pull request approvals when new commits are pushed**: Enabled
- **Require review from Code Owners**: Optional (enable if CODEOWNERS file exists)

**Rationale**: Ensures all code changes are reviewed by at least one other team member, catching potential bugs and maintaining code quality standards.

#### 2. Require Status Checks to Pass Before Merging
- **Setting**: Enable "Require status checks to pass before merging"
- **Require branches to be up to date before merging**: Enabled
- **Required status checks**:
  - `lint / Lint with Ruff`
  - `test / Run Tests (3.12)`
  - `test / Run Tests (3.13)`
  - `build / Build Verification`
  - `security / Security Checks`
  - `all-checks / All Checks Passed`

**Rationale**: Ensures all automated quality gates pass before code is merged, preventing broken code from entering the main branch.

#### 3. Require Conversation Resolution Before Merging
- **Setting**: Enable "Require conversation resolution before merging"

**Rationale**: Ensures all review comments and discussions are addressed before merging, preventing unresolved issues from being overlooked.

#### 4. Require Signed Commits
- **Setting**: Enable "Require signed commits" (optional but recommended)

**Rationale**: Verifies the authenticity of commits, adding an extra layer of security to ensure commits come from trusted sources.

#### 5. Require Linear History
- **Setting**: Enable "Require linear history"

**Rationale**: Maintains a clean, easy-to-follow commit history by preventing merge commits. Requires using rebase or squash merge strategies.

#### 6. Include Administrators
- **Setting**: Enable "Include administrators"

**Rationale**: Ensures even repository administrators follow the same rules, preventing accidental bypasses of important safeguards.

### Advanced Protection Rules

#### 7. Restrict Who Can Push to Matching Branches
- **Setting**: Enable "Restrict who can push to matching branches"
- **Allowed actors**: CI/CD service accounts only (if applicable)

**Rationale**: Prevents direct pushes to main, ensuring all changes go through pull requests.

#### 8. Prevent Force Pushes
- **Setting**: Enable "Do not allow bypassing the above settings"
- **Allow force pushes**: Disabled
- **Allow deletions**: Disabled

**Rationale**: Prevents rewriting history on the main branch, which could cause issues for other developers and lose important historical context.

## Configuration Methods

### Method 1: GitHub Web UI (Recommended for Initial Setup)

1. Navigate to your repository on GitHub
2. Go to **Settings** → **Branches**
3. Under "Branch protection rules", click **Add rule** or **Edit** if a rule already exists
4. In "Branch name pattern", enter: `main`
5. Configure the settings as outlined above
6. Click **Save changes**

### Method 2: GitHub CLI (`gh`)

```bash
# Install GitHub CLI if not already installed
# See: https://cli.github.com/

# Create branch protection rule
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/Qredence/skill-fleet/branches/main/protection \
  -f required_status_checks='{"strict":true,"contexts":["lint / Lint with Ruff","test / Run Tests (3.12)","test / Run Tests (3.13)","build / Build Verification","security / Security Checks","all-checks / All Checks Passed"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"dismiss_stale_reviews":true,"require_code_owner_reviews":false,"required_approving_review_count":1}' \
  -f restrictions=null \
  -f required_linear_history=true \
  -f allow_force_pushes=false \
  -f allow_deletions=false \
  -f block_creations=false \
  -f required_conversation_resolution=true \
  -f lock_branch=false \
  -f allow_fork_syncing=false
```

### Method 3: Using GitHub REST API

Save this as a JSON file (`branch-protection.json`):

```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "lint / Lint with Ruff",
      "test / Run Tests (3.12)",
      "test / Run Tests (3.13)",
      "build / Build Verification",
      "security / Security Checks",
      "all-checks / All Checks Passed"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": false
}
```

Then apply it using curl:

```bash
curl -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/Qredence/skill-fleet/branches/main/protection \
  -d @branch-protection.json
```

## Verifying Configuration

After configuring branch protection rules:

1. **Test with a Pull Request**: Create a test branch and PR to verify:
   - Status checks appear and run
   - Review approval is required
   - Merge is blocked until all conditions are met

2. **Check Settings**: Navigate to Settings → Branches and verify all rules are shown correctly

3. **Monitor First Few PRs**: Ensure the workflow works smoothly and adjust settings if needed

## CI/CD Workflow

The repository includes a CI workflow (`.github/workflows/ci.yml`) that provides the required status checks:

- **Lint**: Runs `ruff check` and `ruff format --check` to ensure code style compliance
- **Test**: Runs pytest on Python 3.12 and 3.13 to ensure compatibility
- **Build**: Verifies the package builds and CLI entrypoint works
- **Security**: Placeholder for security scanning (can be extended with tools like `pip-audit`)

## Maintenance

### Updating Status Checks

When adding or renaming jobs in the CI workflow:

1. Update the branch protection rule to include the new status check names
2. Ensure backward compatibility during transition (mark new checks as optional initially)
3. After a few PRs pass with the new checks, make them required

### Handling Emergency Situations

If an urgent fix is needed and CI is broken:

1. Repository administrators can temporarily disable specific rules
2. Merge the urgent fix
3. Immediately re-enable the rules
4. Create a follow-up PR to fix any quality issues

**Note**: This should be rare and documented in the PR description.

## Related Documentation

- [GitHub Docs: Managing Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)
- [GitHub Docs: About Protected Branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Contributing Guidelines](../docs/development/CONTRIBUTING.md)

## Support

For questions or issues with branch protection configuration, please:
1. Review this documentation
2. Check existing GitHub Issues
3. Contact the repository maintainers

## Changelog

- **2026-01-13**: Initial branch protection configuration guide created
- **Future**: Document will be updated as CI requirements evolve
