interface Holding {
  symbol: string
  name: string
  quantity: number
  value: number
  weight: number
  change: string
}

interface HoldingsTableProps {
  holdings: Holding[]
}

export function HoldingsTable({ holdings }: HoldingsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-200">
            <th className="text-left py-fib3 px-fib4 text-sm font-medium text-slate-600">Symbol</th>
            <th className="text-left py-fib3 px-fib4 text-sm font-medium text-slate-600">Name</th>
            <th className="text-right py-fib3 px-fib4 text-sm font-medium text-slate-600">Quantity</th>
            <th className="text-right py-fib3 px-fib4 text-sm font-medium text-slate-600">Value</th>
            <th className="text-right py-fib3 px-fib4 text-sm font-medium text-slate-600">Weight</th>
            <th className="text-right py-fib3 px-fib4 text-sm font-medium text-slate-600">Change</th>
          </tr>
        </thead>
        <tbody>
          {holdings.map((holding, index) => (
            <tr key={index} className="border-b border-slate-100 hover:bg-slate-50">
              <td className="py-fib4 px-fib4">
                <div className="font-medium text-slate-900">{holding.symbol}</div>
              </td>
              <td className="py-fib4 px-fib4">
                <div className="text-sm text-slate-600">{holding.name}</div>
              </td>
              <td className="py-fib4 px-fib4 text-right">
                <div className="text-sm text-slate-900">{holding.quantity.toLocaleString()}</div>
              </td>
              <td className="py-fib4 px-fib4 text-right">
                <div className="text-sm font-medium text-slate-900">
                  ${holding.value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
              </td>
              <td className="py-fib4 px-fib4 text-right">
                <div className="text-sm text-slate-600">{holding.weight}%</div>
              </td>
              <td className="py-fib4 px-fib4 text-right">
                <div className={`text-sm font-medium ${
                  holding.change.startsWith('+') ? 'profit' : 
                  holding.change.startsWith('-') ? 'loss' : 
                  'neutral'
                }`}>
                  {holding.change}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
