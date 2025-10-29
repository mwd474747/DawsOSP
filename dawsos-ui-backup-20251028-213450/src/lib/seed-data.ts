// Demo data for UAT testing
export const demoPortfolioData = {
  portfolio_id: "demo-portfolio-001",
  name: "Demo Portfolio",
  total_value: 1250000.00,
  total_return: 0.0875,
  total_return_pct: 8.75,
  positions: [
    {
      security_id: "AAPL",
      symbol: "AAPL",
      name: "Apple Inc.",
      weight: 0.15,
      value: 187500.00,
      return: 0.12,
      return_pct: 12.0
    },
    {
      security_id: "MSFT",
      symbol: "MSFT", 
      name: "Microsoft Corporation",
      weight: 0.12,
      value: 150000.00,
      return: 0.08,
      return_pct: 8.0
    },
    {
      security_id: "GOOGL",
      symbol: "GOOGL",
      name: "Alphabet Inc.",
      weight: 0.10,
      value: 125000.00,
      return: 0.15,
      return_pct: 15.0
    }
  ]
};

export const demoMacroData = {
  current_regime: "Expansion",
  regime_confidence: 0.85,
  key_indicators: {
    gdp_growth: 2.3,
    inflation: 3.2,
    unemployment: 3.8,
    fed_funds_rate: 5.25
  },
  factor_exposures: {
    market: 0.95,
    size: -0.12,
    value: 0.08,
    momentum: 0.15
  }
};

export const demoAlertsData = [
  {
    id: "alert-001",
    type: "Risk",
    severity: "High",
    title: "Portfolio Concentration Risk",
    message: "Portfolio is 37% concentrated in technology sector",
    timestamp: new Date().toISOString(),
    status: "Active"
  },
  {
    id: "alert-002", 
    type: "Performance",
    severity: "Medium",
    title: "Underperforming Position",
    message: "MSFT position underperforming benchmark by 2.5%",
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    status: "Active"
  }
];

export const demoScenariosData = [
  {
    id: "scenario-001",
    name: "Market Crash (-30%)",
    probability: 0.15,
    portfolio_impact: -0.28,
    key_risks: ["Equity market collapse", "Credit spread widening"]
  },
  {
    id: "scenario-002",
    name: "Recession (-15%)",
    probability: 0.25,
    portfolio_impact: -0.14,
    key_risks: ["Economic contraction", "Earnings decline"]
  }
];

export const demoReportsData = [
  {
    id: "report-001",
    name: "Monthly Portfolio Report",
    type: "PDF",
    generated_at: new Date().toISOString(),
    status: "Ready",
    download_url: "/api/reports/monthly-portfolio-report.pdf"
  },
  {
    id: "report-002",
    name: "Risk Analysis Report", 
    type: "PDF",
    generated_at: new Date(Date.now() - 86400000).toISOString(),
    status: "Ready",
    download_url: "/api/reports/risk-analysis-report.pdf"
  }
];
