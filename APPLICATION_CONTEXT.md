# DawsOS Application Context & User Flow Documentation

## 🎯 Application Overview

**DawsOS** is a sophisticated AI-powered portfolio management platform that combines institutional-grade financial analytics with Ray Dalio's economic framework. The system provides real-time portfolio analysis, macro regime detection, scenario testing, and AI-driven insights.

### Core Value Proposition
- **Real-time Portfolio Intelligence**: Track holdings, performance, and risk metrics
- **Dalio Framework Integration**: 4 economic cycles (STDC, LTDC, Empire, Internal Order)
- **AI-Powered Analysis**: Claude-powered insights and recommendations
- **Scenario Analysis**: Test portfolio resilience against market shocks
- **Macro-Aware Strategy**: Regime-conditional portfolio optimization

---

## 🏗️ System Architecture

### Technology Stack
- **Backend**: FastAPI (Python) with async/await
- **Frontend**: HTML/JavaScript with modern UI (gradient design)
- **Database**: PostgreSQL with pricing packs architecture
- **AI Integration**: Anthropic Claude API
- **Authentication**: JWT tokens with role-based access
- **Data Sources**: Polygon.io, FRED, NewsAPI, Financial Modeling Prep

### Key Components
1. **Combined Server** (`combined_server.py`): Monolithic backend (3,600+ lines)
2. **Web UI** (`full_ui.html`): Single-page application
3. **Macro Services**: Regime detection, cycle analysis
4. **Scenario Engine**: Professional factor-based modeling
5. **Alert System**: Real-time monitoring with notifications

---

## 👤 User Authentication Flow

### Login Process
1. **Entry Point**: User lands on login page
2. **Credentials**: Email + Password
3. **Authentication Methods**:
   - Mock Mode: Hardcoded users for demo
   - Production: PostgreSQL user table
4. **Token Generation**: JWT with 24-hour expiration
5. **Access Granted**: Dashboard loads with user data

### Test Credentials
```
Email: michael@dawsos.com
Password: admin123
Role: ADMIN
```

### Security Features
- Bcrypt password hashing
- JWT token validation
- Role-based access (ADMIN, MANAGER, USER, VIEWER)
- Protected API endpoints

---

## 🎮 Main Dashboard Navigation

The application has **8 primary tabs** in the navigation bar:

### 1. **Overview Tab** (Default)
**Purpose**: Portfolio summary and quick access to features

**Key Metrics Displayed**:
- Total Portfolio Value
- Unrealized P&L
- Day Return & YTD Return
- Portfolio Beta
- Sharpe Ratio
- Value at Risk (95%)
- Max Drawdown

**Feature Cards** (Quick Actions):
- 📊 Scenario Analysis → Test portfolio resilience
- 🤖 AI Analysis → Get Claude insights
- 🌍 Macro Insights → View economic indicators
- ⚡ Portfolio Optimization → Rebalancing recommendations

**Export Options** (Dropdown Menu):
- 📄 Export as PDF → Full portfolio report
- 📊 Export Holdings (CSV)
- 📈 Export Transactions (CSV)

### 2. **Holdings Tab**
**Purpose**: Detailed view of current positions

**Table Columns**:
- Symbol
- Quantity
- Current Price
- Market Value
- Portfolio Weight (%)
- Daily Change
- Beta

**Features**:
- Real-time pricing updates
- Sortable columns
- Color-coded gains/losses
- Position concentration analysis

### 3. **Transactions Tab**
**Purpose**: Complete trading history

**Summary Statistics**:
- Total Invested
- Total Dividends Received
- Realized Gains/Losses

**Transaction Table**:
- Date
- Type (Buy/Sell/Dividend)
- Symbol
- Shares
- Price
- Amount
- Gain/Loss

**Features**:
- Pagination (20 per page)
- Tax lot tracking
- Dividend reinvestment tracking

### 4. **Scenarios Tab**
**Purpose**: Stress test portfolio against market conditions

**Available Scenarios**:
1. **Market Crash (-20%)**
   - Equity selloff simulation
   - Beta-weighted impact
   - Sector correlation effects

2. **Interest Rate Hike (+2%)**
   - Duration impact on bonds
   - Growth stock compression
   - Real estate sensitivity

