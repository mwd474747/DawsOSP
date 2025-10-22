#!/bin/bash
# ARCHIVE_CLEANUP.sh - Reduce archive from 230 files → 15 files (93% reduction)

set -e

echo "=== ARCHIVE CLEANUP - MASSIVE REDUCTION ==="
echo ""
echo "This will DELETE 209 files from archive/"
echo "Files are preserved in git history"
echo ""

# Phase 1: Delete entire directories (58 files)
echo "Phase 1: Deleting obsolete migration directories..."
rm -rf archive/migration_docs_old/
rm -rf archive/migration_history/
rm -rf archive/v3_migration_to_root/
rm -rf archive/old_docs_backup/
echo "  ✅ 58 files deleted (4 directories)"

# Phase 2: Clean session_reports (18 files)
echo "Phase 2: Cleaning session_reports (keep 2 recent)..."
cd archive/session_reports/
rm -f DEAD_CODE_VALIDATION_REPORT.md
rm -f ECONOMIC_DASHBOARD_COMPLETE.md
rm -f FINAL_SESSION_COMPLETE.md
rm -f INTEGRATION_TEST_SUMMARY.md
rm -f PATTERN_REMEDIATION_COMPLETE.md
rm -f PHASE0_*.md
rm -f PHASE1_EMERGENCY_FIX_COMPLETE.md
rm -f REFACTORING_PHASE2_COMPLETE.md
rm -f REMEDIATION_SESSION_SUMMARY.md
rm -f SESSION_COMPLETE_SUMMARY.md
rm -f SESSION_SUMMARY.md
rm -f TEMPLATE_GENERATION_REPORT.md
rm -f TRINITY_3.0_COMPLETION_REPORT.md
rm -f TRINITY_3.0_DETAILED_EXECUTION_PLAN.md
rm -f UI_STRUCTURE_IMPROVEMENT_REPORT.md
cd ../..
echo "  ✅ 15 files deleted"

# Phase 3: Clean legacy archive (128 files)
echo "Phase 3: Cleaning legacy archive (keep INDEX + claude_agents)..."
rm -rf archive/legacy/fixes/
rm -rf archive/legacy/refactoring/
rm -rf archive/legacy/sessions/
rm -rf archive/legacy/technical_debt/
echo "  ✅ 128 files deleted (4 subdirectories)"

# Phase 4: Clean planning_docs (5 files)
echo "Phase 4: Cleaning planning_docs (keep 3 reference)..."
cd archive/planning_docs/
rm -f AGENT_WIRING_PLAN.md
rm -f CLEANUP_SUMMARY.md
rm -f CURRENT_STATE_ASSESSMENT.md
rm -f TRINITY_AGENTS_REPLACED.md
rm -f AGENT_SOURCE_INVESTIGATION.md
cd ../..
echo "  ✅ 5 files deleted"

echo ""
echo "=== CLEANUP COMPLETE ==="
echo "Total deleted: 206 files"
echo "Archive reduced: ~230 files → ~15 files (93% reduction)"
echo ""
echo "Remaining archive structure:"
find archive -name "*.md" -type f | sort
echo ""
echo "Archive directory count:"
find archive -type d | wc -l
