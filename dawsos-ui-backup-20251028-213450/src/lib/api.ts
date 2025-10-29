// API client for DawsOS backend integration
export class DawsOSAPI {
  private baseURL: string
  private token: string | null = null

  constructor(baseURL?: string) {
    this.baseURL = baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }

  setToken(token: string) {
    this.token = token
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${this.baseURL}${endpoint}`
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
      ...options.headers,
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  // Pattern execution
  async executePattern(patternId: string, inputs: any) {
    return this.request('/v1/execute', {
      method: 'POST',
      body: JSON.stringify({
        pattern_id: patternId,
        inputs,
      }),
    })
  }

  // Portfolio patterns
  async getPortfolioOverview(portfolioId: string, lookbackDays: number = 30) {
    return this.executePattern('portfolio_overview', {
      portfolio_id: portfolioId,
      lookback_days: lookbackDays,
    })
  }

  async getBuffettChecklist(securityId: string) {
    return this.executePattern('buffett_checklist', {
      security_id: securityId,
    })
  }

  async getPolicyRebalance(portfolioId: string, policies: any, constraints: any) {
    return this.executePattern('policy_rebalance', {
      portfolio_id: portfolioId,
      policies,
      constraints,
    })
  }

  // Macro patterns
  async getMacroCyclesOverview(asofDate?: string) {
    return this.executePattern('macro_cycles_overview', {
      asof_date: asofDate,
    })
  }

  async getPortfolioMacroOverview(portfolioId: string) {
    return this.executePattern('portfolio_macro_overview', {
      portfolio_id: portfolioId,
    })
  }

  async getPortfolioCycleRisk(portfolioId: string) {
    return this.executePattern('portfolio_cycle_risk', {
      portfolio_id: portfolioId,
    })
  }

  // Scenario patterns
  async getPortfolioScenarioAnalysis(portfolioId: string, scenarios: any) {
    return this.executePattern('portfolio_scenario_analysis', {
      portfolio_id: portfolioId,
      scenarios,
    })
  }

  async getCycleDeleveragingScenarios(portfolioId: string, ltdcPhase: string) {
    return this.executePattern('cycle_deleveraging_scenarios', {
      portfolio_id: portfolioId,
      ltdc_phase: ltdcPhase,
    })
  }

  // News patterns
  async getNewsImpactAnalysis(portfolioId: string, entities: string[], lookbackHours: number = 24) {
    return this.executePattern('news_impact_analysis', {
      portfolio_id: portfolioId,
      entities,
      lookback_hours: lookbackHours,
    })
  }

  // Export patterns
  async exportPortfolioReport(portfolioId: string, templateName: string = 'portfolio_summary') {
    return this.executePattern('export_portfolio_report', {
      portfolio_id: portfolioId,
      template_name: templateName,
    })
  }

  // Trend monitoring
  async getMacroTrendMonitor(asofDate?: string) {
    return this.executePattern('macro_trend_monitor', {
      asof_date: asofDate,
    })
  }

  // Authentication
  async login(email: string, password: string) {
    const response = await this.request('/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    
    if (response.access_token) {
      this.setToken(response.access_token)
    }
    
    return response
  }

  async refreshToken() {
    return this.request('/v1/auth/refresh', {
      method: 'POST',
    })
  }

  async getUserInfo() {
    return this.request('/v1/auth/me')
  }
}

// Singleton instance
export const api = new DawsOSAPI()
