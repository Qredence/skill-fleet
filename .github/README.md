# GitHub Configuration

This directory contains GitHub-specific configuration files and documentation for the skill-fleet repository.

## Contents

### Branch Protection

- **[BRANCH_PROTECTION.md](BRANCH_PROTECTION.md)**: Comprehensive guide for configuring branch protection rules
- **[branch-protection-config.json](branch-protection-config.json)**: JSON template for API-based branch protection setup
- **[../scripts/setup_branch_protection.sh](../scripts/setup_branch_protection.sh)**: Interactive script for configuring branch protection

### Workflows

- **[workflows/ci.yml](workflows/ci.yml)**: Main CI workflow for linting, testing, and build verification
- **[workflows/copilot-setup-steps.yml](workflows/copilot-setup-steps.yml)**: Setup workflow for GitHub Copilot
- **[workflows/junie.yml](workflows/junie.yml)**: Junie AI agent workflow

### Instructions

- **[copilot-instructions.md](copilot-instructions.md)**: Detailed instructions for GitHub Copilot integration

## Quick Start: Setting Up Branch Protection

### Option 1: Using the Interactive Script (Recommended)

```bash
# Run the interactive setup script
./scripts/setup_branch_protection.sh
```

This script provides an interactive menu to:
- View current branch protection rules
- Apply recommended protection settings
- Verify the configuration

**Prerequisites**:
- GitHub CLI (`gh`) installed: https://cli.github.com/
- Authenticated with GitHub: `gh auth login`
- Repository admin access

### Option 2: Manual Setup via GitHub UI

1. Go to the repository on GitHub
2. Navigate to **Settings** → **Branches**
3. Click **Add rule** (or edit existing rule for `main`)
4. Follow the configuration guide in [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md)

### Option 3: Using GitHub API

```bash
# Using the JSON configuration file
curl -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/Qredence/skill-fleet/branches/main/protection \
  -d @.github/branch-protection-config.json
```

## CI/CD Status Checks

The CI workflow provides the following status checks required for branch protection:

| Check Name | Purpose | Configuration |
|------------|---------|---------------|
| `lint / Lint with Ruff` | Code style and quality checks | Runs `ruff check` and `ruff format --check` |
| `test / Run Tests (3.12)` | Python 3.12 compatibility tests | Runs pytest on Python 3.12 |
| `test / Run Tests (3.13)` | Python 3.13 compatibility tests | Runs pytest on Python 3.13 |
| `build / Build Verification` | Package build and CLI verification | Verifies package installs and CLI works |
| `security / Security Checks` | Security vulnerability scanning | Placeholder for security tools |
| `all-checks / All Checks Passed` | Final gate ensuring all checks pass | Meta-check that depends on all others |

## Recommended Branch Protection Settings

For the `main` branch, we recommend:

✅ **Require pull request reviews** (1 approval minimum)  
✅ **Require status checks to pass** (all CI checks listed above)  
✅ **Require conversation resolution**  
✅ **Require linear history** (no merge commits)  
✅ **Include administrators** (admins follow same rules)  
✅ **Block force pushes**  
✅ **Block deletions**  

See [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md) for detailed rationale and configuration instructions.

## Troubleshooting

### Status Checks Not Appearing

If status checks don't appear on a pull request:
1. Ensure the CI workflow has run at least once on the branch
2. Check that the workflow file is valid YAML
3. Verify the job names match exactly in branch protection settings

### CI Workflow Failures

Common issues and solutions:
- **Linting failures**: Run `uv run ruff check --fix .` and `uv run ruff format .` locally
- **Test failures**: Run `uv run pytest tests/unit/` locally to reproduce
- **Build failures**: Ensure dependencies are up to date with `uv sync --group dev`

### Unable to Apply Branch Protection

If you can't configure branch protection:
- Verify you have admin access to the repository
- Check that you're authenticated with sufficient permissions
- Try using a personal access token with `repo` scope

## Maintenance

### Updating Status Check Requirements

When modifying the CI workflow:

1. Update the workflow file: `.github/workflows/ci.yml`
2. Update the branch protection settings to match new job names
3. Update [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md) documentation
4. Update [branch-protection-config.json](branch-protection-config.json) template
5. Test on a development branch before applying to main

### Regular Reviews

Review branch protection settings:
- **Quarterly**: Ensure settings still align with team workflow
- **After major changes**: When CI/CD pipeline is modified
- **When adding team members**: Ensure proper permissions are set

## Additional Resources

- [GitHub Docs: About Protected Branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Docs: Managing Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)
- [GitHub REST API: Branch Protection](https://docs.github.com/en/rest/branches/branch-protection)
- [Repository Contributing Guidelines](../docs/development/CONTRIBUTING.md)

## Support

For questions or issues:
1. Check this documentation
2. Review [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md) for detailed guidance
3. Open an issue in the repository
4. Contact repository maintainers
