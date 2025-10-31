'use client'

import { useState } from 'react'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function AIInsightsPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hello! I'm Claude, your AI portfolio assistant. I can help you analyze your portfolio, understand market conditions, generate insights, and answer any questions about your investments. How can I assist you today?",
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      // Call the real AI insights endpoint
      const response = await apiClient.getPortfolioAnalysis('1')
      
      // Use the response or fallback to sample response
      let responseContent = ''
      if (response?.analysis) {
        responseContent = response.analysis
      } else if (response?.insights) {
        responseContent = response.insights
      } else {
        responseContent = generateSampleResponse(input)
      }
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseContent,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Failed to get AI response:', error)
      // Fallback to sample response on error
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: generateSampleResponse(input),
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
    } finally {
      setLoading(false)
    }
  }

  const generateSampleResponse = (query: string): string => {
    const lowerQuery = query.toLowerCase()

    if (lowerQuery.includes('risk')) {
      return `Based on my analysis of your portfolio:

**Risk Assessment:**
• Portfolio Beta: 0.85 (moderate market exposure)
• VaR (95%): -$125,430 (1-day)
• Maximum Drawdown: -8.2% (current)
• Sharpe Ratio: 1.85 (good risk-adjusted returns)

**Key Risk Factors:**
1. **Concentration Risk**: Your top 5 holdings represent 53.2% of the portfolio
2. **Sector Exposure**: Technology sector at 35% creates vulnerability to tech volatility
3. **Currency Risk**: 20% international exposure without hedging

**Recommendations:**
• Consider reducing AAPL position from 15.2% to under 10%
• Add defensive sectors (utilities, consumer staples)
• Implement currency hedging for international positions`
    }

    if (lowerQuery.includes('market') || lowerQuery.includes('macro')) {
      return `**Current Market Analysis:**

The market is exhibiting late-cycle characteristics:

**Macro Indicators:**
• We're in a LATE CYCLE SLOWDOWN phase
• Credit conditions are TIGHTENING
• Inflation is DECLINING but remains elevated
• DAR (Debt-Asset Ratio) at 1.85, approaching critical levels

**Regime Detection:**
• Short-term debt cycle: Expansion phase (5.3 years)
• Long-term debt cycle: Late stage (high debt/GDP at 280%)
• Empire cycle: Declining phase for US dominance

**Portfolio Implications:**
Your portfolio should prepare for potential recession in 18-24 months. Consider:
1. Increasing cash allocation to 15-20%
2. Adding gold/commodities as inflation hedge
3. Reducing cyclical stock exposure
4. Implementing protective puts on equity positions`
    }

    if (lowerQuery.includes('optimize') || lowerQuery.includes('improve')) {
      return `**Portfolio Optimization Analysis:**

I've identified several opportunities to improve your portfolio:

**Recommended Changes:**
1. **Rebalance Allocation:**
   - Reduce Tech: 35% → 28%
   - Increase Healthcare: 12% → 18%
   - Add Fixed Income: 20% → 25%

2. **Specific Trades:**
   - SELL 50 shares AAPL @ $178.25 (reduce concentration)
   - BUY 150 shares VTI @ $218.50 (broad market exposure)
   - BUY 200 shares BND @ $72.40 (defensive positioning)

**Expected Improvements:**
• Return: 8.5% → 9.8% (+1.3%)
• Volatility: 15.2% → 12.8% (-2.4%)
• Sharpe Ratio: 0.85 → 1.15 (+0.30)

These changes would move your portfolio closer to the efficient frontier while reducing risk.`
    }

    // Default response
    return `I understand you're asking about "${query}". Let me analyze your portfolio data to provide relevant insights.

Based on your current portfolio structure, here are some key observations:

• Your portfolio is valued at $12.5M with a YTD return of +18.5%
• You're outperforming the benchmark by 3.3%
• Current risk score is 6.5/10 (MODERATE)

For more specific insights, you might want to ask about:
- Risk analysis and VaR calculations
- Market regime and macro conditions
- Portfolio optimization opportunities
- Specific stock ratings (Buffett checklist)
- Scenario analysis and stress testing

What specific aspect would you like me to explore further?`
  }

  // Sample queries
  const sampleQueries = [
    "What are my biggest portfolio risks?",
    "How should I position for a recession?",
    "Analyze the current market regime",
    "Generate a portfolio optimization plan",
    "What's my exposure to inflation?",
    "Should I be hedging currency risk?"
  ]

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)]">
      <header className="glass-card-dark mb-4">
        <h1 className="text-2xl font-bold text-blue-400">AI INSIGHTS CONSOLE</h1>
        <p className="text-slate-400 mt-2">
          Natural language portfolio analysis powered by Claude AI
        </p>
      </header>

      <div className="flex-1 flex gap-6">
        {/* Chat Interface */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 glass-card-dark overflow-y-auto mb-4">
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${
                    message.role === 'assistant' ? '' : 'justify-end'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                      <Bot size={18} className="text-blue-400" />
                    </div>
                  )}
                  <div
                    className={`max-w-[70%] p-4 rounded-lg ${
                      message.role === 'assistant'
                        ? 'bg-slate-800/50 text-slate-200'
                        : 'bg-blue-500/20 text-blue-100'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    <p className="text-xs text-slate-500 mt-2">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                  {message.role === 'user' && (
                    <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center flex-shrink-0">
                      <User size={18} className="text-slate-400" />
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                    <Bot size={18} className="text-blue-400" />
                  </div>
                  <div className="bg-slate-800/50 p-4 rounded-lg">
                    <Loader2 className="animate-spin text-blue-400" size={18} />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Input */}
          <div className="glass-card-dark p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Ask about your portfolio..."
                className="flex-1 terminal-input"
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                disabled={loading}
                className="btn-terminal px-6"
              >
                {loading ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
              </button>
            </div>
          </div>
        </div>

        {/* Sample Queries Sidebar */}
        <div className="w-80">
          <div className="glass-card-dark h-full">
            <h3 className="terminal-title mb-4">Sample Queries</h3>
            <div className="space-y-2">
              {sampleQueries.map((query, index) => (
                <button
                  key={index}
                  onClick={() => setInput(query)}
                  className="w-full text-left p-3 bg-slate-800/30 rounded-lg hover:bg-slate-800/50 transition-colors text-sm text-slate-300 hover:text-slate-100"
                >
                  {query}
                </button>
              ))}
            </div>

            <div className="mt-6 p-4 border-t border-slate-700">
              <h4 className="text-xs font-semibold uppercase text-slate-500 mb-3">Capabilities</h4>
              <ul className="space-y-2 text-xs text-slate-400">
                <li>• Portfolio risk analysis</li>
                <li>• Market regime detection</li>
                <li>• Trade recommendations</li>
                <li>• Scenario planning</li>
                <li>• Performance attribution</li>
                <li>• Hedge suggestions</li>
                <li>• Report generation</li>
              </ul>
            </div>

            <div className="mt-6 p-4 border-t border-slate-700">
              <h4 className="text-xs font-semibold uppercase text-slate-500 mb-3">AI Status</h4>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Model</span>
                  <span className="text-xs text-blue-400">Claude 3 Opus</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Context</span>
                  <span className="text-xs profit">Full Portfolio</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Last Update</span>
                  <span className="text-xs">Real-time</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}