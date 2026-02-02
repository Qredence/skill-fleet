# Claude Auto-Fix CI Failures - Setup Instructions

Complete setup guide for the Claude Code Auto-Fix CI workflow.

## Quick Start (5 minutes)

### Step 1: Add GitHub Secrets

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the secret:
   ```
   Name: ANTHROPIC_API_KEY
   Value: sk-ant-... (your API key)
   ```
5. Click **Add secret**

**Optional:** Add custom API endpoint
   ```
   Name: ANTHROPIC_BASE_URL
   Value: https://api.example.com/v1
   ```

### Step 2: Workflows are Already Installed

The workflow files are already in your repository:
- `.github/workflows/claude-autofix.yml` - Simple single-attempt version
- `.github/workflows/claude-autofix-retry.yml` - Advanced retry version (recommended)

### Step 3: Test the Workflow

#### Method A: Automatic (Easiest)
1. Make a commit that causes CI to fail (e.g., a linting error)
2. Push to your branch
3. Watch the workflow automatically trigger and fix it

#### Method B: Manual Trigger
1. Go to **Actions** tab
2. Select **Claude Auto-Fix CI Failures** or **Claude Auto-Fix with Retry**
3. Click **Run workflow**
4. Fill in optional parameters (branch name)
5. Click **Run workflow**

#### Method C: Command Line
```bash
# Run on current branch
gh workflow run claude-autofix.yml -f branch=$(git branch --show-current)

# Run with specific run ID (from failed CI)
gh workflow run claude-autofix-retry.yml -f run_id=1234567890
```

---

## Detailed Setup

### Prerequisites

- **GitHub Repository Admin Access** - To add secrets
- **Anthropic API Key** - Get one at https://console.anthropic.com/
- **GitHub CLI** (optional) - For command-line triggers

### Step-by-Step Setup

#### 1. Create Anthropic API Key

1. Go to https://console.anthropic.com/
2. Log in with your Anthropic account (create one if needed)
3. Navigate to **API Keys** section
4. Click **Create Key**
5. Name it something like "GitHub Actions"
6. Copy the key (starts with `sk-ant-`)
7. Keep it secret! Don't commit it to the repo.

#### 2. Add Secret to GitHub

**Via Web UI:**
1. Open your repository on github.com
2. Go to **Settings** (repository settings, not profile)
3. Click **Secrets and variables** in the left sidebar
4. Click **Actions**
5. Click **New repository secret**
6. Fill in:
   - **Name:** `ANTHROPIC_API_KEY`
   - **Secret:** Paste your API key from Step 1
7. Click **Add secret**

**Via GitHub CLI:**
```bash
# Set the secret interactively (paste when prompted)
gh secret set ANTHROPIC_API_KEY

# Or provide the value
gh secret set ANTHROPIC_API_KEY --body "sk-ant-..."
```

**Via Environment Variable (Linux/Mac):**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
gh secret set ANTHROPIC_API_KEY --body "$ANTHROPIC_API_KEY"
```

#### 3. (Optional) Add Custom Base URL

If you're using a proxy or custom Anthropic endpoint:

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Fill in:
   - **Name:** `ANTHROPIC_BASE_URL`
   - **Secret:** Your custom endpoint (e.g., `https://api.example.com/v1`)
4. Click **Add secret**

#### 4. Choose Your Workflow Version

**Simple Version (claude-autofix.yml):**
- ✅ Single fix attempt
- ✅ Fast, straightforward
- ✅ No retry logic
- 👉 Use for: Simple linting/formatting fixes

**Retry Version (claude-autofix-retry.yml):** ← Recommended
- ✅ Up to 3 retry attempts
- ✅ Better for complex issues
- ✅ Automatic failure notifications
- 👉 Use for: Any CI failure that needs investigation

**Recommendation:** Use the retry version for production. It's more robust and handles edge cases better.

#### 5. Verify Installation

```bash
# Check both workflow files exist
ls -la .github/workflows/claude-autofix*.yml

# Expected output:
# .github/workflows/claude-autofix.yml (9K)
# .github/workflows/claude-autofix-retry.yml (15K)

# Check they're valid YAML
cat .github/workflows/claude-autofix.yml | head -20
```

#### 6. Configure Workflow (Optional)

Edit `.github/workflows/claude-autofix-retry.yml` to customize:

**Increase max retry attempts:**
```yaml
env:
  MAX_ATTEMPTS: 5  # Change from 3 to 5
```

**Add more workflow triggers:**
```yaml
on:
  workflow_run:
    workflows: ["CI", "Tests", "Security Checks"]  # Add more
    types: [completed]
```

