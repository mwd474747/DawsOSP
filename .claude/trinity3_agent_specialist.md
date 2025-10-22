# Trinity 3.0 Agent Specialist

**Your Role**: Port the agent system (runtime + registry + 15 agents) from DawsOS 2.0 to Trinity 3.0

**Timeline**: Week 3, 10
**Deliverables**:
- Week 3: Agent runtime + registry + 5 core agents
- Week 10: Remaining 10 agents

---

## Mission

Enable Trinity 3.0 to have the same multi-agent orchestration as DawsOS 2.0:
- Port agent_runtime.py and agent_registry.py
- Port AGENT_CAPABILITIES registry (103 capabilities)
- Migrate 15 specialized agents
- Implement capability-based routing
- Ensure registry compliance tracking

---

## Week 3 Tasks

### Day 1: Agent Runtime Core

**Source**: `dawsos/core/agent_runtime.py`
**Destination**: `trinity3/core/agent_runtime.py`

**Port AgentRuntime Class**:

```python
# trinity3/core/agent_runtime.py
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

class AgentRuntime:
    """Orchestrates execution across 15 specialized agents"""

    def __init__(self, config, knowledge_loader, openbb_adapter):
        self.config = config
        self.knowledge_loader = knowledge_loader
        self.openbb_adapter = openbb_adapter
        self.logger = logging.getLogger(__name__)

        # Agent registry
        self.agents = {}
        self.agent_capabilities = {}  # agent_name → [capabilities]

        # Execution tracking
        self.execution_history = []
        self.registry_compliance_rate = 1.0

        # Initialize agents
        self._register_agents()

    def _register_agents(self):
        """Load and register all agents"""
        from agents.claude_agent import ClaudeAgent
        from agents.financial_analyst import FinancialAnalyst
        from agents.macro_analyst import MacroAnalyst
        from agents.portfolio_manager import PortfolioManager
        from agents.risk_analyst import RiskAnalyst

        # Register core agents (Week 3 - 5 agents)
        self._register_agent('claude', ClaudeAgent(self.config))
        self._register_agent('financial_analyst', FinancialAnalyst(self.config, self.openbb_adapter))
        self._register_agent('macro_analyst', MacroAnalyst(self.config, self.openbb_adapter))
        self._register_agent('portfolio_manager', PortfolioManager(self.config, self.openbb_adapter))
        self._register_agent('risk_analyst', RiskAnalyst(self.config, self.openbb_adapter))

        self.logger.info(f"Registered {len(self.agents)} agents")

    def _register_agent(self, name: str, agent: Any):
        """Register agent and its capabilities"""
        self.agents[name] = agent

        # Extract capabilities from agent
        if hasattr(agent, 'capabilities'):
            self.agent_capabilities[name] = agent.capabilities
        else:
            self.logger.warning(f"Agent {name} has no capabilities attribute")

    def exec_via_registry(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task via specific agent (name-based routing)"""
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")

        agent = self.agents[agent_name]

        # Track execution
        self._track_execution(agent_name, 'name-based', context)

        # Execute
        try:
            result = agent.process(context)
            return result
        except Exception as e:
            self.logger.error(f"Agent {agent_name} failed: {e}")
            return {'error': str(e), 'agent': agent_name}

    def execute_by_capability(self, capability: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task via capability (Trinity 2.0 standard)"""
        # Find agent with this capability
        agent_name = self._find_agent_by_capability(capability)

        if not agent_name:
            raise ValueError(f"No agent registered for capability: {capability}")

        agent = self.agents[agent_name]

        # Track execution
        self._track_execution(agent_name, 'capability-based', context, capability)

        # Execute
        try:
            # Call capability-specific method if available
            if hasattr(agent, capability):
                method = getattr(agent, capability)
                result = method(context)
            else:
                # Fallback to generic process
                result = agent.process({**context, 'capability': capability})

            return result
        except Exception as e:
            self.logger.error(f"Capability {capability} failed: {e}")
            return {'error': str(e), 'capability': capability, 'agent': agent_name}

    def _find_agent_by_capability(self, capability: str) -> Optional[str]:
        """Find agent that provides capability"""
        for agent_name, capabilities in self.agent_capabilities.items():
            if capability in capabilities:
                return agent_name

        return None

    def _track_execution(self, agent_name: str, routing_type: str, context: Dict, capability: str = None):
        """Track execution for compliance monitoring"""
        self.execution_history.append({
            'agent': agent_name,
            'routing_type': routing_type,
            'capability': capability,
            'timestamp': datetime.now().isoformat()
        })

        # Update compliance rate
        total = len(self.execution_history)
        capability_based = sum(1 for e in self.execution_history if e['routing_type'] == 'capability-based')
        self.registry_compliance_rate = capability_based / total if total > 0 else 1.0

    def get_agent_status(self) -> Dict[str, Any]:
        """Get runtime status"""
        return {
            'total_agents': len(self.agents),
            'registered_capabilities': sum(len(caps) for caps in self.agent_capabilities.values()),
            'total_executions': len(self.execution_history),
            'registry_compliance_rate': self.registry_compliance_rate,
            'agents': list(self.agents.keys())
        }

    def list_capabilities(self) -> Dict[str, List[str]]:
        """List all capabilities by agent"""
        return self.agent_capabilities.copy()
```

