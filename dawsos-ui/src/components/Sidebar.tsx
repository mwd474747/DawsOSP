'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  LayoutDashboard, 
  TrendingUp, 
  Shield, 
  Target, 
  Cpu, 
  Award, 
  Brain, 
  Bell, 
  BarChart3, 
  Database,
  FileText,
  ChevronDown,
  ChevronRight,
  Settings,
  LogOut
} from 'lucide-react'
import { useState } from 'react'

interface NavItem {
  label: string
  href?: string
  icon: any
  children?: NavItem[]
}

const navigation: NavItem[] = [
  {
    label: 'Dashboard',
    href: '/',
    icon: LayoutDashboard
  },
  {
    label: 'Macro Cycles',
    href: '/macro-cycles',
    icon: TrendingUp,
    children: [
      { label: 'Short-term Debt', href: '/macro-cycles/short-term', icon: null },
      { label: 'Long-term Debt', href: '/macro-cycles/long-term', icon: null },
      { label: 'Empire Cycles', href: '/macro-cycles/empire', icon: null },
      { label: 'Regime Detection', href: '/macro-cycles/regime', icon: null },
      { label: 'DAR Analysis', href: '/macro-cycles/dar', icon: null }
    ]
  },
  {
    label: 'Risk Analytics',
    href: '/risk',
    icon: Shield,
    children: [
      { label: 'VaR & DaR', href: '/risk/var-dar', icon: null },
      { label: 'Factor Exposures', href: '/risk/factors', icon: null },
      { label: 'Concentration', href: '/risk/concentration', icon: null },
      { label: 'Drawdowns', href: '/risk/drawdowns', icon: null }
    ]
  },
  {
    label: 'Scenarios',
    href: '/scenarios',
    icon: Target
  },
  {
    label: 'Optimizer',
    href: '/optimizer',
    icon: Cpu,
    children: [
      { label: 'Trade Proposals', href: '/optimizer/trades', icon: null },
      { label: 'Impact Analysis', href: '/optimizer/impact', icon: null },
      { label: 'Hedging', href: '/optimizer/hedging', icon: null }
    ]
  },
  {
    label: 'Ratings',
    href: '/ratings',
    icon: Award,
    children: [
      { label: 'Dividend Safety', href: '/ratings/dividend', icon: null },
      { label: 'Moat Strength', href: '/ratings/moat', icon: null },
      { label: 'Resilience', href: '/ratings/resilience', icon: null },
      { label: 'Buffett Checklist', href: '/ratings/buffett', icon: null }
    ]
  },
  {
    label: 'AI Insights',
    href: '/ai-insights',
    icon: Brain
  },
  {
    label: 'Alerts',
    href: '/alerts',
    icon: Bell
  },
  {
    label: 'Attribution',
    href: '/attribution',
    icon: BarChart3
  },
  {
    label: 'Market Data',
    href: '/market-data',
    icon: Database
  },
  {
    label: 'Reports',
    href: '/reports',
    icon: FileText
  }
]

export function Sidebar() {
  const pathname = usePathname()
  const [expandedItems, setExpandedItems] = useState<string[]>([])

  const toggleExpand = (label: string) => {
    setExpandedItems(prev => 
      prev.includes(label) 
        ? prev.filter(item => item !== label)
        : [...prev, label]
    )
  }

  const isActive = (href: string) => {
    if (href === '/') {
      return pathname === '/'
    }
    return pathname.startsWith(href)
  }

  const renderNavItem = (item: NavItem) => {
    const hasChildren = item.children && item.children.length > 0
    const isExpanded = expandedItems.includes(item.label)
    const Icon = item.icon
    const active = item.href && isActive(item.href)

    return (
      <div key={item.label}>
        {hasChildren ? (
          <>
            <button
              onClick={() => toggleExpand(item.label)}
              className={`nav-item w-full text-left ${active ? 'active' : ''}`}
            >
              {Icon && <Icon size={18} />}
              <span className="flex-1">{item.label}</span>
              {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
            {isExpanded && (
              <div className="ml-6 mt-1">
                {item.children.map(child => (
                  <Link
                    key={child.label}
                    href={child.href!}
                    className={`nav-item text-xs ${isActive(child.href!) ? 'active' : ''}`}
                  >
                    <span>{child.label}</span>
                  </Link>
                ))}
              </div>
            )}
          </>
        ) : (
          <Link
            href={item.href!}
            className={`nav-item ${active ? 'active' : ''}`}
          >
            {Icon && <Icon size={18} />}
            <span>{item.label}</span>
          </Link>
        )}
      </div>
    )
  }

  return (
    <div className="nav-sidebar">
      {/* Logo Section */}
      <div className="p-6 border-b border-slate-800">
        <h1 className="text-xl font-bold text-blue-400 font-mono">DawsOS</h1>
        <p className="text-xs text-slate-500 mt-1 uppercase tracking-wider">
          Portfolio Intelligence Platform
        </p>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 p-4">
        <div className="space-y-1">
          {navigation.map(renderNavItem)}
        </div>
      </nav>

      {/* Bottom Section */}
      <div className="p-4 border-t border-slate-800">
        <button className="nav-item w-full">
          <Settings size={18} />
          <span>Settings</span>
        </button>
        <button className="nav-item w-full text-red-400">
          <LogOut size={18} />
          <span>Logout</span>
        </button>
      </div>
    </div>
  )
}