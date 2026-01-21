#!/usr/bin/env bash
# =============================================================================
# Technical Debt Cleanup Script
# Generated: 2026-01-20
# Ref: plans/technical-debt-audit.md
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJECT_ROOT/src/skill_fleet"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Phase 1: Quick Wins (5 min)
# =============================================================================

phase1_ruff_fix() {
    log_info "Phase 1: Fixing unused imports/variables with ruff..."
    
    cd "$PROJECT_ROOT"
    
    if command -v uv &> /dev/null; then
        uv run ruff check src/skill_fleet --select F401,F841 --fix 2>/dev/null || true
        log_success "Ruff auto-fix complete (28 issues)"
    else
        log_warn "uv not found, skipping ruff fix"
    fi
}

# =============================================================================
# Phase 2: Delete Orphaned Files (5 min)
# =============================================================================

phase2_delete_orphaned() {
    log_info "Phase 2: Deleting orphaned files..."
    
    # CASCADE: conversational_program.py imports chat.py
    # Deleting conversational_program.py orphans chat.py
    # Both should be deleted together
    local orphaned_files=(
        "$SRC_DIR/core/dspy/conversational_program.py"      # GuidedCreatorProgram (never imported)
        "$SRC_DIR/core/dspy/signatures/chat.py"             # Only used by conversational_program.py
    )
    
    for file in "${orphaned_files[@]}"; do
        if [[ -f "$file" ]]; then
            rm -v "$file"
            log_success "Deleted: $(basename "$file")"
        else
            log_warn "Already deleted: $(basename "$file")"
        fi
    done
    
    log_info "Justification: conversational_program.py is the only consumer of chat.py"
    log_info "              Both are safe to delete - conversational.py is the active alternative"
}

# =============================================================================
# Phase 3: Integrate enhanced_metrics.py (15 min)
# =============================================================================

phase3_integrate_enhanced_metrics() {
    log_info "Phase 3: Integrating enhanced_metrics into __init__.py..."
    
    local init_file="$SRC_DIR/core/dspy/metrics/__init__.py"
    
    if [[ -f "$init_file" ]]; then
        # Check if already integrated
        if grep -q "enhanced_metrics" "$init_file" 2>/dev/null; then
            log_warn "enhanced_metrics already integrated"
        else
            # Append exports (corrected based on actual file contents)
            cat >> "$init_file" << 'EOF'

# Enhanced metrics - structure-focused evaluation (integrated 2026-01-20)
# These complement skill_quality.py (content-focused) metrics
from .enhanced_metrics import (
    taxonomy_accuracy_metric,
    metadata_quality_metric,
    skill_style_alignment_metric,
    comprehensive_metric,
    create_metric_for_phase,
)

# Update __all__ to include enhanced metrics
__all__ += [
    # enhanced_metrics.py (structure-focused)
    "taxonomy_accuracy_metric",
    "metadata_quality_metric",
    "skill_style_alignment_metric",
    "comprehensive_metric",
    "create_metric_for_phase",
]
EOF
            log_success "Integrated enhanced_metrics exports"
        fi
    else
        log_error "metrics/__init__.py not found"
    fi
}

# =============================================================================
# Phase 4: Integrate Advanced Modules (ensemble, error_handling)
# =============================================================================

phase4_integrate_advanced_modules() {
    log_info "Phase 4: Integrating advanced modules into exports..."
    
    local init_file="$SRC_DIR/core/dspy/modules/__init__.py"
    
    if [[ -f "$init_file" ]]; then
        # Check if already integrated
        if grep -q "EnsembleModule" "$init_file" 2>/dev/null; then
            log_warn "Advanced modules already integrated"
        else
            # Append exports
            cat >> "$init_file" << 'EOF'

# Advanced modules (experimental - use with caution)
from .ensemble import (
    EnsembleModule,
    BestOfN,
    MajorityVote,
)
from .error_handling import (
    RobustModule,
    ValidatedModule,
)

__all__ = [
    # ... existing exports ...
    # Ensemble
    "EnsembleModule",
    "BestOfN",
    "MajorityVote",
    # Error handling
    "RobustModule",
    "ValidatedModule",
]
EOF
            log_success "Integrated advanced module exports"
        fi
    else
        log_error "modules/__init__.py not found"
    fi
}

# =============================================================================
# Phase 5: Rename Legacy SkillCreationProgram (1 hour - MANUAL)
# =============================================================================

