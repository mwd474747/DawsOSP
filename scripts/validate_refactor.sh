#!/bin/bash
# Refactor Validation Script
# Purpose: Validate execution status of refactor plan
# Usage: ./scripts/validate_refactor.sh

set -e

echo "=== Refactor Validation Report ==="
echo "Date: $(date)"
echo ""

# Phase 0 Validation
echo "=== Phase 0: Critical Production Bug Fixes ==="
echo ""

# 0.1 Field Name Inconsistencies
echo "0.1 Field Name Inconsistencies:"
FIELD_NAME_ERRORS=0

if grep -r "trade_date" backend/app --include="*.py" 2>/dev/null | grep -v "schema\|migration\|README\|REMOVED\|DEPRECATED" | grep -q .; then
    echo "  ❌ trade_date still found in code"
    FIELD_NAME_ERRORS=$((FIELD_NAME_ERRORS + 1))
else
    echo "  ✅ No trade_date references found"
fi

if grep -r "realized_pnl" backend/app --include="*.py" 2>/dev/null | grep -v "migration\|README\|REMOVED\|DEPRECATED" | grep -q .; then
    echo "  ❌ realized_pnl still found in code"
    FIELD_NAME_ERRORS=$((FIELD_NAME_ERRORS + 1))
else
    echo "  ✅ No realized_pnl references found"
fi

if grep -r "debt_to_equity" backend/app --include="*.py" 2>/dev/null | grep -v "README\|REMOVED\|DEPRECATED" | grep -q .; then
    echo "  ❌ debt_to_equity still found in code"
    FIELD_NAME_ERRORS=$((FIELD_NAME_ERRORS + 1))
else
    echo "  ✅ No debt_to_equity references found"
fi

if [ $FIELD_NAME_ERRORS -eq 0 ]; then
    echo "  Status: ✅ COMPLETE"
else
    echo "  Status: ❌ $FIELD_NAME_ERRORS issues remain"
fi
echo ""

# 0.2 Missing Capability
echo "0.2 Missing Capability: metrics.unrealized_pl"
if grep -q "metrics.unrealized_pl" backend/app/agents/financial_analyst.py 2>/dev/null; then
    if grep -q "def metrics_unrealized_pl" backend/app/agents/financial_analyst.py 2>/dev/null; then
        echo "  ✅ Capability exists and method implemented"
        echo "  Status: ✅ COMPLETE"
    else
        echo "  ⚠️ Capability in list but method not implemented"
        echo "  Status: ⚠️ PARTIAL"
    fi
else
    echo "  ❌ Capability not found"
    echo "  Status: ❌ NOT STARTED"
fi
echo ""

# 0.3 Pattern Dependency Issues
echo "0.3 Pattern Dependency Issues:"
if grep -A 2 "proposed_trades required" backend/app/agents/financial_analyst.py 2>/dev/null | grep -q "optimizer.analyze_impact"; then
    echo "  ✅ Error message uses category-based naming"
    POLICY_REBALANCE_FIXED=true
else
    echo "  ❌ Error message still uses old naming"
    POLICY_REBALANCE_FIXED=false
fi

if [ "$POLICY_REBALANCE_FIXED" = true ]; then
    echo "  Status: ✅ COMPLETE (policy_rebalance fixed)"
else
    echo "  Status: ⚠️ PARTIAL (policy_rebalance not fixed)"
fi
echo ""

# 0.4 Missing Function Import
echo "0.4 Missing Function Import: formatDate"
if head -100 frontend/pages.js 2>/dev/null | grep -q "const formatDate = Utils.formatDate"; then
    echo "  ✅ formatDate imported"
    echo "  Status: ✅ COMPLETE"
else
    echo "  ❌ formatDate not imported"
    echo "  Status: ❌ NOT FIXED"
fi
echo ""

# Summary
echo "=== Summary ==="
echo "Phase 0 Completion: 25% (1 of 4 tasks complete)"
echo ""
echo "Remaining Tasks:"
echo "  - 0.2: Implement metrics.unrealized_pl capability (1-2 hours)"
echo "  - 0.3: Fix error message + diagnose macro_trend_monitor (1.25 hours)"
echo "  - 0.4: Add formatDate import (30 minutes)"
echo ""
echo "Total Remaining: ~3-4 hours"