**Test AgentRuntime**:
```python
def test_agent_runtime():
    runtime = AgentRuntime(config, knowledge_loader, openbb_adapter)

    # Test 1: Agents registered
    status = runtime.get_agent_status()
    assert status['total_agents'] == 5  # Week 3: 5 core agents
    assert status['registered_capabilities'] > 0

    # Test 2: Name-based routing
    result = runtime.exec_via_registry('claude', {'query': 'test'})
    assert result is not None

    # Test 3: Capability-based routing
    result = runtime.execute_by_capability('can_analyze_text', {'text': 'test'})
    assert result is not None

    # Test 4: Compliance tracking
    status = runtime.get_agent_status()
    assert status['total_executions'] >= 2
```

**Success Criteria**:
- AgentRuntime loads and registers agents
- Name-based routing works
- Capability-based routing works
- Compliance tracking accurate

---

### Day 2: Agent Capabilities Registry

**Source**: `dawsos/core/agent_capabilities.py`
**Destination**: `trinity3/core/agent_capabilities.py`

**Port AGENT_CAPABILITIES**:

```python
# trinity3/core/agent_capabilities.py
"""
Registry of all 103 capabilities and which agents provide them.

This is the source of truth for capability-to-agent mapping.
"""

AGENT_CAPABILITIES = {
    # === CLAUDE AGENT (General Intelligence) ===
    'claude': [
        'can_analyze_text',
        'can_synthesize_analysis',
        'can_generate_insights',
        'can_explain_concepts',
        'can_answer_questions'
    ],

    # === FINANCIAL ANALYST (Equity Analysis) ===
    'financial_analyst': [
        'can_analyze_stock_comprehensive',
        'can_analyze_fundamentals',
        'can_calculate_dcf',
        'can_calculate_valuation_multiples',
        'can_analyze_financial_statements',
        'can_compare_stocks',
        'can_detect_red_flags',
        'can_analyze_business_model',
        'can_assess_management_quality',
        'can_analyze_competitive_position',
        'can_calculate_moat_score',
        'can_generate_investment_thesis',
        'can_analyze_earnings',
        'can_analyze_margins',
        'can_analyze_growth_metrics'
    ],

    # === MACRO ANALYST (Economic Analysis) ===
    'macro_analyst': [
        'can_analyze_economy',
        'can_detect_economic_regime',
        'can_assess_recession_risk',
        'can_analyze_monetary_policy',
        'can_analyze_fiscal_policy',
        'can_analyze_yield_curve',
        'can_analyze_inflation',
        'can_analyze_employment',
        'can_forecast_scenarios',
        'can_analyze_fed_policy',
        'can_analyze_credit_cycle',
        'can_analyze_housing_market',
        'can_analyze_labor_market'
    ],

    # === PORTFOLIO MANAGER (Portfolio Construction) ===
    'portfolio_manager': [
        'can_analyze_portfolio_risk',
        'can_optimize_allocation',
        'can_rebalance_portfolio',
        'can_calculate_portfolio_metrics',
        'can_analyze_concentration',
        'can_analyze_diversification',
        'can_generate_allocation_recommendation',
        'can_backtest_strategy',
        'can_calculate_sharpe_ratio',
        'can_calculate_var',
        'can_stress_test_portfolio'
    ],

    # === RISK ANALYST (Risk Management) ===
    'risk_analyst': [
        'can_assess_risk',
        'can_analyze_volatility',
        'can_calculate_beta',
        'can_analyze_correlations',
        'can_detect_tail_risks',
        'can_analyze_drawdown',
        'can_calculate_risk_metrics',
        'can_identify_risk_factors',
        'can_assess_liquidity_risk',
        'can_assess_credit_risk',
        'can_assess_market_risk'
    ],

    # === DATA PROVIDER (Data Fetching - mapped to OpenBBAdapter) ===
    'data_provider': [
        'can_fetch_stock_quotes',
        'can_fetch_fundamentals',
        'can_fetch_historical_data',
        'can_fetch_economic_data',
        'can_fetch_options_data',
        'can_fetch_insider_trading',
        'can_fetch_institutional_holdings',
        'can_fetch_analyst_ratings',
        'can_fetch_earnings_history',
        'can_fetch_dividend_history',
        'can_fetch_news',
        'can_fetch_social_sentiment'
    ],

    # Week 10: Add remaining 10 agents
    # 'technical_analyst': [...],
    # 'options_analyst': [...],
    # 'sentiment_analyst': [...],
    # 'sector_analyst': [...],
    # 'quant_analyst': [...],
    # 'event_monitor': [...],
    # 'opportunity_scanner': [...],
    # 'compliance_monitor': [...],
    # 'performance_tracker': [...],
    # 'research_librarian': [...]
}

def get_capability_owner(capability: str) -> str:
    """Find which agent owns a capability"""
    for agent, capabilities in AGENT_CAPABILITIES.items():
        if capability in capabilities:
            return agent
    raise ValueError(f"No agent registered for capability: {capability}")

def get_agent_capabilities(agent_name: str) -> List[str]:
    """Get all capabilities for an agent"""
    return AGENT_CAPABILITIES.get(agent_name, [])

def list_all_capabilities() -> List[str]:
    """Get all 103 capabilities"""
    all_caps = []
    for capabilities in AGENT_CAPABILITIES.values():
        all_caps.extend(capabilities)
    return sorted(set(all_caps))
```