3. **High Inflation (6%+)**
   - Real return erosion
   - Commodity exposure benefits
   - TIPS performance

**Results Display**:
- Portfolio Impact (% and $)
- Affected Holdings List
- Hedge Recommendations
- Historical Context

### 5. **Alerts Tab**
**Purpose**: Automated monitoring and notifications

**Alert Types**:
1. **Price Alerts** 💹
   - Symbol-specific thresholds
   - Above/Below triggers
   - Percentage or absolute values

2. **Portfolio Alerts** 📊
   - Total value changes
   - P&L thresholds
   - Risk metric breaches
   - Sharpe ratio degradation

3. **Macro Alerts** 🌍
   - VIX spikes
   - Interest rate changes
   - Inflation surprises
   - GDP updates

**Alert Configuration**:
- Condition (>, <, =, crosses)
- Threshold Value
- Notification Channels (Email/SMS/In-app)
- Cooldown Period (prevent spam)
- Active/Inactive Toggle

### 6. **AI Analysis Tab**
**Purpose**: Claude-powered portfolio insights

**Query Types**:
1. **Portfolio Health Check**
   - Risk assessment
   - Diversification analysis
   - Performance attribution

2. **Market Outlook**
   - Sector rotation signals
   - Macro regime implications
   - Timing recommendations

3. **Optimization Suggestions**
   - Rebalancing proposals
   - Tax loss harvesting
   - Risk reduction strategies

**Features**:
- Natural language queries
- Context-aware responses
- Historical analysis integration
- Actionable recommendations

### 7. **Optimize Tab**
**Purpose**: Portfolio optimization using mean-variance

**Risk Tolerance Slider**:
- 0.0 = Conservative (Min volatility)
- 0.5 = Balanced
- 1.0 = Aggressive (Max return)

**Optimization Results**:
- Current vs Optimal Allocation
- Expected Return Improvement
- Risk Reduction Potential
- Specific Trade Recommendations
- Transaction Cost Analysis

### 8. **Macro Dashboard Tab** ⭐
**Purpose**: Dalio framework economic analysis

**Master Reasoning Panel** 🧠:
- Combined Assessment across all cycles
- Historical Parallels identification
- Dalio Principles application
- Causal Chain visualization

**Four Cycle Cards**:

#### Short-Term Debt Cycle (STDC)
- **Duration**: 5-8 years
- **Current Phase**: (e.g., "Late Expansion")
- **Key Metrics**:
  - Credit Growth Rate
  - Interest Rate Cycle Position
  - Phase Duration
- **Visual**: Cycle position chart
- **Reasoning Panel**: Shows raw data → calculations → logic → conclusion

#### Long-Term Debt Cycle (LTDC)
- **Duration**: 75-100 years
- **Current Phase**: (e.g., "Bubble")
- **Key Metrics**:
  - Debt/GDP Ratio
  - Debt Service Ratio
  - Deleveraging Risk Level
- **Visual**: Cycle position chart
- **Reasoning Panel**: Complete analysis chain

#### Empire Cycle
- **Duration**: 250 years
- **Current Phase**: (e.g., "Peak")
- **Empire Score**: 0-100
- **8 Key Indicators**:
  - Education Level
  - Innovation Rate
  - Military Strength
  - Trade Dominance
  - Reserve Currency Status
  - Wealth Gap
  - Values Strength
  - Natural Resources

#### Internal Order Cycle
- **Duration**: 100 years
- **Current Stage**: 1-6
- **Key Metrics**:
  - Wealth Inequality (Gini)
  - Political Polarization
  - Social Cohesion Score
- **Stage Descriptions**: From prosperity to revolution

**Economic Indicators Grid**:
- GDP Growth (with trend)
- Inflation Rate
- Unemployment
- Interest Rates
- VIX (Fear Index)
- Dollar Index

**Market Outlook Panels**:
- Near-term (1-3 months)
- Medium-term (3-12 months)
- Risk factors
- Opportunities

---

## 🔄 Key User Workflows

### Workflow 1: Daily Portfolio Review
```
1. Login → Dashboard
2. Check Overview metrics (P&L, returns)
3. Review Holdings for concentration
4. Check Active Alerts for triggers
5. Read AI morning briefing
6. Export daily report (optional)
```

