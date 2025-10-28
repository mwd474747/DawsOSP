'use client'

import { useState } from 'react'
import { Navigation } from '@/components/Navigation'
import { PortfolioOverview } from '@/components/PortfolioOverview'
import { MacroDashboard } from '@/components/MacroDashboard'
import { HoldingsDetail } from '@/components/HoldingsDetail'
import { Scenarios } from '@/components/Scenarios'
import { Alerts } from '@/components/Alerts'
import { Reports } from '@/components/Reports'

export default function Home() {
  const [activeTab, setActiveTab] = useState('portfolio')

  const renderContent = () => {
    switch (activeTab) {
      case 'portfolio':
        return <PortfolioOverview />
      case 'macro':
        return <MacroDashboard />
      case 'holdings':
        return <HoldingsDetail />
      case 'scenarios':
        return <Scenarios />
      case 'alerts':
        return <Alerts />
      case 'reports':
        return <Reports />
      default:
        return <PortfolioOverview />
    }
  }

  return (
    <main className="min-h-screen">
      <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="pt-fib10"> {/* Account for fixed navigation */}
        {renderContent()}
      </div>
    </main>
  )
}