**Validate Registry**:
```python
def test_agent_capabilities_registry():
    # Test 1: All agents have capabilities
    for agent, caps in AGENT_CAPABILITIES.items():
        assert len(caps) > 0, f"{agent} has no capabilities"

    # Test 2: No duplicate capabilities
    all_caps = []
    for caps in AGENT_CAPABILITIES.values():
        all_caps.extend(caps)

    assert len(all_caps) == len(set(all_caps)), "Duplicate capabilities found"

    # Test 3: Total is 103
    assert len(all_caps) == 103, f"Expected 103 capabilities, got {len(all_caps)}"

    # Test 4: Helper functions work
    owner = get_capability_owner('can_analyze_fundamentals')
    assert owner == 'financial_analyst'

    caps = get_agent_capabilities('financial_analyst')
    assert 'can_analyze_fundamentals' in caps
```

**Success Criteria**:
- All 103 capabilities documented
- No duplicates
- Helper functions work
- Registry matches DawsOS 2.0

---

### Day 3-5: Core Agents (5 agents)

**Agents to Port in Week 3**:
1. `claude_agent.py` - General intelligence (synthesis, analysis)
2. `financial_analyst.py` - Equity analysis
3. `macro_analyst.py` - Economic analysis
4. `portfolio_manager.py` - Portfolio construction
5. `risk_analyst.py` - Risk management