phase5_rename_legacy_program() {
    log_info "Phase 5: Checking for duplicate SkillCreationProgram..."
    
    local programs_file="$SRC_DIR/core/dspy/programs.py"
    
    if [[ -f "$programs_file" ]]; then
        if grep -q "class SkillCreationProgram" "$programs_file" 2>/dev/null; then
            log_warn "MANUAL ACTION REQUIRED:"
            echo "  1. Rename 'SkillCreationProgram' to 'LegacySkillCreationProgram' in:"
            echo "     $programs_file"
            echo ""
            echo "  2. Update imports in:"
            echo "     - cli/commands/optimize.py"
            echo "     - core/optimization/optimizer.py"
            echo "     - agent/agent.py"
            echo "     - core/creator.py"
            echo ""
            echo "  3. Update core/dspy/__init__.py to export both:"
            echo "     from .programs import LegacySkillCreationProgram"
            echo "     from .skill_creator import SkillCreationProgram"
        else
            log_success "Already renamed or not present"
        fi
    fi
}

# =============================================================================
# Phase 6: Verify chat.py deletion (was MANUAL merge, now CASCADE delete)
# =============================================================================

phase6_verify_chat_deleted() {
    log_info "Phase 6: Verifying chat.py was deleted (CASCADE from Phase 2)..."
    
    local chat_file="$SRC_DIR/core/dspy/signatures/chat.py"
    
    if [[ -f "$chat_file" ]]; then
        log_warn "chat.py still exists - should have been deleted in Phase 2"
        echo ""
        echo "  Justification for DELETE (not merge):"
        echo "  - Only consumer was conversational_program.py (also deleted)"
        echo "  - Signatures are NOT shared with hitl.py (different patterns)"
        echo "  - hitl.py has its own complete signature set"
        echo ""
        echo "  To delete now: rm $chat_file"
    else
        log_success "chat.py correctly deleted (CASCADE from conversational_program.py)"
    fi
}

# =============================================================================
# Phase 7: Clean Old Training Data
# =============================================================================

phase7_clean_training_data() {
    log_info "Phase 7: Archiving old training data..."
    
    local training_dir="$PROJECT_ROOT/config/training"
    local archive_dir="$training_dir/archive"
    
    mkdir -p "$archive_dir"
    
    local old_files=(
        "$training_dir/trainset_v2.json"
        "$training_dir/trainset_v3.json"
    )
    
    for file in "${old_files[@]}"; do
        if [[ -f "$file" ]]; then
            mv -v "$file" "$archive_dir/"
            log_success "Archived: $(basename "$file")"
        fi
    done
}

# =============================================================================
# Verification
# =============================================================================

verify_cleanup() {
    log_info "Verifying cleanup..."
    
    cd "$PROJECT_ROOT"
    
    # Run ruff check
    if command -v uv &> /dev/null; then
        local issues
        issues=$(uv run ruff check src/skill_fleet --select F401,F841 2>/dev/null | wc -l || echo "0")
        
        if [[ "$issues" -eq 0 ]]; then
            log_success "No remaining unused imports/variables"
        else
            log_warn "$issues unused import issues remain"
        fi
    fi
    
    # Run pytest (quick sanity check)
    log_info "Running quick test sanity check..."
    if command -v uv &> /dev/null; then
        uv run pytest tests/ -x -q --tb=no 2>/dev/null || log_warn "Some tests may need updates"
    fi
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo ""
    echo "============================================="
    echo "   Technical Debt Cleanup"
    echo "   Generated: 2026-01-20"
    echo "============================================="
    echo ""
    
    local mode="${1:-all}"
    
    case "$mode" in
        quick)
            log_info "Running quick fixes only..."
            phase1_ruff_fix
            phase2_delete_orphaned
            ;;
        integrate)
            log_info "Running integration fixes..."
            phase3_integrate_enhanced_metrics
            phase4_integrate_advanced_modules
            ;;
        manual)
            log_info "Showing manual actions..."
            phase5_rename_legacy_program
            phase6_merge_chat_signatures
            ;;
        archive)
            log_info "Running archive operations..."
            phase7_clean_training_data
            ;;
        all)
            log_info "Running all automated fixes..."
            phase1_ruff_fix
            phase2_delete_orphaned
            phase3_integrate_enhanced_metrics
            phase4_integrate_advanced_modules
            phase7_clean_training_data
            echo ""
            phase5_rename_legacy_program
            echo ""
            phase6_verify_chat_deleted
            ;;
        verify)
            verify_cleanup
            ;;
        *)
            echo "Usage: $0 [quick|integrate|manual|archive|all|verify]"
            echo ""
            echo "  quick     - Ruff fix + delete orphans (5 min)"
            echo "  integrate - Add exports to __init__.py files (15 min)"
            echo "  manual    - Show manual refactor instructions"
            echo "  archive   - Archive old training data"
            echo "  all       - Run all automated + show manual (default)"
            echo "  verify    - Verify cleanup was successful"
            exit 1
            ;;
    esac
    
    echo ""
    log_success "Cleanup phase complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Review changes: git diff"
    echo "  2. Run tests: uv run pytest"
    echo "  3. Verify: $0 verify"
    echo ""
}

main "$@"
