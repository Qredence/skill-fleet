# Claude Code Auto-Fix CI Failures Workflow

## Overview

This GitHub Actions workflow uses Claude Code to automatically diagnose and fix CI failures with intelligent retry logic. When your CI workflow fails, Claude analyzes the error logs and automatically fixes common issues like linting errors, type mismatches, test failures, and more.

**Features:**
- ✅ Automatic trigger on CI failures
- ✅ Manual trigger via workflow dispatch
- ✅ Up to 3 retry attempts for complex issues
- ✅ Direct push to branch (no PR creation)
- ✅ Automatic failure notifications
- ✅ Detailed logging and audit trail

## Files

### 1. `.github/workflows/claude-autofix.yml`
Simple single-attempt auto-fix workflow. Use this if you prefer straightforward, no-retry fixes.

**Triggers:**
- Automatically when the `CI` workflow fails
- Manually via `workflow_dispatch`

**Outputs:**
- Commits fixes directly to the failing branch
- Posts comment on PR (if exists) with status

### 2. `.github/workflows/claude-autofix-retry.yml`
Advanced retry-enabled auto-fix workflow. Use this for more complex issues that may need multiple fix attempts.

**Features:**
- Intelligent retry logic (up to 3 attempts)
- Tracks attempt number across retries
- Creates issue when max retries exceeded
- Detailed logging at each attempt
- Progress summary

**Recommended:** Use this version for production

## Setup

### Prerequisites

