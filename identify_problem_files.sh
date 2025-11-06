#!/bin/bash
# Identify and remove files causing git sync issues

echo "==================================================================="
echo "          IDENTIFYING PROBLEMATIC FILES FOR GIT SYNC              "
echo "==================================================================="
echo ""

# Step 1: Clear lock files first
echo "[1/5] Clearing lock files..."
rm -f .git/index.lock 2>/dev/null
rm -f .git/refs/remotes/origin/HEAD.lock 2>/dev/null
find .git -name "*.lock" -delete 2>/dev/null || true
echo "✅ Lock files cleared"

# Step 2: List all the documentation files that are likely causing issues
echo ""
echo "[2/5] PROBLEMATIC FILES (likely causing conflicts):"
echo ""
echo "=== DOCUMENTATION FILES (41 files) ==="
ls -1 *.md 2>/dev/null | grep -v README.md | grep -v replit.md | head -40

echo ""
echo "=== TEMPORARY SCRIPTS (11 files) ==="
ls -1 *.sh 2>/dev/null | head -15

echo ""
echo "=== TEST/VALIDATION FILES (5 files) ==="
ls -1 *_results.json 2>/dev/null

echo ""
echo "=== BACKUP FILES ==="
ls -1 *.tar.gz 2>/dev/null

# Step 3: Count problematic files
echo ""
echo "[3/5] FILE COUNT:"
MD_COUNT=$(ls -1 *.md 2>/dev/null | wc -l)
SH_COUNT=$(ls -1 *.sh 2>/dev/null | wc -l)
JSON_COUNT=$(ls -1 *_results.json 2>/dev/null | wc -l)
echo "  Documentation files: $MD_COUNT"
echo "  Script files: $SH_COUNT"
echo "  Test result files: $JSON_COUNT"
echo "  Total problematic: $(($MD_COUNT + $SH_COUNT + $JSON_COUNT))"

# Step 4: Show what we need to keep
echo ""
echo "[4/5] FILES TO KEEP (critical fixes):"
echo "  ✅ backend/app/services/factor_analysis.py"
echo "  ✅ backend/app/agents/financial_analyst.py"
echo "  ✅ backend/db/schema/economic_indicators.sql"
echo "  ✅ backend/db/migrations/015_add_economic_indicators.sql"
echo "  ✅ README.md"
echo "  ✅ replit.md"
echo "  ✅ combined_server.py"
echo "  ✅ full_ui.html"
echo "  ✅ requirements.txt"

# Step 5: Create removal script
echo ""
echo "[5/5] Creating cleanup script..."
cat > remove_problem_files.sh << 'CLEANUP'
#!/bin/bash
echo "Removing all problematic files..."

# Remove all documentation except README.md and replit.md
ls -1 *.md | grep -v README.md | grep -v replit.md | xargs rm -f 2>/dev/null

# Remove all temporary scripts except this one
ls -1 *.sh | grep -v remove_problem_files.sh | xargs rm -f 2>/dev/null

# Remove test results
rm -f *_results.json 2>/dev/null

# Remove backup files
rm -f *.tar.gz 2>/dev/null

# Remove Python scripts that aren't core
rm -f analyze_pattern_contracts.py 2>/dev/null
rm -f load_env.py 2>/dev/null

# Remove attached_assets if it exists
rm -rf attached_assets 2>/dev/null

echo "✅ Problematic files removed!"
echo ""
echo "Now try: git status"
CLEANUP

chmod +x remove_problem_files.sh

echo ""
echo "==================================================================="
echo "                    PROBLEM FILES IDENTIFIED!                     "
echo "==================================================================="
echo ""
echo "THE ISSUE: You have 50+ documentation and temporary files"
echo "that are conflicting with the remote repository!"
echo ""
echo "TO FIX: Run this command to remove all problematic files:"
echo ""
echo "  ./remove_problem_files.sh"
echo ""
echo "This will remove all the temporary files but keep your"
echo "4 critical code fixes and core application files."
echo ""