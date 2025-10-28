import Link from 'next/link'

// Force dynamic rendering
export const dynamic = 'force-dynamic'

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto px-8 py-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            DawsOS Portfolio Intelligence
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Advanced portfolio analysis and risk management platform
          </p>
        </div>

        {/* Navigation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <Link href="/portfolio" className="group">
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 hover:shadow-md transition-shadow">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center mr-4">
                  <span className="text-white text-xl">📊</span>
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-white">Portfolio Overview</h3>
              </div>
              <p className="text-slate-600 dark:text-slate-400">
                Comprehensive portfolio analysis with KPIs, performance metrics, and attribution analysis.
              </p>
            </div>
          </Link>

          <Link href="/macro" className="group">
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 hover:shadow-md transition-shadow">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center mr-4">
                  <span className="text-white text-xl">🌍</span>
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-white">Macro Dashboard</h3>
              </div>
              <p className="text-slate-600 dark:text-slate-400">
                Market regime analysis, economic cycles, and factor exposure monitoring.
              </p>
            </div>
          </Link>

          <Link href="/holdings" className="group">
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 hover:shadow-md transition-shadow">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center mr-4">
                  <span className="text-white text-xl">📈</span>
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-white">Holdings Detail</h3>
              </div>
              <p className="text-slate-600 dark:text-slate-400">
                Detailed holdings analysis with risk metrics and performance attribution.
              </p>
            </div>
          </Link>

          <Link href="/scenarios" className="group">
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 hover:shadow-md transition-shadow">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-orange-500 rounded-lg flex items-center justify-center mr-4">
                  <span className="text-white text-xl">🎯</span>
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-white">Scenarios</h3>
              </div>
              <p className="text-slate-600 dark:text-slate-400">
                Stress testing and what-if analysis for portfolio risk assessment.
              </p>
            </div>
          </Link>

          <Link href="/alerts" className="group">
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 hover:shadow-md transition-shadow">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center mr-4">
                  <span className="text-white text-xl">🔔</span>
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-white">Alerts</h3>
              </div>
              <p className="text-slate-600 dark:text-slate-400">
                Real-time alert management and risk monitoring system.
              </p>
            </div>
          </Link>

          <Link href="/reports" className="group">
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 hover:shadow-md transition-shadow">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-indigo-500 rounded-lg flex items-center justify-center mr-4">
                  <span className="text-white text-xl">📄</span>
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-white">Reports</h3>
              </div>
              <p className="text-slate-600 dark:text-slate-400">
                Generate comprehensive PDF reports and export portfolio data.
              </p>
            </div>
          </Link>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <h3 className="text-sm font-medium text-slate-600 dark:text-slate-400">Total Value</h3>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">$1,234,567</p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <h3 className="text-sm font-medium text-slate-600 dark:text-slate-400">Today's P&L</h3>
            <p className="text-2xl font-bold text-green-600">+$12,345</p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <h3 className="text-sm font-medium text-slate-600 dark:text-slate-400">YTD Return</h3>
            <p className="text-2xl font-bold text-green-600">+15.2%</p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <h3 className="text-sm font-medium text-slate-600 dark:text-slate-400">Sharpe Ratio</h3>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">1.85</p>
          </div>
        </div>
      </div>
    </main>
  )
}