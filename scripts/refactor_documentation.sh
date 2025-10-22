#!/bin/bash
# Documentation Refactoring Script
# Consolidates 18 files → 13 files with proper hierarchy

set -e

echo "=== DOCUMENTATION REFACTORING SCRIPT ==="
echo ""

# Create backup directory
echo "1. Creating backup..."
mkdir -p archive/old_docs_backup
cp *.md archive/old_docs_backup/ 2>/dev/null || true

# Create session reports directory
echo "2. Creating session_reports directory..."
mkdir -p archive/session_reports

# Archive historical files
echo "3. Archiving historical files..."
[ -f "NAMING_FIXES_COMPLETE.md" ] && mv NAMING_FIXES_COMPLETE.md archive/session_reports/2025-10-21_naming_fixes.md
[ -f "PLAN_VALIDATION_AND_UX_SIMULATION.md" ] && mv PLAN_VALIDATION_AND_UX_SIMULATION.md archive/session_reports/2025-10-21_ux_validation.md

# Delete outdated file
echo "4. Deleting outdated file..."
[ -f "AUDIT_SUMMARY_AND_NEXT_STEPS.md" ] && rm AUDIT_SUMMARY_AND_NEXT_STEPS.md

echo ""
echo "✅ Phase 1 Complete - Historical files archived"
echo ""
echo "Next steps (manual):"
echo "1. Create CURRENT_STATE.md (merge FINAL_CONSOLIDATED_STATE.md + PROJECT_STATE_AUDIT.md)"
echo "2. Create PRODUCT_VISION.md (merge TRINITY_PRODUCT_VISION_REFINED.md + PRODUCT_VISION_ALIGNMENT_ANALYSIS.md)"
echo "3. Update README.md with hierarchy"
echo "4. Update CLAUDE.md references"
echo "5. Archive source files after merge"