### Workflow 2: Risk Assessment
```
1. Navigate to Scenarios tab
2. Run "Market Crash" scenario
3. Review impact on holdings
4. Navigate to Optimize tab
5. Adjust risk tolerance slider
6. Generate rebalancing recommendations
7. Review suggested trades
```

### Workflow 3: Macro-Driven Strategy
```
1. Open Macro Dashboard
2. Review 4 cycles positions
3. Click "Show Reasoning" for details
4. Understand regime classification
5. Navigate to Scenarios
6. Run regime-appropriate scenario
7. Get AI recommendations
8. Set regime-based alerts
```

### Workflow 4: Alert Management
```
1. Go to Alerts tab
2. Click "+ New Alert"
3. Select alert type (Price/Portfolio/Macro)
4. Configure conditions:
   - Choose metric/symbol
   - Set operator (>, <, crosses)
   - Enter threshold
   - Select notification channel
5. Save alert
6. Monitor triggers in real-time
```

### Workflow 5: AI-Assisted Analysis
```
1. Navigate to AI Analysis
2. Type natural language query:
   "What's my biggest risk?"
   "Should I rebalance given inflation?"
   "Find tax loss harvesting opportunities"
3. Review Claude's analysis
4. Follow recommendations
5. Set alerts based on insights
```

---

## 🎯 Function Behavior Under Different Options

### Mock Mode vs Production Mode

#### **Mock Mode** (USE_MOCK_DATA=true)
- **Data Source**: Hardcoded sample portfolio
- **Holdings**: Fixed 8 stocks (AAPL, GOOGL, etc.)
- **Scenarios**: Basic calculations using beta
- **Macro Data**: Simulated regime changes
- **Alerts**: In-memory storage
- **Purpose**: Demo and development

#### **Production Mode** (USE_MOCK_DATA=false)
- **Data Source**: PostgreSQL database
- **Holdings**: Real user positions
- **Scenarios**: Professional factor modeling
- **Macro Data**: Live FRED API data
- **Alerts**: Database-persisted
- **Purpose**: Live trading

### Feature Availability Matrix

| Feature | Mock Mode | Production | Notes |
|---------|-----------|------------|-------|
| Portfolio Overview | ✅ Full | ✅ Full | Real-time calculations |
| Holdings Display | ✅ Static | ✅ Dynamic | DB-driven in production |
| Transactions | ✅ Sample | ✅ Historical | Full history in production |
| Basic Scenarios | ✅ Working | ❌ 501 Error | Needs connection fix |
| Advanced Scenarios | ❌ N/A | ✅ 9 types | Professional system ready |
| Macro Dashboard | ✅ Full | ✅ Full | All 4 cycles operational |
| AI Analysis | ✅ Limited | ✅ Full | Context-aware in production |
| Alerts | ✅ Volatile | ✅ Persistent | DB-backed in production |
| Optimization | ✅ Basic | ✅ Advanced | Riskfolio-lib in production |
| Export PDF | ✅ Working | ✅ Working | Full reports |
| Export CSV | ✅ Working | ✅ Working | Holdings & transactions |

### Conditional Logic Examples

#### Scenario Analysis Behavior
```python
if USE_MOCK_DATA:
    # Simple beta-based calculation
    impact = portfolio_value * beta * scenario_magnitude
else:
    # Professional multi-factor attribution
    impact = ScenarioService.apply_shock(
        factors=['rates', 'credit', 'equity', 'fx'],
        correlations=correlation_matrix,
        portfolio=actual_positions
    )
```

#### Alert Processing
```python
if USE_MOCK_DATA:
    # Check in-memory list
    triggered = check_against_mock_thresholds()
else:
    # Database query with cooldown logic
    triggered = await check_alerts_with_cooldown(user_id)
```

---

## 🚨 Critical Integration Points

### 1. **Scenario Analysis Gap**
- **Issue**: Production throws 501 error
- **Root Cause**: ScenarioService not connected
- **Impact**: Users can't stress test in production
- **Fix Required**: Connect professional service