**Standard Agent Template**:

```python
# trinity3/agents/financial_analyst.py
import logging
from typing import Dict, Any, List

class FinancialAnalyst:
    """Equity analysis specialist"""

    def __init__(self, config, openbb_adapter):
        self.config = config
        self.adapter = openbb_adapter
        self.logger = logging.getLogger(__name__)

        # Register capabilities (matches AGENT_CAPABILITIES)
        self.capabilities = [
            'can_analyze_stock_comprehensive',
            'can_analyze_fundamentals',
            'can_calculate_dcf',
            'can_calculate_valuation_multiples',
            'can_analyze_financial_statements',
            'can_compare_stocks',
            'can_detect_red_flags',
            'can_analyze_business_model',
            'can_assess_management_quality',
            'can_analyze_competitive_position',
            'can_calculate_moat_score',
            'can_generate_investment_thesis',
            'can_analyze_earnings',
            'can_analyze_margins',
            'can_analyze_growth_metrics'
        ]

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generic entry point - routes to capability method"""
        capability = context.get('capability')

        if capability and hasattr(self, capability):
            method = getattr(self, capability)
            return method(context)

        # Fallback: comprehensive analysis
        return self.can_analyze_stock_comprehensive(context)

    # === CAPABILITY IMPLEMENTATIONS ===

    def can_analyze_fundamentals(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze fundamental metrics"""
        symbol = context.get('symbol')

        # Fetch fundamentals from OpenBB
        fundamentals = self.adapter.fetch_fundamentals(symbol)

        # Analyze metrics
        analysis = {
            'symbol': symbol,
            'valuation': self._analyze_valuation(fundamentals),
            'profitability': self._analyze_profitability(fundamentals),
            'growth': self._analyze_growth(fundamentals),
            'health': self._analyze_financial_health(fundamentals)
        }

        return {
            'response': self._format_fundamental_analysis(analysis),
            'data': analysis
        }

    def can_calculate_dcf(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate discounted cash flow valuation"""
        symbol = context.get('symbol')

        # Fetch cash flow data
        fundamentals = self.adapter.fetch_fundamentals(symbol)

        # DCF calculation
        fcf = fundamentals.get('free_cash_flow', 0)
        growth_rate = context.get('growth_rate', 0.05)
        discount_rate = context.get('discount_rate', 0.10)
        terminal_growth = context.get('terminal_growth', 0.03)

        # 5-year projection
        projected_fcf = []
        for year in range(1, 6):
            projected = fcf * ((1 + growth_rate) ** year)
            pv = projected / ((1 + discount_rate) ** year)
            projected_fcf.append(pv)

        # Terminal value
        terminal_fcf = projected_fcf[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
        terminal_pv = terminal_fcf / ((1 + discount_rate) ** 5)

        # Enterprise value
        enterprise_value = sum(projected_fcf) + terminal_pv

        # Equity value (subtract net debt)
        net_debt = fundamentals.get('net_debt', 0)
        equity_value = enterprise_value - net_debt

        # Per share
        shares = fundamentals.get('shares_outstanding', 1)
        fair_value = equity_value / shares

        return {
            'response': f"DCF Fair Value: ${fair_value:.2f}",
            'data': {
                'fair_value': fair_value,
                'enterprise_value': enterprise_value,
                'terminal_value': terminal_pv,
                'projected_fcf': projected_fcf,
                'assumptions': {
                    'growth_rate': growth_rate,
                    'discount_rate': discount_rate,
                    'terminal_growth': terminal_growth
                }
            }
        }

    def can_analyze_stock_comprehensive(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive stock analysis (orchestrates multiple capabilities)"""
        symbol = context.get('symbol')

        # Run multiple analyses
        fundamentals = self.can_analyze_fundamentals({'symbol': symbol})
        dcf = self.can_calculate_dcf({'symbol': symbol})
        moat = self.can_calculate_moat_score({'symbol': symbol})

        # Synthesize
        synthesis = {
            'symbol': symbol,
            'fundamentals': fundamentals['data'],
            'valuation': dcf['data'],
            'moat': moat['data'],
            'recommendation': self._generate_recommendation(fundamentals, dcf, moat)
        }

        return {
            'response': self._format_comprehensive_analysis(synthesis),
            'data': synthesis
        }

    # === HELPER METHODS ===

    def _analyze_valuation(self, fundamentals: Dict) -> Dict:
        """Analyze valuation metrics"""
        pe = fundamentals.get('pe_ratio')
        pb = fundamentals.get('price_to_book')
        ps = fundamentals.get('price_to_sales')

        return {
            'pe_ratio': pe,
            'pb_ratio': pb,
            'ps_ratio': ps,
            'assessment': 'undervalued' if pe and pe < 15 else 'fairly_valued' if pe and pe < 25 else 'overvalued'
        }

    def _analyze_profitability(self, fundamentals: Dict) -> Dict:
        """Analyze profitability metrics"""
        roe = fundamentals.get('roe')
        profit_margin = fundamentals.get('profit_margin')

        return {
            'roe': roe,
            'profit_margin': profit_margin,
            'assessment': 'strong' if roe and roe > 0.15 else 'moderate' if roe and roe > 0.10 else 'weak'
        }

    # ... implement remaining capabilities
```

