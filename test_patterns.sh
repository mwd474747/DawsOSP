#!/bin/bash
# Test all 15 patterns for DawsOS

TOKEN="test-token"
PORTFOLIO_ID="64ff3be6-0ed1-4990-a32b-4ded17f0320c"
SECURITY_ID="3406c701-34b0-4ba5-ad9a-ef54df4e37e2"

echo "Testing DawsOS Patterns..."
echo "=========================="

patterns=(
  "portfolio_overview"
  "holding_deep_dive"
  "portfolio_scenario_analysis"
  "portfolio_cycle_risk"
  "macro_cycles_overview"
  "macro_trend_monitor"
  "buffett_checklist"
  "policy_rebalance"
  "news_impact_analysis"
  "corporate_actions_upcoming"
  "export_portfolio_report"
  "portfolio_tax_report"
  "tax_harvesting_opportunities"
  "portfolio_macro_overview"
  "cycle_deleveraging_scenarios"
)

for pattern in "${patterns[@]}"; do
  echo -n "Testing $pattern..."
  
  # Build request based on pattern requirements
  case $pattern in
    holding_deep_dive)
      inputs='{"portfolio_id": "'$PORTFOLIO_ID'", "security_id": "'$SECURITY_ID'"}'
      ;;
    *)
      inputs='{"portfolio_id": "'$PORTFOLIO_ID'"}'
      ;;
  esac
  
  response=$(curl -s -X POST http://localhost:5000/api/patterns/execute \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"pattern_id\": \"$pattern\", \"inputs\": $inputs}" \
    2>/dev/null)
  
  status=$(echo "$response" | jq -r '.status' 2>/dev/null)
  if [ "$status" = "success" ]; then
    echo " ✅ SUCCESS"
  else
    error=$(echo "$response" | jq -r '.error.message' 2>/dev/null | head -c 50)
    echo " ❌ FAILED: $error"
  fi
done

echo "=========================="
echo "Pattern testing complete!"
