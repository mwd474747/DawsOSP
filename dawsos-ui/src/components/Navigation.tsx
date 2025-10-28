'use client'


interface NavigationProps {
  activeTab: string
  setActiveTab: (tab: string) => void
}

export function Navigation({ activeTab, setActiveTab }: NavigationProps) {

  const tabs = [
    { id: 'portfolio', label: 'Portfolio', icon: '📊' },
    { id: 'macro', label: 'Macro', icon: '🌍' },
    { id: 'holdings', label: 'Holdings', icon: '📈' },
    { id: 'scenarios', label: 'Scenarios', icon: '🎯' },
    { id: 'alerts', label: 'Alerts', icon: '🔔' },
    { id: 'reports', label: 'Reports', icon: '📄' },
  ]

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass">
      {/* Top Navigation - 89px (Fib11) */}
      <div className="h-fib9 px-fib8 py-fib5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-fib4">
            <div className="w-fib7 h-fib7 bg-primary-500 rounded-fib3 flex items-center justify-center">
              <span className="text-white font-bold text-lg">D</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">DawsOS</h1>
              <p className="text-xs text-slate-600">Portfolio Intelligence</p>
            </div>
          </div>

          {/* Pack Status Indicator */}
          <div className="flex items-center space-x-fib3">
            <div className="flex items-center space-x-fib2">
              <div className="w-fib2 h-fib2 bg-accent-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-slate-600">Live Data</span>
            </div>
            <div className="text-xs text-slate-500">
              Pack: 2025-10-28
            </div>
          </div>
        </div>
      </div>

      {/* Context Bar - 55px (Fib10) */}
      <div className="h-fib8 bg-white/80 backdrop-blur-sm border-t border-slate-200">
        <div className="max-w-7xl mx-auto px-fib8 py-fib3">
          <div className="flex items-center justify-between">
            {/* Portfolio Context */}
            <div className="flex items-center space-x-fib6">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Main Portfolio</h2>
                <p className="text-sm text-slate-600">$1,247,832.45 • +2.34% today</p>
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex space-x-fib1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-fib5 py-fib3 rounded-fib3 text-sm font-medium transition-all duration-fib2 ${
                    activeTab === tab.id
                      ? 'bg-primary-500 text-white shadow-fib2'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <span className="mr-fib2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