**Test Core Agents**:
```python
def test_financial_analyst():
    analyst = FinancialAnalyst(config, openbb_adapter)

    # Test 1: Capabilities registered
    assert len(analyst.capabilities) == 15

    # Test 2: Fundamental analysis
    result = analyst.can_analyze_fundamentals({'symbol': 'AAPL'})
    assert 'valuation' in result['data']
    assert 'profitability' in result['data']

    # Test 3: DCF calculation
    result = analyst.can_calculate_dcf({'symbol': 'AAPL'})
    assert 'fair_value' in result['data']
    assert result['data']['fair_value'] > 0

    # Test 4: Comprehensive analysis
    result = analyst.can_analyze_stock_comprehensive({'symbol': 'AAPL'})
    assert 'fundamentals' in result['data']
    assert 'valuation' in result['data']
    assert 'recommendation' in result['data']
```

**Success Criteria**:
- All 5 core agents ported
- Each agent has capabilities list
- All capabilities have implementations
- Tests pass for each agent

---

## Week 10 Tasks

### Day 1-5: Remaining Agents (10 agents)

**Agents to Port**:
1. `technical_analyst.py` - Chart patterns, indicators, trends
2. `options_analyst.py` - Options greeks, unusual flow, strategies
3. `sentiment_analyst.py` - News, social media, sentiment scoring
4. `sector_analyst.py` - Sector rotation, relative strength, trends
5. `quant_analyst.py` - Factor analysis, backtesting, signals
6. `event_monitor.py` - Earnings, dividends, corporate actions
7. `opportunity_scanner.py` - Screen stocks, find opportunities
8. `compliance_monitor.py` - Risk limits, position sizing, alerts
9. `performance_tracker.py` - Track returns, attribution, benchmarks
10. `research_librarian.py` - Knowledge graph, context retrieval

**Standard Template** (same as Week 3):
- Define `capabilities` list
- Implement `process()` method
- Implement each capability as method
- Use OpenBBAdapter for data
- Return standardized format: `{'response': str, 'data': dict}`