### 2. **Macro-Scenario Integration**
- **Opportunity**: Regime-conditional scenarios
- **Current State**: Systems disconnected
- **Proposed**: MacroAwareScenarioService
- **Value**: Dynamic risk assessment

### 3. **Historical Pattern Matching**
- **Vision**: Learn from similar periods
- **Data Available**: 30+ years of history
- **Implementation**: EmpiricalScenarioEngine
- **Benefit**: Data-driven predictions

### 4. **Real-time Updates**
- **Current**: Page refresh required
- **Needed**: WebSocket integration
- **Components**: Price feeds, alerts, regime changes
- **Impact**: Better user experience

---

## 📊 Data Flow Architecture

### User Action Flow
```
User Input → UI Event Handler → API Call → Backend Service
    ↓              ↓                ↓            ↓
Form Data    JavaScript     HTTP Request   Python Logic
    ↓              ↓                ↓            ↓
Validation   Fetch API      JWT Auth      Business Logic
    ↓              ↓                ↓            ↓
              UI Update    JSON Response   Database Query
```

### Macro Analysis Flow
```
FRED Data → Indicators → Z-Score Normalization → Regime Detection
    ↓           ↓              ↓                      ↓
Raw Values  Calculations  Statistical         Classification
    ↓           ↓              ↓                      ↓
         Cycle Analysis → Combined Assessment → Recommendations
```

### Scenario Analysis Flow
```
Current Portfolio → Factor Exposures → Shock Application
        ↓                 ↓                  ↓
    Positions         Beta/Duration    Multi-factor Model
        ↓                 ↓                  ↓
              Impact Calculation → Hedge Recommendations
```

---

## 🎮 User Experience Optimizations

### Performance Features
- **Lazy Loading**: Tabs load on demand
- **Pagination**: Large datasets chunked
- **Caching**: Frequently accessed data cached
- **Debouncing**: API calls throttled

### Visual Feedback
- **Loading States**: Spinners and skeletons
- **Success Messages**: Green notifications
- **Error Handling**: Red alerts with guidance
- **Progress Indicators**: Multi-step processes

### Accessibility
- **Keyboard Navigation**: Tab through interface
- **Screen Reader Support**: ARIA labels
- **Color Contrast**: WCAG AA compliant
- **Responsive Design**: Mobile-friendly

---

## 🔮 Future Enhancements

### Planned Features
1. **WebSocket Real-time Updates**
2. **Mobile Native Apps**
3. **Multi-Portfolio Support**
4. **Social Features** (follow traders)
5. **Backtesting Engine**
6. **Options Analytics**
7. **Tax Optimization**
8. **Custom Indicators**

### Technical Improvements
1. **Microservices Migration**
2. **GraphQL API**
3. **Redis Caching Layer**
4. **Kubernetes Deployment**
5. **ML-Based Predictions**
6. **Blockchain Integration**

---

## 📚 API Endpoint Reference

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/me` - Current user info

### Portfolio
- `GET /api/portfolio` - Portfolio overview
- `GET /api/holdings` - Current positions
- `GET /api/transactions` - Trade history
- `GET /api/metrics` - Performance metrics

### Analysis
- `POST /execute` - Run analysis patterns
- `POST /api/scenario` - Scenario analysis
- `POST /api/ai/analyze` - AI insights
- `POST /api/optimize` - Optimization

### Alerts
- `GET /api/alerts` - List alerts
- `POST /api/alerts` - Create alert
- `PUT /api/alerts/{id}` - Update alert
- `DELETE /api/alerts/{id}` - Delete alert

### Export
- `GET /api/export/pdf` - PDF report
- `GET /api/export/csv` - CSV export

### System
- `GET /health` - Health check
- `GET /` - Serve UI

---

## 🏁 Conclusion

DawsOS represents a sophisticated fusion of:
- **Traditional portfolio management**
- **Dalio's economic framework**
- **AI-powered intelligence**
- **Real-time market data**

The system's strength lies in its comprehensive approach to portfolio analysis, combining multiple perspectives (micro portfolio metrics, macro regime analysis, AI insights) into actionable intelligence for investors.

The architecture is ready for production use with some integration gaps to close, particularly connecting the professional ScenarioService and implementing the proposed MacroAwareScenarioService for regime-conditional analysis.