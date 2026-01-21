#!/usr/bin/env bash

# Branch Protection Configuration Script
# This script helps configure branch protection rules for the skill-fleet repository
# Requires: GitHub CLI (gh) or GitHub Personal Access Token

set -e

REPO_OWNER="Qredence"
REPO_NAME="skill-fleet"
BRANCH_NAME="main"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if gh CLI is installed
check_gh_cli() {
    if command -v gh &> /dev/null; then
        print_info "GitHub CLI (gh) is installed"
        return 0
    else
        print_warning "GitHub CLI (gh) is not installed"
        return 1
    fi
}

# Check if authenticated with GitHub
check_gh_auth() {
    if gh auth status &> /dev/null; then
        print_info "Authenticated with GitHub"
        return 0
    else
        print_error "Not authenticated with GitHub. Run: gh auth login"
        return 1
    fi
}

# Display current branch protection rules
show_current_rules() {
    print_info "Fetching current branch protection rules for '${BRANCH_NAME}'..."
    
    if gh api "repos/${REPO_OWNER}/${REPO_NAME}/branches/${BRANCH_NAME}/protection" 2>/dev/null; then
        print_info "Current rules retrieved successfully"
    else
        print_warning "No existing branch protection rules found or unable to retrieve them"
    fi
}

# Apply branch protection rules
apply_protection_rules() {
    print_info "Applying branch protection rules to '${BRANCH_NAME}'..."
    
    # Create the protection rule using gh CLI
    gh api \
        --method PUT \
        -H "Accept: application/vnd.github+json" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        "repos/${REPO_OWNER}/${REPO_NAME}/branches/${BRANCH_NAME}/protection" \
        -f required_status_checks[strict]=true \
        -f required_status_checks[contexts][]='lint / Lint with Ruff' \
        -f required_status_checks[contexts][]='test / Run Tests (3.12)' \
        -f required_status_checks[contexts][]='test / Run Tests (3.13)' \
        -f required_status_checks[contexts][]='build / Build Verification' \
        -f required_status_checks[contexts][]='security / Security Checks' \
        -f required_status_checks[contexts][]='all-checks / All Checks Passed' \
        -F enforce_admins=true \
        -f required_pull_request_reviews[dismiss_stale_reviews]=true \
        -f required_pull_request_reviews[require_code_owner_reviews]=false \
        -f required_pull_request_reviews[required_approving_review_count]=1 \
        -f required_pull_request_reviews[require_last_push_approval]=false \
        -F required_linear_history=true \
        -F allow_force_pushes=false \
        -F allow_deletions=false \
        -F block_creations=false \
        -F required_conversation_resolution=true \
        -F lock_branch=false \
        -F allow_fork_syncing=false
    
    if [ $? -eq 0 ]; then
        print_info "Branch protection rules applied successfully!"
    else
        print_error "Failed to apply branch protection rules"
        return 1
    fi
}

# Verify the configuration
verify_configuration() {
    print_info "Verifying branch protection configuration..."
    
    # Get the current protection rules
    PROTECTION_DATA=$(gh api "repos/${REPO_OWNER}/${REPO_NAME}/branches/${BRANCH_NAME}/protection" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        print_info "✓ Branch protection is enabled"
        
        # Check for required status checks
        if echo "$PROTECTION_DATA" | grep -q "required_status_checks"; then
            print_info "✓ Required status checks are configured"
        fi
        
        # Check for PR reviews
        if echo "$PROTECTION_DATA" | grep -q "required_pull_request_reviews"; then
            print_info "✓ Pull request reviews are required"
        fi
        
        # Check for linear history
        if echo "$PROTECTION_DATA" | grep -q "\"required_linear_history\""; then
            print_info "✓ Linear history is enforced"
        fi
        
        print_info "Configuration verification complete!"
    else
        print_error "Unable to verify configuration"
        return 1
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "================================"
    echo "Branch Protection Configuration"
    echo "================================"
    echo "Repository: ${REPO_OWNER}/${REPO_NAME}"
    echo "Branch: ${BRANCH_NAME}"
    echo ""
    echo "1. Show current protection rules"
    echo "2. Apply recommended protection rules"
    echo "3. Verify configuration"
    echo "4. Exit"
    echo ""
    read -p "Select an option (1-4): " choice
    
    case $choice in
        1)
            show_current_rules
            show_menu
            ;;
        2)
            apply_protection_rules
            show_menu
            ;;
        3)
            verify_configuration
            show_menu
            ;;
        4)
            print_info "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid option. Please select 1-4."
            show_menu
            ;;
    esac
}

# Main script execution
main() {
    echo "========================================"
    echo "Skill Fleet - Branch Protection Setup"
    echo "========================================"
    echo ""
    
    # Check prerequisites
    if ! check_gh_cli; then
        print_error "Please install GitHub CLI: https://cli.github.com/"
        exit 1
    fi
    
    if ! check_gh_auth; then
        print_error "Please authenticate with GitHub: gh auth login"
        exit 1
    fi
    
    # Check if user has admin access
    print_info "Checking repository access..."
    if gh api "repos/${REPO_OWNER}/${REPO_NAME}" &> /dev/null; then
        print_info "Repository access confirmed"
    else
        print_error "Unable to access repository. Check your permissions."
        exit 1
    fi
    
    # Show interactive menu
    show_menu
}

# Run main function
main