**Restrict Claude's tools (security):**
```yaml
claude_args: |
  --max-turns 15  # Reduce from 25
  --allowedTools Read,Bash(ruff:*),Bash(pytest:*)  # Only specific tools
```

---

## First Test Run

### Test Scenario: Fix a Linting Error

1. Create a new branch:
   ```bash
   git checkout -b test/claude-autofix
   ```

2. Introduce a linting error in a Python file:
   ```python
   # src/skill_fleet/example.py
   def hello(  ):  # Extra spaces - violates ruff rules
       x=1  # Missing spaces - linting error
       return x
   ```

3. Push and trigger CI:
   ```bash
   git add .
   git commit -m "test: introduce linting error"
   git push origin test/claude-autofix
   ```

4. Wait for CI to fail (~2-3 minutes)

5. Watch Claude Auto-Fix trigger:
   - Go to **Actions** tab
   - Look for **Claude Auto-Fix CI Failures** or **Claude Auto-Fix with Retry**
   - Watch the workflow run in real-time

6. Results:
   - ✅ Claude fixes the linting errors
   - ✅ Commits and pushes fixes
   - ✅ CI automatically re-runs
   - ✅ CI passes

---

## Workflow Behavior

### Automatic Trigger Flow

```
1. You push code to any branch
                    ↓
2. CI workflow runs
                    ↓
3. CI fails
                    ↓
4. Claude Auto-Fix automatically triggers
                    ↓
5. Claude analyzes logs and fixes code
                    ↓
6. Claude commits and pushes fixes
                    ↓
7. CI automatically re-runs (triggered by push)
                    ↓
8. CI passes ✅
```

### What Claude Can Fix

**Automatic fixes:**
- ✅ Ruff linting errors (`ruff check . --fix`)
- ✅ Ruff formatting issues (`ruff format .`)
- ✅ Type annotation errors (fixes code to match `ty` requirements)
- ✅ Simple test failures (fixes test code or dependencies)
- ✅ Security scanning issues (addresses bandit/safety findings)

**Requires manual intervention:**
- ❌ Complex architectural issues
- ❌ Missing external dependencies
- ❌ Configuration issues in external services
- ❌ Issues requiring human judgment/decision

---

## Monitoring & Logging

### View Workflow Runs

1. Go to your repository
2. Click **Actions** tab
3. Select the workflow:
   - **Claude Auto-Fix CI Failures** (simple version)
   - **Claude Auto-Fix with Retry** (retry version)
4. Click on a run to view details

### View Claude's Analysis

1. Click on the workflow run
2. Expand the **Auto-Fix** or **Auto-Fix (Attempt X)** job
3. Expand the **Claude Code Auto-Fix** step
4. Scroll through the logs to see:
   - How Claude analyzed the error
   - What fixes it attempted
   - Commands it ran
   - Files it modified

### Check Commits

```bash
# See commits made by Claude
git log --author="github-actions" --oneline

# See what Claude changed
git log -p --author="github-actions" | head -100
```

---

## Troubleshooting

### Issue: "Failed to authenticate with Anthropic API"

**Cause:** `ANTHROPIC_API_KEY` secret not set or invalid

**Fix:**
1. Verify the secret exists: **Settings** → **Secrets and variables** → **Actions**
2. Verify the secret value is correct (should start with `sk-ant-`)
3. Try regenerating the API key at console.anthropic.com

**Verify:**
```bash
# Check secret exists (no value shown for security)
gh secret list | grep ANTHROPIC_API_KEY
```

### Issue: "Workflow doesn't trigger on CI failure"

**Cause:** Workflow name doesn't match, or CI workflow has different name

**Fix:**
1. Find the exact name of your CI workflow:
   ```bash
   gh workflow list
   ```

2. Update the workflow file to match:
   ```yaml
   on:
     workflow_run:
       workflows: ["Your CI Workflow Name"]  # Match exactly
       types: [completed]
   ```

3. Commit and push the changes

### Issue: "No logs available" when triggering manually

**Cause:** Run ID not accessible or GitHub token lacks permissions

**Fix:**
- Provide the branch name instead of run ID:
  ```bash
  gh workflow run claude-autofix.yml -f branch=main
  ```

- Or get the run ID from failed CI:
  1. Go to **Actions** tab
  2. Find the failed CI run
  3. Copy the run ID from the URL or details
  4. Use it in the manual trigger

### Issue: "Max retries exceeded" (Retry version)

**Cause:** Claude couldn't fix the issue in 3 attempts

**Solution:**
1. Go to **Issues** tab - a new issue should be created
2. Review the issue for context
3. Investigate manually:
   - Look at the CI logs
   - Identify the root cause
   - Create a manual fix
   - Push the fix to trigger CI again

