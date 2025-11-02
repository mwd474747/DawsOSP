# DawsOS User Flow Documentation

## 🎯 Overview
This document maps all user journeys through the DawsOS platform, detailing decision points, actions, and outcomes for each workflow.

---

## 🔐 Authentication Flows

### Flow 1: First-Time User Login
```mermaid
Start → Login Page → Enter Credentials → Validate
         ↓                   ↓              ↓
   See Gradient UI    Email + Password   JWT Token
         ↓                   ↓              ↓
                      Submit Form    → Dashboard Loads
                           ↓              ↓
                    [Invalid] → Error  Portfolio Data
                           ↓
                     Try Again
```

**Steps:**
1. User navigates to application URL
2. Lands on login page with gradient background
3. Enters email and password
4. System validates credentials:
   - **Success**: JWT token generated, dashboard loads
   - **Failure**: Error message displayed
5. Dashboard shows personalized portfolio data

**Key Decision Points:**
- Credentials correct? → Success/Retry
- Database available? → Production/Mock mode

---

## 📊 Portfolio Management Flows

### Flow 2: Daily Portfolio Review
```
Dashboard → Overview Tab → Check Metrics → Review Holdings
     ↓           ↓              ↓              ↓
  Login    8 Key Stats    Green/Red      Holdings Tab
     ↓           ↓              ↓              ↓
          [Export?] → PDF   [Alerts?] → Check Triggers
```

**Morning Routine Path:**
1. **9:00 AM** - User logs in
2. **Overview Tab** - Scans 8 metrics:
   - Total Value: $1.2M (↑)
   - Day Return: +0.8%
   - YTD Return: +12.3%
   - Sharpe Ratio: 1.4
3. **Decision**: Performance acceptable?
   - ✅ Yes → Continue to Holdings
   - ❌ No → Navigate to Scenarios/AI
4. **Holdings Review** - Check concentration
5. **Export** - Generate morning report

### Flow 3: Risk Assessment Journey
```
Concern → Scenarios Tab → Select Scenario → View Impact
   ↓           ↓              ↓               ↓
Market     3 Options    Market Crash    Portfolio -$240k
News          ↓              ↓               ↓
         [Customize?]   Run Analysis   [Too High?] → Optimize
```

**Risk Analysis Path:**
1. **Trigger**: Market volatility news
2. **Navigate**: Scenarios Tab
3. **Choose Scenario**:
   - Market Crash (-20%)
   - Interest Rate Hike (+2%)
   - High Inflation (6%+)
4. **Review Results**:
   - Dollar Impact
   - Affected Holdings
   - VaR Analysis
5. **Decision Tree**:
   - Risk Acceptable → Set Alerts
   - Risk Too High → Optimization Tab
   - Need Advice → AI Analysis

---

## 🤖 AI-Assisted Workflows

### Flow 4: AI Analysis Journey
```
Question → AI Tab → Type Query → Get Analysis → Take Action
    ↓         ↓          ↓           ↓            ↓
Problem   Natural   "What's my   Claude      Follow Advice
         Language   biggest risk?"  Response        ↓
                                      ↓       Set Alerts
                                  Markdown    Rebalance
                                  Response    Research
```

**Common AI Query Paths:**

#### Path A: Risk Discovery
1. User asks: "What's my biggest risk exposure?"
2. Claude analyzes:
   - Portfolio concentration
   - Sector exposure
   - Correlation risks
3. Response: "72% tech concentration poses risk"
4. User action: Navigate to Optimize

#### Path B: Market Timing
1. User asks: "Should I rebalance given current macro?"
2. Claude considers:
   - Current regime
   - Cycle positions
   - Historical patterns
3. Response: "Late cycle suggests defensive shift"
4. User action: Review recommendations

#### Path C: Tax Optimization
1. User asks: "Find tax loss harvesting opportunities"
2. Claude identifies:
   - Unrealized losses
   - Wash sale rules
   - Offset potential
3. Response: "Sell ARKK, harvest $12k loss"
4. User action: Execute trades

---

## 🌍 Macro Analysis Flows

### Flow 5: Macro-Driven Strategy
```
Macro Tab → Review 4 Cycles → Show Reasoning → Understand
    ↓            ↓                ↓              ↓
Navigate    STDC: Late      Click Button    See Logic Chain
    ↓       LTDC: Bubble         ↓              ↓
         Empire: Peak     Raw Data→Math    Portfolio Impact
         Order: Stage 4          ↓              ↓
                           Conclusion    Adjust Strategy
```

**Macro Investigation Path:**
1. **Open Macro Dashboard**
2. **Scan 4 Cycles**:
   - STDC: "Late Expansion" 🔴
   - LTDC: "Bubble" 🔴
   - Empire: "Peak" ⚠️
   - Internal Order: "Stage 4" ⚠️
3. **Deep Dive** (Show Reasoning):
   - View raw indicators
   - See calculations
   - Follow logic chain
   - Read conclusion
4. **Pattern Recognition**:
   - "Similar to 2007"
   - "Matches 2000 setup"
