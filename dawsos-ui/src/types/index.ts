// TypeScript types for DawsOS API responses
export interface PortfolioData {
  portfolio_id: string
  portfolio_name: string
  total_value: number
  currency: string
  positions: Position[]
  performance: PerformanceMetrics
  attribution: AttributionData
  metadata: PortfolioMetadata
}

export interface Position {
  security_id: string
  symbol: string
  name: string
  quantity: number
  market_value: number
  weight: number
  cost_basis: number
  unrealized_pnl: number
  realized_pnl: number
  currency: string
}

export interface PerformanceMetrics {
  twr_1d: number
  twr_1w: number
  twr_1m: number
  twr_3m: number
  twr_6m: number
  twr_1y: number
  twr_ytd: number
  sharpe_ratio: number
  max_drawdown: number
  volatility: number
}

export interface AttributionData {
  currency_attribution: CurrencyAttribution[]
  sector_attribution: SectorAttribution[]
  factor_attribution: FactorAttribution[]
}

export interface CurrencyAttribution {
  currency: string
  weight: number
  contribution: number
  fx_impact: number
}

export interface SectorAttribution {
  sector: string
  weight: number
  contribution: number
  benchmark_weight: number
  active_weight: number
}

export interface FactorAttribution {
  factor: string
  exposure: number
  contribution: number
  risk_contribution: number
}

export interface PortfolioMetadata {
  asof_date: string
  pricing_pack_id: string
  last_updated: string
  data_providers: string[]
}

export interface MacroData {
  regime: string
  regime_confidence: number
  cycle_phase: string
  cycle_confidence: number
  indicators: MacroIndicator[]
  scenarios: Scenario[]
  dar: number
}

export interface MacroIndicator {
  name: string
  value: number
  change: number
  change_pct: number
  trend: 'up' | 'down' | 'flat'
  significance: 'high' | 'medium' | 'low'
}

export interface Scenario {
  id: string
  name: string
  description: string
  probability: number
  impact: number
  regime: string
  factors: string[]
}

export interface BuffettRating {
  security_id: string
  symbol: string
  dividend_safety: number
  moat_strength: number
  resilience: number
  overall_score: number
  recommendation: 'buy' | 'hold' | 'sell'
  rationale: string
}

export interface Alert {
  id: string
  portfolio_id: string
  condition: string
  threshold: number
  current_value: number
  status: 'active' | 'triggered' | 'disabled'
  created_at: string
  last_triggered: string | null
}

export interface Report {
  id: string
  portfolio_id: string
  template_name: string
  generated_at: string
  file_size: number
  download_url: string
  attributions: string[]
  watermark: string | null
}

export interface APIResponse<T = any> {
  success: boolean
  data: T
  error?: string
  execution_time_ms: number
  pattern_id: string
  timestamp: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: {
    id: string
    email: string
    role: string
  }
}

export interface User {
  id: string
  email: string
  role: 'VIEWER' | 'USER' | 'MANAGER' | 'ADMIN'
  permissions: string[]
  created_at: string
  last_login: string
}