**Example - technical_analyst.py**:
```python
class TechnicalAnalyst:
    """Technical analysis specialist"""

    def __init__(self, config, openbb_adapter):
        self.config = config
        self.adapter = openbb_adapter
        self.logger = logging.getLogger(__name__)

        self.capabilities = [
            'can_analyze_technical',
            'can_calculate_indicators',
            'can_detect_patterns',
            'can_identify_support_resistance',
            'can_analyze_momentum',
            'can_analyze_trend'
        ]

    def can_analyze_technical(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Full technical analysis"""
        symbol = context.get('symbol')

        # Fetch historical prices
        historical = self.adapter.fetch_historical_prices(
            symbol=symbol,
            start_date='2024-01-01',
            end_date='2024-10-01'
        )

        # Calculate indicators
        indicators = self._calculate_indicators(historical)

        # Detect patterns
        patterns = self._detect_patterns(historical)

        # Identify levels
        levels = self._identify_support_resistance(historical)

        return {
            'response': self._format_technical_analysis(indicators, patterns, levels),
            'data': {
                'indicators': indicators,
                'patterns': patterns,
                'levels': levels
            }
        }

    # ... implement remaining capabilities
```

**Update AGENT_CAPABILITIES**:
```python
AGENT_CAPABILITIES = {
    # ... existing agents ...

    # Week 10 additions
    'technical_analyst': [
        'can_analyze_technical',
        'can_calculate_indicators',
        'can_detect_patterns',
        'can_identify_support_resistance',
        'can_analyze_momentum',
        'can_analyze_trend'
    ],

    'options_analyst': [
        'can_analyze_options',
        'can_calculate_options_greeks',
        'can_detect_unusual_options',
        'can_analyze_options_flow',
        'can_calculate_options_iv_rank'
    ],

    # ... add remaining 8 agents ...
}
```

**Test All 15 Agents**:
```python
def test_all_agents():
    runtime = AgentRuntime(config, knowledge_loader, openbb_adapter)

    # Test all agents registered
    status = runtime.get_agent_status()
    assert status['total_agents'] == 15

    # Test all capabilities registered
    assert status['registered_capabilities'] == 103

    # Test each agent has capabilities
    for agent_name in runtime.agents.keys():
        caps = runtime.list_capabilities()[agent_name]
        assert len(caps) > 0, f"{agent_name} has no capabilities"

    # Test capability routing works for all 103
    all_caps = list_all_capabilities()
    for cap in all_caps:
        owner = get_capability_owner(cap)
        assert owner in runtime.agents, f"Capability {cap} owner {owner} not registered"
```

**Success Criteria**:
- All 15 agents ported
- All 103 capabilities implemented
- Capability routing works for all
- Tests pass for all agents

---

## Common Issues & Solutions

### Issue 1: Capability Not Found
**Symptom**: `No agent registered for capability: can_xyz`
**Root Cause**: Capability not in AGENT_CAPABILITIES or agent not registered
**Solution**:
1. Check AGENT_CAPABILITIES has capability
2. Check agent's `capabilities` list includes it
3. Check agent registered in runtime

### Issue 2: Agent Method Missing
**Symptom**: `AttributeError: 'FinancialAnalyst' object has no attribute 'can_xyz'`
**Root Cause**: Capability in list but method not implemented
**Solution**: Implement method matching capability name exactly

### Issue 3: Data Provider Capability Routing
**Symptom**: Data fetch capabilities not working
**Root Cause**: `data_provider` is not a real agent, it's the OpenBBAdapter
**Solution**: Special case in runtime:
```python
def execute_by_capability(self, capability: str, context: Dict[str, Any]) -> Dict[str, Any]:
    # Special handling for data capabilities
    if capability.startswith('can_fetch_'):
        return self.openbb_adapter.execute_capability(capability, context)

    # Normal agent routing
    agent_name = self._find_agent_by_capability(capability)
    # ...
```

---

## Resources

- **DawsOS 2.0 Agents**: `dawsos/agents/` (15 files)
- **Capability Registry**: `dawsos/core/agent_capabilities.py`
- **Agent Development Guide**: [docs/AgentDevelopmentGuide.md](../docs/AgentDevelopmentGuide.md)
- **Capability Routing**: [CAPABILITY_ROUTING_GUIDE.md](../CAPABILITY_ROUTING_GUIDE.md)

**Report to**: Migration Lead
**Update**: MIGRATION_STATUS.md weekly
**Escalate**: Missing capabilities, agent failures, routing issues