5. **Strategic Decision**:
   - Reduce risk → Optimize Tab
   - Hedge → Scenarios Tab
   - Get advice → AI Tab

### Flow 6: Reasoning Chain Investigation
```
Cycle Card → Show Reasoning → Raw Data → Calculations → Logic → Conclusion
     ↓            ↓            ↓           ↓           ↓         ↓
  STDC       Button Click   GDP: 2.1%   Z-Score    IF/THEN   "Late Stage"
                            CPI: 3.4%    Normalize  Rules     Action Items
```

**Deep Analysis Path:**
1. Click "Show Reasoning" on STDC
2. **Raw Data Display**:
   - Credit Growth: 8.2%
   - Fed Funds: 5.25%
   - Spread: -0.5%
3. **Calculations Show**:
   - "Credit Z-Score: +1.8σ"
   - "Inverted yield curve"
4. **Logic Chain**:
   - "IF credit > 7% AND curve inverted"
   - "THEN late cycle probability = 85%"
5. **Conclusion**:
   - "Recession risk elevated"
   - "Reduce equity exposure"

---

## 🔔 Alert Management Flows

### Flow 7: Alert Creation Workflow
```
Alerts Tab → New Alert → Choose Type → Configure → Save
     ↓          ↓           ↓            ↓         ↓
Navigate   Click Button  Price/Port   Set Rules  Active
                          /Macro     Threshold   Monitor
```

**Alert Setup Paths:**

#### Price Alert Path:
1. Click "+ New Alert"
2. Select "Price Alert"
3. Choose Symbol (AAPL)
4. Set Condition (Below)
5. Enter Threshold ($150)
6. Configure Channels (Email)
7. Set Cooldown (4 hours)
8. Save & Activate

#### Portfolio Alert Path:
1. Select "Portfolio Alert"
2. Choose Metric:
   - Total Value
   - Sharpe Ratio
   - Volatility
3. Set Trigger Level
4. Configure Notifications

#### Macro Alert Path:
1. Select "Macro Alert"
2. Choose Indicator:
   - VIX > 30
   - Rate Change
   - Inflation Surprise
3. Set Sensitivity
4. Link to Actions

### Flow 8: Alert Response Flow
```
Alert Fires → Notification → User Checks → Analyze → Action
     ↓            ↓             ↓           ↓         ↓
Condition    Email/SMS    Open Dashboard  Context  Trade/Hold
   Met                         ↓           ↓         
                          Review Alert  AI Advice
```

---

## ⚡ Optimization Workflows

### Flow 9: Portfolio Optimization Journey
```
Optimize Tab → Set Risk → Generate → Review → Implement
      ↓           ↓          ↓        ↓         ↓
  Navigate    Slider     Algorithm  Compare   Execute
             (0-1.0)       Runs    Current vs  Trades
                            ↓      Optimal
                      Recommendations
```

**Optimization Decision Tree:**
1. **Set Risk Tolerance**:
   - 0.0-0.3: Conservative
   - 0.4-0.6: Balanced
   - 0.7-1.0: Aggressive
2. **Generate Recommendations**
3. **Review Suggestions**:
   - Current: 70% stocks, 30% bonds
   - Optimal: 60% stocks, 35% bonds, 5% gold
4. **Analyze Trade-offs**:
   - Return: +0.5% expected
   - Risk: -2.1% volatility
   - Costs: $340 in fees
5. **Decision**:
   - Accept → Execute trades
   - Modify → Adjust constraints
   - Reject → Keep current

---

## 📤 Export Workflows

### Flow 10: Report Generation
```
Need Report → Export Button → Choose Format → Generate → Download
      ↓            ↓              ↓            ↓          ↓
  Meeting      Dropdown      PDF/CSV      Processing   Save File
                Menu         Holdings        ↓
                           Transactions   Preview
```

**Export Scenarios:**

#### Monthly Report Path:
1. Navigate to Overview
2. Click Export dropdown
3. Select "Export as PDF"
4. System generates:
   - Portfolio summary
   - Performance charts
   - Holdings details
   - Transaction history
5. Download PDF
6. Email to stakeholders

#### Tax Preparation Path:
1. Go to Transactions
2. Export → CSV
3. Select date range
4. Include:
   - All trades
   - Dividends
   - Fees
5. Download CSV
6. Import to tax software

---

## 🔄 Scenario Testing Flows

### Flow 11: Scenario Analysis Workflow
```
Concern → Scenarios → Select Test → Run → Evaluate → Decide
   ↓         ↓           ↓          ↓        ↓         ↓
Market    Navigate   Crash/Rate   Execute  Impact   Hedge/Hold
Event                /Inflation   Analysis  Report   /Rebalance
```

**Scenario Testing Paths:**

#### Market Crash Simulation:
1. Select "Market Crash (-20%)"
2. System calculates:
   - Beta-weighted impacts
   - Correlation effects
   - Sector exposure
3. Results show:
   - Portfolio: -$240,000
   - AAPL: -$45,000
   - Bonds: +$8,000