1. **GitHub Secrets** - Add to your repository settings:

   - `ANTHROPIC_API_KEY` (required)
     - Your Anthropic API key
     - [Get one here](https://console.anthropic.com/)
     - Go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

   - `ANTHROPIC_BASE_URL` (optional)
     - Use if you have a custom endpoint or proxy
     - Example: `https://api.example.com/v1`
     - Leave blank to use default Anthropic API

2. **Workflow File**
   - Choose either `claude-autofix.yml` (simple) or `claude-autofix-retry.yml` (advanced)
   - Copy the desired file to `.github/workflows/`
   - If using the retry version, remove `claude-autofix.yml` to avoid conflicts

### Installation Steps

```bash
# Option 1: Simple single-attempt version
curl -L https://github.com/Qredence/skill-fleet/raw/main/.github/workflows/claude-autofix.yml \
  -o .github/workflows/claude-autofix.yml

# Option 2: Advanced retry version (recommended)
curl -L https://github.com/Qredence/skill-fleet/raw/main/.github/workflows/claude-autofix-retry.yml \
  -o .github/workflows/claude-autofix-retry.yml
```

Or copy the YAML content directly from the workflow files above.

## Usage

### Automatic Trigger

The workflow automatically runs when the `CI` workflow fails:

```
CI Workflow Fails → Claude Auto-Fix Runs → Diagnoses issue → Fixes code → Pushes to branch → CI Re-runs
```

**Example scenario:**
1. You push a commit with a linting error
2. CI fails due to `ruff` formatting
3. Claude Auto-Fix automatically:
   - Analyzes the error logs
   - Identifies the linting violations
   - Runs `ruff check . --fix` and `ruff format .`
   - Commits and pushes the fixes
   - CI automatically re-runs and passes

### Manual Trigger

Manually trigger the workflow from the GitHub UI:

1. Go to **Actions** → **Claude Auto-Fix CI Failures** (or Claude Auto-Fix with Retry)
2. Click **Run workflow**
3. Fill in the optional inputs:
   - `run_id`: Failed workflow run ID (optional)
   - `branch`: Branch to fix (required if no run_id)
   - `attempt`: For retry version only (auto-filled)
4. Click **Run workflow**

**Via CLI:**
```bash
# Simple version
gh workflow run claude-autofix.yml -f branch=main

# Retry version with specific run
gh workflow run claude-autofix-retry.yml \
  -f run_id=1234567890 \
  -f branch=feature/my-changes \
  -f attempt=1
```

## How It Works

### Phase 1: Diagnosis
Claude analyzes the CI failure logs to identify:
- Error type (linting, types, tests, etc.)
- Affected files
- Root cause
- Required fixes

### Phase 2: Fixing
Claude applies targeted fixes:
- **Linting**: `uv run ruff check . --fix && uv run ruff format .`
- **Type errors**: Fixes type annotations
- **Test failures**: Fixes failing test code or dependencies
- **Security issues**: Addresses security scanning findings

### Phase 3: Verification
Claude verifies fixes by running the same checks that failed:
```bash
uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/
uv run ty check src/ tests/
uv run pytest tests/unit/ -v --tb=short
```

### Phase 4: Commit & Push
Claude commits and pushes changes:
- Commit message: `fix(ci): <description of what was fixed>`
- Direct push to the failing branch
- CI automatically re-triggers

### (Retry version only) Phase 5: Retry Logic
If CI still fails:
- Attempt counter increments
- Claude analyzes the new failure
- Repeats phases 1-4
- Maximum 3 attempts before requiring manual intervention

## Customization

### Modify Allowed Workflow Triggers

Edit the workflow file to trigger on different workflow failures:

```yaml
on:
  workflow_run:
    workflows: ["CI", "Tests", "Security Checks"]  # Add more workflows
    types: [completed]
```

### Change Maximum Retry Attempts

In `claude-autofix-retry.yml`, modify:

```yaml
env:
  MAX_ATTEMPTS: 5  # Change from 3 to 5 (or any number)
```

### Customize Claude's Tools

Modify the `claude_args` in the workflow to enable/disable tools:

```yaml
claude_args: |
  --max-turns 30
  --allowedTools Read,Write,Edit,Bash(uv:*),Bash(ruff:*),Bash(pytest:*)
  # Add or remove tools as needed
```

Available tools:
- `Read`, `Write`, `Edit` - File operations
- `Bash(*)` - Shell commands (scoped by prefix)
- `Bash(git:*)` - Git operations
- `Bash(uv:*)` - uv commands
- `Bash(ruff:*)` - Ruff linting
- `Bash(pytest:*)` - pytest testing

### Adjust Concurrency

Control how concurrent fix attempts run:

```yaml
concurrency:
  group: claude-autofix-${{ github.ref }}
  cancel-in-progress: true  # Set to false to allow all attempts to run
```

## Examples

### Scenario 1: Automatic Ruff Fix

```
Branch: feature/new-feature
Event: Push with linting errors
Result: Claude runs ruff --fix, commits, pushes
CI Re-run: PASS ✅
```

### Scenario 2: Type Error Fix with Retry

```
Attempt 1: Fixes type annotation in main module
  → CI re-runs, but reveals dependency issue
Attempt 2: Fixes the dependency version
  → CI re-runs, passes
Result: PASS ✅ (after 2 attempts)
```

### Scenario 3: Manual Trigger

```
Branch: bugfix/critical-issue
User: Manually triggers via GitHub UI
Claude: Analyzes recent failures
Result: Commits fix, pushes to branch
CI: Auto-runs, PASS ✅
```

## Troubleshooting

### "Failed to authenticate with Anthropic API"
- **Cause**: `ANTHROPIC_API_KEY` not set
- **Fix**: Add the secret to repository settings
- **Verify**: Go to **Settings** → **Secrets and variables** → **Actions** → confirm `ANTHROPIC_API_KEY` exists

### "No logs available"
- **Cause**: Workflow run ID inaccessible
- **Fix**: Ensure GitHub token has sufficient permissions (usually automatic)
- **Fallback**: Use manual trigger with branch name

### "Max retries exceeded"
- **Cause**: Claude couldn't fix the issue in 3 attempts
- **Next steps**:
  1. Review the CI logs manually
  2. Identify the root cause (may require human judgment)
  3. Create a manual fix and push
  4. Re-trigger Claude if needed

### Workflow doesn't trigger
- **Check**: Is the CI workflow named exactly `CI`? Edit the `workflows:` section if different
- **Check**: Are you pushing to a branch that has the workflow enabled?
- **Check**: Are there any branch protection rules preventing auto-commits?

### Claude makes unwanted changes
- **Cause**: Prompt was too broad or allowed too many tools
- **Fix**: Edit `claude_args` to restrict tools, reduce `--max-turns`
- **Emergency**: Delete the workflow file temporarily to stop execution

## Security Considerations

### Permissions
The workflow uses minimal required permissions:
- `contents: write` - Push fixes to branches
- `pull-requests: write` - Comment on PRs
- `actions: read` - Read workflow logs
- `checks: write` - Update check status
- `id-token: write` - For OIDC authentication

### Safety Features
1. **Scoped tools** - Claude can only use tools specified in `claude_args`
2. **Read-only logs** - Claude reads failure logs, doesn't modify them
3. **Audit trail** - All commits have clear messages and attribution
4. **No force-push** - Safe git operations only
5. **Failure notifications** - Issues created when retries exhausted

### Secret Management
- **API Key**: Never commit to repo, use GitHub Secrets
- **Base URL**: Optional, useful for proxies but handle carefully
- **Token**: Uses GitHub's built-in `GITHUB_TOKEN` automatically

## Monitoring

### Workflow Runs
Monitor auto-fix attempts in **Actions** tab:
- **Claude Auto-Fix CI Failures** - Simple version
- **Claude Auto-Fix with Retry** - Retry version

Each run shows:
- Status (success/failure)
- Attempt number (retry version)
- Commits made
- Logs from Claude analysis

### View Logs
1. Go to **Actions** → workflow run
2. Click on the **Auto-Fix** job
3. Expand **Claude Code Auto-Fix** step
4. Review Claude's analysis and actions

### Create Alerts
Set up notifications for:
- Workflow failures (go back to manual review)
- New issues created (max retries exceeded)
- Branches with multiple fix attempts

## FAQ

**Q: Will Claude create a pull request?**
A: No, Claude pushes directly to the branch. You can create a PR manually or it can update an existing PR.

**Q: Can I exclude certain files from auto-fix?**
A: Yes, modify the prompt in `claude_args` to focus only on specific directories.

**Q: What if the auto-fix breaks something?**
A: GitHub's branch protection rules and code review requirements are still in place. You can require manual review before merge.

**Q: How much does this cost?**
A: Claude API charges per token. Typical CI fixes use 5-50K tokens (~$0.01-0.15). See [Anthropic pricing](https://www.anthropic.com/pricing).

**Q: Can I use this on multiple branches?**
A: Yes, the workflow runs on any branch where CI fails. No configuration needed.

**Q: What if Claude can't fix the issue?**
A: The workflow includes detailed error logging. If CI still fails after 3 attempts, an issue is created for manual review.

## Best Practices

1. **Start with simple version** - Use `claude-autofix.yml` first, upgrade to retry version if needed
2. **Monitor first run** - Review the first few auto-fix attempts to ensure quality
3. **Review commits** - Check commits in history to understand what Claude fixed
4. **Set limits** - Use `--max-turns` to prevent excessive analysis
5. **Restrict tools** - Only enable tools Claude actually needs
6. **Test locally** - Verify fixes pass locally before merging
7. **Keep secrets secure** - Never commit API keys or base URLs

## Advanced Configuration

### Environment Variable Support

Add custom environment variables via GitHub Secrets and reference in the workflow:

```yaml
env:
  CUSTOM_VAR: ${{ secrets.CUSTOM_VAR }}
```

### Integration with Other Tools

Combine with other workflows:

```yaml
# Trigger security scan after successful auto-fix
- name: Run security scan
  if: success()
  run: npm audit
```

### Custom Claude Model

Specify a different model:

```yaml
claude_args: |
  --max-turns 20
  --model claude-opus  # Use different model if desired
```

## Support

For issues or questions:
1. Check the **Troubleshooting** section above
2. Review Claude Code Action docs: https://github.com/anthropics/claude-code-action
3. Check your repo's CI logs for specific errors
4. Open a GitHub issue in this repository

## License

This workflow is part of the Skill Fleet project and follows the same license (MIT).
