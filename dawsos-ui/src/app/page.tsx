import Link from 'next/link';

// Force dynamic rendering
export const dynamic = 'force-dynamic'

const stats = [
  { label: 'Total Value', value: '$1,234,567', change: '+12.5%', trend: 'up' },
  { label: "Today's P&L", value: '+$12,345', change: '+2.3%', trend: 'up' },
  { label: 'YTD Return', value: '+15.2%', change: '+0.8%', trend: 'up' },
  { label: 'Sharpe Ratio', value: '1.85', change: '+0.12', trend: 'up' },
];

const cards = [
  {
    href: '/portfolio',
    title: 'Portfolio Overview',
    description: 'Comprehensive portfolio analysis with KPIs and performance metrics',
    emoji: '📊'
  },
  {
    href: '/macro',
    title: 'Macro Dashboard',
    description: 'Market regime analysis, economic cycles, and factor monitoring',
    emoji: '🌍'
  },
  {
    href: '/holdings',
    title: 'Holdings Detail',
    description: 'Detailed holdings analysis with risk metrics and attribution',
    emoji: '📈'
  },
  {
    href: '/scenarios',
    title: 'Scenarios',
    description: 'Stress testing and what-if analysis for portfolio assessment',
    emoji: '🎯'
  },
  {
    href: '/alerts',
    title: 'Alerts',
    description: 'Real-time alert management and risk monitoring system',
    emoji: '🔔'
  },
  {
    href: '/reports',
    title: 'Reports',
    description: 'Generate comprehensive PDF reports and export portfolio data',
    emoji: '📄'
  }
];

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-full blur-3xl animate-float" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-br from-green-500/10 to-blue-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 right-1/3 w-72 h-72 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '4s' }} />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8 py-8">
        <div className="text-center mb-12">
          <h1 className="text-5xl lg:text-6xl font-bold mb-4">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              DawsOS Portfolio
            </span>
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
              Intelligence
            </span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Advanced portfolio analysis and risk management platform with real-time insights
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="glass-card-dark p-6 hover:scale-105 transition-transform duration-300"
            >
              <div className="flex justify-between items-start mb-2">
                <p className="text-sm text-slate-400">{stat.label}</p>
                <span className={stat.trend === 'up' ? 'text-green-400' : 'text-red-400'}>
                  {stat.trend === 'up' ? '↑' : '↓'}
                </span>
              </div>
              <p className="text-3xl font-bold text-white mb-1">{stat.value}</p>
              <div className="flex items-center gap-2">
                <span className={`text-sm ${stat.trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
                  {stat.change}
                </span>
                <span className="text-xs text-slate-500">24h</span>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cards.map((card) => (
            <Link key={card.href} href={card.href}>
              <div className="glass-card-dark p-6 h-full hover:shadow-glow hover:scale-105 transition-all duration-300 cursor-pointer">
                <div className="flex items-start justify-between mb-4">
                  <div className="text-4xl">{card.emoji}</div>
                  <span className="text-slate-500">→</span>
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  {card.title}
                </h3>
                <p className="text-slate-400">
                  {card.description}
                </p>
              </div>
            </Link>
          ))}
        </div>

        <div className="mt-12 text-center">
          <div className="inline-flex gap-4">
            <button className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full font-semibold hover:shadow-glow transition-all duration-300 hover:scale-105">
              ⚡ Quick Analysis
            </button>
            <button className="px-8 py-3 glass-card-dark text-white rounded-full font-semibold hover:shadow-glow transition-all duration-300 hover:scale-105">
              💰 Market Overview
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}