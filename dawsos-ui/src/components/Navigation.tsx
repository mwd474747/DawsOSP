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
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
      <div className="h-16 px-8 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-4">
            <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
              <span className="text-white font-bold text-lg">D</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white">DawsOS</h1>
              <p className="text-sm text-slate-600 dark:text-slate-400">Portfolio Intelligence</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex space-x-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-white dark:hover:bg-slate-800'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}