4. The issue likely requires:
   - Human judgment/decision
   - External configuration changes
   - Architecture modifications
   - Multiple independent fixes

### Issue: Unwanted file changes

**Cause:** Claude made changes you didn't want

**Fix:**
1. Review the commit: `git show <commit-hash>`
2. Revert if needed: `git revert <commit-hash>`
3. Edit the workflow prompt to be more specific about what to fix
4. Or remove/disable the workflow temporarily: `rm .github/workflows/claude-autofix.yml`

---

## Security Best Practices

### 1. Keep API Key Secure

- ✅ Store only in GitHub Secrets
- ✅ Never commit to repository
- ✅ Rotate key periodically
- ❌ Don't share in Slack/Discord
- ❌ Don't put in commit messages

### 2. Limit Workflow Permissions

The workflow only requests necessary permissions:
```yaml
permissions:
  contents: write      # Push fixes
  pull-requests: write # Comment on PRs
  actions: read        # Read workflow logs
  checks: write        # Update checks
  id-token: write      # OIDC auth
```

### 3. Restrict Claude's Tools

Edit the workflow to limit what Claude can do:
```yaml
claude_args: |
  --allowedTools Read,Bash(ruff:*),Bash(pytest:*)  # Only these tools
```

### 4. Use Branch Protection Rules

Set up branch protection to require review even for auto-fixes:
1. Go to **Settings** → **Branches**
2. Create rule for main branch
3. Enable **Require pull request reviews**
4. Claude's commits will be treated as regular commits

### 5. Audit Commits

Regularly review what Claude commits:
```bash
# List all Claude commits
git log --author="github-actions" --oneline --all

# Review specific commit
git show <commit-hash>
```

---

## Advanced Configuration

### Use Different Model

Edit the workflow to use a specific Claude model:
```yaml
claude_args: |
  --max-turns 20
  --model claude-opus-4  # Specify model
```

### Custom System Prompt

Add a system prompt to guide Claude:
```yaml
claude_args: |
  --system-prompt "You are a Python expert. Focus on fixing type errors and linting issues."
  --max-turns 20
```

### Disable Auto-Trigger

To use only manual triggers, comment out `workflow_run`:
```yaml
on:
  # workflow_run:  # Commented out
  #   workflows: ["CI"]
  #   types: [completed]

  workflow_dispatch:
    inputs:
      branch:
        required: true
        type: string
```

### Integration with Other Tools

Combine with other workflows:
```yaml
# In your CI workflow
- name: Run after auto-fix
  if: github.event.workflow_run.conclusion == 'success'
  run: echo "CI passed after auto-fix!"
```

---

## FAQ

**Q: How much will this cost?**
A: Claude API charges per token. Typical fixes use 5-50K tokens. At current pricing (~$0.01 per 1K tokens), expect ~$0.05-0.50 per fix.

**Q: Can I use this on multiple repositories?**
A: Yes, add the workflow to any repository. Set up secrets for each repo.

**Q: Will Claude create pull requests?**
A: No, Claude pushes directly to the branch. You can use branch protection rules to require review before merge.

**Q: What if Claude breaks something?**
A: All changes are committed with clear messages. You can review and revert:
```bash
git log --author="github-actions"
git revert <commit-hash>  # Undo Claude's changes
```

**Q: Can I exclude certain files?**
A: Yes, modify the prompt in the workflow to exclude specific paths.

**Q: How do I disable this workflow?**
A: Delete or rename the workflow file:
```bash
rm .github/workflows/claude-autofix.yml
git push origin
```

---

## Support & Resources

### Official Documentation
- Claude Code Action: https://github.com/anthropics/claude-code-action
- Anthropic API: https://docs.anthropic.com/
- GitHub Actions: https://docs.github.com/en/actions

### Troubleshooting
1. Check workflow logs in **Actions** tab
2. Review Claude's analysis in the **Claude Code Auto-Fix** step
3. Verify secrets are configured correctly
4. Check if API key has sufficient usage quota

### Getting Help
- Report issues in your repository's **Issues** tab
- Check Claude Code Action issues: https://github.com/anthropics/claude-code-action/issues
- Review this guide's FAQ section

---

## Next Steps

1. ✅ Add `ANTHROPIC_API_KEY` secret to GitHub
2. ✅ Verify workflow files are in `.github/workflows/`
3. ✅ Test with a real CI failure
4. ✅ Review and monitor the first few auto-fixes
5. ✅ Adjust workflow settings as needed
6. ✅ Share with your team!

**You're all set!** Your Claude auto-fix workflow is ready to help keep your CI passing. 🚀
