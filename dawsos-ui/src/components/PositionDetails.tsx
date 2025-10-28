interface Holding {
  symbol: string
  name: string
  quantity: number
  market_value: number
  cost_basis: number
  unrealized_pnl: number
  weight: number
  currency: string
}

interface PositionHistory {
  date: string
  action: string
  quantity: number
  price: number
  total: number
}

interface PositionDetailsProps {
  holding: Holding
  history: PositionHistory[]
}

export function PositionDetails({ holding, history }: PositionDetailsProps) {
  const currentPrice = holding.market_value / holding.quantity
  const avgCost = holding.cost_basis / holding.quantity
  const pnlPercentage = (holding.unrealized_pnl / holding.cost_basis) * 100

  return (
    <div className="metric-card">
      <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Position Details</h3>
      
      {/* Position Summary */}
      <div className="grid grid-cols-2 gap-fib4 mb-fib6">
        <div className="text-center p-fib4 bg-slate-50 rounded-fib3">
          <div className="text-lg font-bold text-slate-900">{holding.quantity.toLocaleString()}</div>
          <div className="text-xs text-slate-600">Shares</div>
        </div>
        <div className="text-center p-fib4 bg-slate-50 rounded-fib3">
          <div className="text-lg font-bold text-slate-900">{holding.weight}%</div>
          <div className="text-xs text-slate-600">Portfolio Weight</div>
        </div>
      </div>

      {/* Price Information */}
      <div className="space-y-fib4 mb-fib6">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-600">Current Price</span>
          <span className="text-sm font-medium text-slate-900">
            ${currentPrice.toFixed(2)}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-600">Average Cost</span>
          <span className="text-sm font-medium text-slate-900">
            ${avgCost.toFixed(2)}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-600">Market Value</span>
          <span className="text-sm font-medium text-slate-900">
            ${holding.market_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-600">Cost Basis</span>
          <span className="text-sm font-medium text-slate-900">
            ${holding.cost_basis.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="flex items-center justify-between border-t border-slate-200 pt-fib3">
          <span className="text-sm font-medium text-slate-900">Unrealized P&L</span>
          <span className={`text-sm font-medium ${
            holding.unrealized_pnl >= 0 ? 'profit' : 'loss'
          }`}>
            ${holding.unrealized_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            <span className="ml-fib2">
              ({pnlPercentage >= 0 ? '+' : ''}{pnlPercentage.toFixed(1)}%)
            </span>
          </span>
        </div>
      </div>

      {/* Transaction History */}
      <div>
        <h4 className="text-sm font-medium text-slate-900 mb-fib3">Transaction History</h4>
        <div className="space-y-fib2">
          {history.map((transaction, index) => (
            <div key={index} className="flex items-center justify-between p-fib3 bg-slate-50 rounded-fib2">
              <div className="flex items-center space-x-fib3">
                <div className={`w-fib2 h-fib2 rounded-full ${
                  transaction.action === 'Buy' ? 'bg-accent-500' : 'bg-red-500'
                }`}></div>
                <div>
                  <div className="text-sm font-medium text-slate-900">
                    {transaction.action} {transaction.quantity} shares
                  </div>
                  <div className="text-xs text-slate-600">{transaction.date}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-slate-900">
                  ${transaction.price.toFixed(2)}
                </div>
                <div className="text-xs text-slate-600">
                  ${transaction.total.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
