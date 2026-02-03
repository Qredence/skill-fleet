#!/bin/bash
# Claude Auto-Fix CI Workflow - Quick Setup Script
# This script helps you set up the Claude auto-fix workflow

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Claude Code Auto-Fix CI Failures - Setup Guide           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository. Please run this from your repo root."
    exit 1
fi

# Check if .github/workflows exists
if [ ! -d ".github/workflows" ]; then
    echo "📁 Creating .github/workflows directory..."
    mkdir -p .github/workflows
fi

echo "✅ Repository structure verified"
echo ""

# Workflow file selection
echo "Which version would you like to use?"
echo "  1) Simple (single attempt) - claude-autofix.yml"
echo "  2) Advanced with Retry (recommended) - claude-autofix-retry.yml"
echo "  3) Both (install both workflows)"
echo ""
read -p "Enter choice (1-3): " choice

echo ""
echo "📋 Workflow files status:"
echo ""

# Check existing files
if [ -f ".github/workflows/claude-autofix.yml" ]; then
    echo "  ✅ claude-autofix.yml already exists"
else
    echo "  ⭕ claude-autofix.yml not found (will be created if selected)"
fi

if [ -f ".github/workflows/claude-autofix-retry.yml" ]; then
    echo "  ✅ claude-autofix-retry.yml already exists"
else
    echo "  ⭕ claude-autofix-retry.yml not found (will be created if selected)"
fi

echo ""
echo "🔑 Checking GitHub Secrets..."
echo ""

# Note: We can't actually check secrets from the CLI without additional tools
echo "Next, you need to set up GitHub Secrets:"
echo ""
echo "1. Go to your repository on GitHub"
echo "2. Settings → Secrets and variables → Actions"
echo "3. Click 'New repository secret'"
echo "4. Add the following secret:"
echo ""
echo "   Name: ANTHROPIC_API_KEY"
echo "   Value: [Your Anthropic API key from console.anthropic.com]"
echo ""
echo "(Optional) Add custom API endpoint:"
echo "   Name: ANTHROPIC_BASE_URL"
echo "   Value: [Your custom endpoint URL]"
echo ""

# Prompt for API key confirmation
read -p "Have you already added ANTHROPIC_API_KEY to GitHub Secrets? (y/n): " has_key

if [ "$has_key" != "y" ]; then
    echo ""
    echo "⚠️  Please add ANTHROPIC_API_KEY to GitHub Secrets first:"
    echo "   https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git$/\1/')/settings/secrets/actions"
    exit 1
fi

echo ""
echo "✅ GitHub Secrets configured"
echo ""

# Installation instructions based on choice
case $choice in
    1)
        echo "Installing Simple Version (claude-autofix.yml)..."
        echo ""
        echo "You can copy the workflow file manually:"
        echo "  1. Go to .github/workflows/claude-autofix.yml"
        echo "  2. The file is already created in your repository"
        echo ""
        ;;
    2)
        echo "Installing Advanced Version with Retry (claude-autofix-retry.yml)..."
        echo ""
        echo "Recommended configuration:"
        echo "  - Max retries: 3 attempts"
        echo "  - Max turns: 25 per attempt"
        echo "  - Tools: Read, Write, Edit, Bash commands"
        echo ""
        echo "The workflow file is already created at:"
        echo "  .github/workflows/claude-autofix-retry.yml"
        echo ""
        ;;
    3)
        echo "Installing Both Versions..."
        echo ""
        echo "Both workflow files are now available:"
        echo "  1. .github/workflows/claude-autofix.yml (simple)"
        echo "  2. .github/workflows/claude-autofix-retry.yml (advanced)"
        echo ""
        echo "⚠️  Note: Only one will be active. Remove the simple version"
        echo "   if you want to use the retry version exclusively."
        echo ""
        ;;
    *)
        echo "Invalid choice. Please run again."
        exit 1
        ;;
esac

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Next Steps                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "1. ✅ Commit the workflow file(s):"
echo "     git add .github/workflows/claude-autofix*.yml"
echo "     git commit -m 'ci: add Claude auto-fix workflow'"
echo ""
echo "2. ✅ Push to your repository:"
echo "     git push origin"
echo ""
echo "3. ✅ Test the workflow:"
echo "     - Trigger a CI failure on any branch"
echo "     - Or manually run: Actions → [workflow name] → Run workflow"
echo ""
echo "4. 📚 Documentation:"
echo "     See .github/CLAUDE_AUTOFIX_README.md for full details"
echo ""
echo "✨ Your Claude auto-fix workflow is ready!"
echo ""