4. Decision:
   - Add hedges
   - Reduce exposure
   - Accept risk

#### Interest Rate Shock:
1. Select "Rate Hike (+2%)"
2. Analysis includes:
   - Duration impact
   - REIT exposure
   - Bank benefits
3. Results guide:
   - Shorten duration
   - Add floating rate
   - Increase banks

---

## 🎯 Decision Tree Summaries

### Master Decision Flow
```
Login → Dashboard → Primary Goal?
           ↓
    ┌──────┴──────┬──────────┬───────────┬──────────┐
    │             │          │           │          │
Check Health  Assess Risk  Get Advice  Optimize  Monitor
    ↓             ↓          ↓           ↓          ↓
Overview      Scenarios    AI Tab    Optimize    Alerts
    ↓             ↓          ↓           ↓          ↓
Metrics       Run Tests   Query      Rebalance   Set/Check
    ↓             ↓          ↓           ↓          ↓
Export        Evaluate    Follow     Execute     Respond
```

### Risk Management Decision Tree
```
Risk Concern
     ↓
Is it Specific?
  ├─ Yes → Scenarios Tab → Run Specific Test
  └─ No → AI Analysis → "Assess my risks"
            ↓
       Risk Level?
         ├─ High → Optimize Tab → Reduce Risk
         ├─ Medium → Set Alerts → Monitor
         └─ Low → Continue Normal Operations
```

### Macro-Driven Decision Tree
```
Macro Dashboard
      ↓
  All 4 Cycles
      ↓
  Risk Level?
   ├─ RED (High Risk)
   │    ├─ Check Scenarios → Crash Test
   │    ├─ Optimize → Defensive
   │    └─ Set Macro Alerts
   │
   ├─ YELLOW (Moderate)
   │    ├─ AI Analysis → Get Advice
   │    ├─ Review Holdings
   │    └─ Prepare Hedges
   │
   └─ GREEN (Low Risk)
        ├─ Stay Course
        ├─ Look for Opportunities
        └─ Reduce Hedges
```

---

## 🚀 Advanced User Journeys

### Power User Daily Routine
```
6:30 AM: Check overnight alerts (mobile)
9:00 AM: Login → Macro Dashboard → Check all 4 cycles
9:15 AM: Overview → Export morning report
9:30 AM: AI Query: "Opportunities today?"
10:00 AM: Review recommendations
2:30 PM: Check alerts
3:30 PM: End-of-day position review
```

### Institutional Manager Workflow
```
Weekly:
- Monday: Macro review → Regime assessment
- Tuesday: Scenario testing → Stress tests
- Wednesday: Optimization → Rebalancing proposals
- Thursday: AI analysis → Deep dives
- Friday: Reports → Export for clients
```

### Risk Officer Checklist
```
Daily:
1. Scenarios Tab → Run all 3 tests
2. Check VaR and max drawdown
3. Review concentration risks
4. Verify hedge effectiveness
5. Set/adjust risk alerts
6. Document in AI chat
```

---

## 🔍 Error Recovery Flows

### Connection Lost
```
Action Failed → Error Message → Retry Options
      ↓             ↓              ↓
API Timeout   "Try Again"    Refresh Page
                              Use Cached Data
                              Contact Support
```

### Invalid Data
```
Form Submit → Validation → Error Display → Correct
     ↓           ↓            ↓             ↓
User Input   Client-side  Red Border   Fix & Retry
             Validation    Message
```

### Service Unavailable
```
API Call → 503 Error → Fallback Mode → Limited Features
    ↓          ↓           ↓              ↓
Request    No Database  Mock Data    Basic Functions
                         Active         Only
```

---

## 📱 Mobile Adaptation Flows

### Mobile Navigation
```
Hamburger Menu → Drawer Opens → Select Tab → Close Drawer
       ↓             ↓             ↓            ↓
   Top Right     Slide Out    Tap Option   Auto Close
                Animation                   Load Content
```

### Touch Interactions
```
Holdings List → Long Press → Context Menu → Quick Actions
      ↓            ↓            ↓             ↓
   Scroll      Hold 1s     View Details   Buy/Sell
                            Set Alert       Share
```

---

## 🎬 Onboarding Flow (Future)

### New User Journey
```
Sign Up → Verification → Portfolio Setup → Tutorial → Live Mode
   ↓          ↓              ↓              ↓         ↓
Email    Confirm Email  Import/Manual   Guided Tour  Full Access
         Set Password   Add Holdings    Key Features  All Tools
```

---

## 🏁 Conclusion

These user flows represent the complete journey map through DawsOS, covering:
- **15+ Primary Workflows**
- **50+ Decision Points**
- **100+ User Actions**
- **Multiple User Personas**

The flows are designed to be:
- **Intuitive**: Natural progression
- **Efficient**: Minimal clicks
- **Flexible**: Multiple paths to goals
- **Recoverable**: Error handling throughout

Each flow has been optimized for both novice investors and professional portfolio managers, ensuring accessibility while maintaining power-user capabilities.