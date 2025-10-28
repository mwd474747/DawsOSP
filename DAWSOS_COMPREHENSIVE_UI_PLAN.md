# DawsOS — Comprehensive UI/UX Implementation Plan
## Professional-Grade Design System with shadcn/ui & Divine Proportions

**Created**: October 28, 2025
**Status**: Complete Specification Ready for Implementation
**Target**: Next.js 14 + shadcn/ui + Tailwind CSS 3.4
**Philosophy**: Divine Geometry × Bloomberg Terminal × Apple Design Language

---

## 🎯 **Executive Summary**

This document provides a **complete, production-ready UI/UX specification** for DawsOS that:

1. **Integrates Divine Proportions** - Fibonacci spacing, golden ratio layouts, mathematically harmonious design
2. **Uses shadcn/ui** - Professional, accessible component library built on Radix UI
3. **Reflects Product Roadmap** - Every UI element mapped to backend capabilities and patterns
4. **Looks Like a Professional Firm** - Bloomberg-quality aesthetics, Apple-level polish
5. **Supports Full Feature Set** - Portfolio overview, macro analysis, scenarios, ratings, alerts, reports

**Design Principles**:
- ✨ **Subtle Luxury** - Expensive without being loud
- 📐 **Mathematical Precision** - Every measurement from Fibonacci/golden ratio
- 🎨 **Professional Restraint** - Clean, dark, sophisticated
- ⚡ **Instant Feedback** - Micro-interactions, loading states, optimistic UI
- 📊 **Data Dense** - Bloomberg-style information density without clutter

---

## 📋 **Table of Contents**

1. [Design System Foundation](#1-design-system-foundation)
2. [Navigation Architecture](#2-navigation-architecture)
3. [Page-by-Page Specifications](#3-page-by-page-specifications)
4. [Component Library](#4-component-library)
5. [Data Visualization System](#5-data-visualization-system)
6. [shadcn/ui Integration Guide](#6-shadcnui-integration-guide)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [Technical Stack](#8-technical-stack)

---

## 1. Design System Foundation

### 1.1 Divine Proportions Color System

Building on our divine proportions specification with shadcn/ui integration:

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        // Base (Divine Proportions)
        background: 'hsl(220, 13%, 9%)',    // Fib-based darkness
        surface: 'hsl(217, 12%, 14%)',      // Cards, elevated
        elevated: 'hsl(217, 12%, 18%)',     // Hover states
        overlay: 'hsl(217, 12%, 22%)',      // Modals

        // Brand (Golden Angle Distribution)
        primary: {
          DEFAULT: 'hsl(180, 100%, 32%)',   // Signal teal (180°)
          50: 'hsl(180, 100%, 96%)',
          100: 'hsl(180, 100%, 88%)',
          200: 'hsl(180, 100%, 76%)',
          300: 'hsl(180, 100%, 64%)',
          400: 'hsl(180, 100%, 48%)',
          500: 'hsl(180, 100%, 32%)',       // Base
          600: 'hsl(180, 100%, 24%)',
          700: 'hsl(180, 100%, 18%)',
          800: 'hsl(180, 100%, 12%)',
          900: 'hsl(180, 100%, 8%)',
        },

        // Accent 1 (Golden Angle +252° = 72°)
        accent: {
          DEFAULT: 'hsl(72, 88%, 42%)',
          warm: 'hsl(72, 88%, 42%)',
        },

        // Accent 2 (Golden Angle +137.5° = 209.5°)
        electric: {
          DEFAULT: 'hsl(209, 100%, 48%)',
          blue: 'hsl(209, 100%, 48%)',
        },

        // Accent 3 (Golden Angle +36° = 245.5°)
        provenance: {
          DEFAULT: 'hsl(245, 67%, 48%)',
          purple: 'hsl(245, 67%, 48%)',
        },

        // Text
        foreground: 'hsl(220, 10%, 96%)',   // High contrast
        muted: {
          DEFAULT: 'hsl(220, 10%, 48%)',
          foreground: 'hsl(220, 10%, 72%)',
        },

        // Functional (shadcn/ui compatible)
        destructive: {
          DEFAULT: 'hsl(0, 72%, 51%)',
          foreground: 'hsl(0, 0%, 100%)',
        },
        success: {
          DEFAULT: 'hsl(142, 76%, 36%)',
          foreground: 'hsl(0, 0%, 100%)',
        },
        warning: {
          DEFAULT: 'hsl(38, 92%, 50%)',
          foreground: 'hsl(0, 0%, 100%)',
        },

        // shadcn/ui semantic tokens
        border: 'hsl(220, 10%, 25%)',
        input: 'hsl(220, 10%, 25%)',
        ring: 'hsl(180, 100%, 32%)',

        // Chart colors (golden angle distributed)
        chart: {
          '1': 'hsl(180, 100%, 32%)',      // Primary teal
          '2': 'hsl(209, 100%, 48%)',      // Electric blue
          '3': 'hsl(245, 67%, 48%)',       // Provenance purple
          '4': 'hsl(72, 88%, 42%)',        // Accent warm
          '5': 'hsl(142, 76%, 36%)',       // Success green
        },
      },

      // Fibonacci Spacing
      spacing: {
        'fib-1': '2px',    // Fib(3) - Hairline
        'fib-2': '3px',    // Fib(4) - Micro
        'fib-3': '5px',    // Fib(5) - Tiny
        'fib-4': '8px',    // Fib(6) - Base
        'fib-5': '13px',   // Fib(7) - Small
        'fib-6': '21px',   // Fib(8) - Medium
        'fib-7': '34px',   // Fib(9) - Large
        'fib-8': '55px',   // Fib(10) - XLarge
        'fib-9': '89px',   // Fib(11) - XXLarge
        'fib-10': '144px', // Fib(12) - Massive
      },

      // Typography (Fibonacci-based)
      fontSize: {
        'xs': ['13px', { lineHeight: '1.5' }],     // Fib(7)
        'sm': ['16px', { lineHeight: '1.5' }],
        'base': ['21px', { lineHeight: '1.6' }],   // Fib(8)
        'lg': ['27px', { lineHeight: '1.4' }],
        'xl': ['34px', { lineHeight: '1.3' }],     // Fib(9)
        '2xl': ['55px', { lineHeight: '1.2' }],    // Fib(10)
        '3xl': ['89px', { lineHeight: '1.1' }],    // Fib(11)
      },

      // Border Radius (Fibonacci)
      borderRadius: {
        'fib-sm': '3px',   // Fib(4)
        'fib-md': '5px',   // Fib(5)
        'fib-lg': '8px',   // Fib(6)
        'fib-xl': '13px',  // Fib(7)
      },

      // Animation Timing (Fibonacci ms)
      transitionDuration: {
        'fib-fast': '89ms',    // Fib(11)
        'fib-normal': '144ms', // Fib(12)
        'fib-slow': '233ms',   // Fib(13)
        'fib-slower': '377ms', // Fib(14)
      },

      // Box Shadow (φ-based opacity)
      boxShadow: {
        'divine-sm': '0 2px 5px hsla(220, 13%, 0%, 0.21)',
        'divine-md': '0 5px 13px hsla(220, 13%, 0%, 0.13)',
        'divine-lg': '0 13px 34px hsla(220, 13%, 0%, 0.08)',
        'divine-xl': '0 21px 55px hsla(220, 13%, 0%, 0.05)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
```

### 1.2 Typography System

```typescript
// lib/fonts.ts
import { Inter, IBM_Plex_Mono } from 'next/font/google'

export const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const ibmPlexMono = IBM_Plex_Mono({
  weight: ['400', '500', '600', '700'],
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
})

// Usage in components
<body className={`${inter.variable} ${ibmPlexMono.variable} font-sans`}>
```

---

## 2. Navigation Architecture

### 2.1 Top Navigation Bar (89px - Fib11)

**Professional fixed navigation** with divine proportions:

```tsx
// components/navigation/top-nav.tsx
import { cn } from '@/lib/utils'
import { Logo } from './logo'
import { UserMenu } from './user-menu'
import { SearchCommand } from './search-command'

export function TopNav() {
  return (
    <nav className={cn(
      'fixed top-0 left-0 right-0 z-50',
      'h-[89px]',  // Fib(11)
      'bg-surface/89 backdrop-blur-[13px]',  // Fib(11)% opacity, Fib(7) blur
      'border-b border-border/5'
    )}>
      <div className="container h-full flex items-center justify-between px-fib-7">
        {/* Logo + Title */}
        <div className="flex items-center gap-fib-7">
          <Logo className="h-8 w-8" />
          <div className="flex flex-col">
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-br from-foreground to-primary-300 bg-clip-text text-transparent">
              DawsOS
            </h1>
            <p className="text-xs text-muted-foreground tracking-wider">
              Portfolio Intelligence
            </p>
          </div>
        </div>

        {/* Navigation Items */}
        <div className="flex items-center gap-fib-7">
          <NavItem href="/portfolio" label="Portfolio" />
          <NavItem href="/macro" label="Macro" />
          <NavItem href="/holdings" label="Holdings" />
          <NavItem href="/scenarios" label="Scenarios" />
          <NavItem href="/alerts" label="Alerts" />
          <NavItem href="/reports" label="Reports" />
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-fib-5">
          <SearchCommand />
          <PackStatus />
          <UserMenu />
        </div>
      </div>
    </nav>
  )
}

function NavItem({ href, label }: { href: string; label: string }) {
  const pathname = usePathname()
  const isActive = pathname.startsWith(href)

  return (
    <Link
      href={href}
      className={cn(
        'px-fib-5 py-fib-4 rounded-fib-md',
        'text-sm font-medium transition-all duration-fib-normal',
        isActive
          ? 'bg-primary/13 text-foreground'  // φ opacity
          : 'text-muted-foreground hover:text-foreground hover:bg-elevated'
      )}
    >
      {label}
    </Link>
  )
}
```

### 2.2 Context Bar (55px - Fib10)

**Portfolio context and metadata display**:

```tsx
// components/navigation/context-bar.tsx
export function ContextBar() {
  const { portfolio } = usePortfolio()
  const { pack } = usePricingPack()

  return (
    <div className={cn(
      'h-[55px]',  // Fib(10)
      'bg-background/89 backdrop-blur-[13px]',
      'border-b border-border/3',
      'fixed top-[89px] left-0 right-0 z-40'  // Below top nav
    )}>
      <div className="container h-full flex items-center justify-between px-fib-7">
        {/* Portfolio Selector */}
        <PortfolioSelector value={portfolio?.id} />

        {/* Context Metadata */}
        <div className="flex items-center gap-fib-6">
          <ContextItem
            label="NAV"
            value={formatCurrency(portfolio?.nav, portfolio?.base_ccy)}
            mono
          />
          <ContextItem
            label="YTD"
            value={formatPercent(portfolio?.ytd_return)}
            valueClass={portfolio?.ytd_return >= 0 ? 'text-success' : 'text-destructive'}
            mono
          />
          <ContextItem
            label="Pack"
            value={pack?.id.slice(0, 8)}
            chip
            chipVariant={pack?.is_fresh ? 'success' : 'warning'}
          />
          <ContextItem
            label="As Of"
            value={formatDate(pack?.date)}
          />
        </div>
      </div>
    </div>
  )
}
```

### 2.3 Combined Stack = 144px (Fib12)

**Perfect Fibonacci sum**: 89px + 55px = 144px

Content area starts at `top-[144px]` with `pt-[144px]` to account for fixed navigation.

---

## 3. Page-by-Page Specifications

### 3.1 Portfolio Overview

**Route**: `/portfolio`
**Pattern**: `portfolio_overview`
**Agent**: `financial_analyst`

```tsx
// app/portfolio/page.tsx
import { PortfolioKPIs } from '@/components/portfolio/kpis'
import { HoldingsTable } from '@/components/portfolio/holdings-table'
import { AllocationCharts } from '@/components/portfolio/allocation-charts'
import { PerformanceChart } from '@/components/portfolio/performance-chart'
import { CurrencyAttribution } from '@/components/portfolio/currency-attribution'

export default function PortfolioPage() {
  const { data, isLoading } = usePortfolioOverview()

  return (
    <div className="container py-fib-7 space-y-fib-7">
      {/* KPI Ribbon */}
      <PortfolioKPIs
        nav={data?.nav}
        twr={data?.twr_ytd}
        mwr={data?.mwr_ytd}
        sharpe={data?.sharpe}
        maxDrawdown={data?.max_drawdown}
        provenance={data?.pricing_pack_id}
      />

      {/* Performance Chart */}
      <PerformanceChart
        data={data?.performance_history}
        benchmark={data?.benchmark_history}
      />

      {/* Two-Column Layout */}
      <div className="grid grid-cols-2 gap-fib-7">
        {/* Left: Allocation */}
        <AllocationCharts
          sectorAllocation={data?.sector_allocation}
          securityAllocation={data?.security_allocation}
        />

        {/* Right: Currency Attribution */}
        <CurrencyAttribution
          localReturn={data?.local_return}
          fxReturn={data?.fx_return}
          interactionReturn={data?.interaction}
        />
      </div>

      {/* Holdings Table */}
      <HoldingsTable
        holdings={data?.holdings}
        onRowClick={(holding) => router.push(`/holdings/${holding.symbol}`)}
      />
    </div>
  )
}
```

**Components Needed**:
1. `PortfolioKPIs` - shadcn/ui Card with Metric components
2. `PerformanceChart` - Recharts line chart with dual axis
3. `AllocationCharts` - Recharts pie + bar charts
4. `CurrencyAttribution` - Waterfall chart
5. `HoldingsTable` - shadcn/ui Table with sorting, filtering

### 3.2 Macro Dashboard

**Route**: `/macro`
**Pattern**: `macro_cycles_overview`
**Agent**: `macro_hound`

```tsx
// app/macro/page.tsx
export default function MacroPage() {
  const { data } = useMacroOverview()

  return (
    <div className="container py-fib-7 space-y-fib-7">
      {/* Regime Card - Hero */}
      <RegimeCard
        regime={data?.regime}
        confidence={data?.regime_confidence}
        drivers={data?.regime_drivers}
        phase={data?.cycle_phase}
      />

      {/* Three-Column Grid */}
      <div className="grid grid-cols-3 gap-fib-6">
        {/* Short-Term Debt Cycle */}
        <CycleCard
          title="Short-Term Debt Cycle"
          phase={data?.stdc_phase}
          indicators={data?.stdc_indicators}
          chart={data?.stdc_chart_data}
        />

        {/* Long-Term Debt Cycle */}
        <CycleCard
          title="Long-Term Debt Cycle"
          phase={data?.ltdc_phase}
          indicators={data?.ltdc_indicators}
          chart={data?.ltdc_chart_data}
        />

        {/* Empire Cycle */}
        <CycleCard
          title="Empire Cycle"
          phase={data?.empire_phase}
          indicators={data?.empire_indicators}
          chart={data?.empire_chart_data}
        />
      </div>

      {/* Factor Exposure */}
      <FactorExposure
        betas={data?.factor_betas}
        varShare={data?.var_share}
      />

      {/* Drawdown-at-Risk (DaR) */}
      <DaRGauge
        dar={data?.dar}
        confidence={0.95}
        drivers={data?.dar_drivers}
      />
    </div>
  )
}
```

**Components Needed**:
1. `RegimeCard` - Large hero card with gradient, phase timeline
2. `CycleCard` - Card with mini chart, indicators, current phase
3. `FactorExposure` - Horizontal bar chart
4. `DaRGauge` - Radial gauge with waterfall breakdown

### 3.3 Holdings Detail

**Route**: `/holdings/[symbol]`
**Pattern**: `holding_deep_dive`
**Agent**: `financial_analyst` + `ratings`

```tsx
// app/holdings/[symbol]/page.tsx
export default function HoldingPage({ params }: { params: { symbol: string } }) {
  const { data } = useHoldingDeepDive(params.symbol)

  return (
    <div className="container py-fib-7 space-y-fib-7">
      {/* Header with Symbol, Name, Price */}
      <HoldingHeader
        symbol={data?.symbol}
        name={data?.name}
        price={data?.current_price}
        change={data?.price_change}
        currency={data?.trading_currency}
      />

      {/* Buffett Ratings */}
      <BuffettRatings
        moat={data?.moat_score}
        moatComponents={data?.moat_components}
        dividendSafety={data?.dividend_safety}
        dividendComponents={data?.dividend_components}
        resilience={data?.resilience_score}
        resilienceComponents={data?.resilience_components}
      />

      {/* Position Details */}
      <PositionDetails
        lots={data?.lots}
        totalShares={data?.total_shares}
        costBasis={data?.cost_basis}
        currentValue={data?.current_value}
        unrealizedPL={data?.unrealized_pl}
      />

      {/* Price Chart */}
      <PriceChart
        data={data?.price_history}
        transactions={data?.transactions}
      />

      {/* Fundamentals */}
      <FundamentalsPanel
        revenue={data?.revenue}
        netIncome={data?.net_income}
        fcf={data?.fcf}
        roe={data?.roe}
        debtToEquity={data?.debt_to_equity}
      />
    </div>
  )
}
```

**Components Needed**:
1. `HoldingHeader` - Large banner with live price
2. `BuffettRatings` - Three rating cards (0-10 scale) with component breakdowns
3. `PositionDetails` - Table of lots with cost basis, P&L
4. `PriceChart` - Candlestick chart with transaction markers
5. `FundamentalsPanel` - Grid of metric cards

### 3.4 Scenarios

**Route**: `/scenarios`
**Pattern**: `portfolio_scenario_analysis`
**Agent**: `macro_hound`

```tsx
// app/scenarios/page.tsx
export default function ScenariosPage() {
  const [selectedScenario, setSelectedScenario] = useState<string>()
  const { data: scenarios } = useScenarios()
  const { data: analysis, mutate } = useScenarioAnalysis(selectedScenario)

  return (
    <div className="container py-fib-7 space-y-fib-7">
      {/* Scenario Selector */}
      <ScenarioSelector
        scenarios={scenarios}
        value={selectedScenario}
        onChange={(id) => {
          setSelectedScenario(id)
          mutate({ scenario_id: id })
        }}
      />

      {/* Impact Summary */}
      {analysis && (
        <>
          <ImpactSummary
            totalImpact={analysis.total_impact}
            impactByHolding={analysis.impact_by_holding}
          />

          {/* Hedge Suggestions */}
          <HedgeSuggestions
            hedges={analysis.hedge_suggestions}
            onPreview={(hedge) => {
              mutate({
                scenario_id: selectedScenario,
                with_hedge: hedge
              })
            }}
          />

          {/* Detailed Breakdown */}
          <ScenarioBreakdownTable
            data={analysis.holding_impacts}
          />
        </>
      )}
    </div>
  )
}
```

**Components Needed**:
1. `ScenarioSelector` - shadcn/ui Select with categories
2. `ImpactSummary` - Large KPI card + waterfall chart
3. `HedgeSuggestions` - Card list with preview buttons
4. `ScenarioBreakdownTable` - Table with ΔP/L by holding

### 3.5 Alerts

**Route**: `/alerts`
**Pattern**: `alert_system_overview` (new)
**Agent**: `alerts`

```tsx
// app/alerts/page.tsx
export default function AlertsPage() {
  const { data: alerts } = useAlerts()
  const { data: presets } = useAlertPresets()

  return (
    <div className="container py-fib-7 space-y-fib-7">
      {/* Create Alert Button */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Alerts</h1>
        <Dialog>
          <DialogTrigger asChild>
            <Button size="lg">
              <PlusIcon className="mr-2 h-4 w-4" />
              Create Alert
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <AlertCreateForm presets={presets} />
          </DialogContent>
        </Dialog>
      </div>

      {/* Active Alerts */}
      <AlertsTable
        alerts={alerts?.active}
        onEdit={(alert) => {/* ... */}}
        onDelete={(alert) => {/* ... */}}
        onToggle={(alert) => {/* ... */}}
      />

      {/* Recent Notifications */}
      <NotificationsTimeline
        notifications={alerts?.recent_notifications}
      />
    </div>
  )
}
```

**Components Needed**:
1. `AlertCreateForm` - shadcn/ui Form with condition builder
2. `AlertsTable` - Table with toggle switches
3. `NotificationsTimeline` - Timeline component with playbook buttons

### 3.6 Reports

**Route**: `/reports`
**Pattern**: `export_portfolio_report`
**Agent**: `reports`

```tsx
// app/reports/page.tsx
export default function ReportsPage() {
  const [generating, setGenerating] = useState(false)
  const { data: history } = useReportHistory()

  return (
    <div className="container py-fib-7 space-y-fib-7">
      {/* Report Generator */}
      <Card className="p-fib-7">
        <h2 className="text-2xl font-bold mb-fib-6">Generate Report</h2>
        <ReportConfigForm
          onGenerate={async (config) => {
            setGenerating(true)
            await generateReport(config)
            setGenerating(false)
          }}
          generating={generating}
        />
      </Card>

      {/* Report History */}
      <Card className="p-fib-7">
        <h2 className="text-2xl font-bold mb-fib-6">Report History</h2>
        <ReportHistoryTable
          reports={history}
          onDownload={(report) => downloadReport(report.id)}
          onDelete={(report) => deleteReport(report.id)}
        />
      </Card>
    </div>
  )
}
```

**Components Needed**:
1. `ReportConfigForm` - Form with date range, sections selector
2. `ReportHistoryTable` - Table with download/delete actions
3. Rights enforcement warning (if data can't be exported)

---

## 4. Component Library

### 4.1 Core shadcn/ui Components

**Install all needed components**:

```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add table
npx shadcn-ui@latest add select
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add form
npx shadcn-ui@latest add input
npx shadcn-ui@latest add label
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add tooltip
npx shadcn-ui@latest add popover
npx shadcn-ui@latest add command
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add switch
npx shadcn-ui@latest add progress
npx shadcn-ui@latest add skeleton
```

### 4.2 Custom DawsOS Components

#### Metric Card (Divine Proportions)

```tsx
// components/ui/metric-card.tsx
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface MetricCardProps {
  label: string
  value: string | number
  delta?: {
    value: number
    label?: string
  }
  provenance?: {
    pack_id: string
    ledger_hash: string
  }
  isFresh?: boolean
  className?: string
}

export function MetricCard({
  label,
  value,
  delta,
  provenance,
  isFresh = true,
  className
}: MetricCardProps) {
  return (
    <Card className={cn(
      'p-fib-6',  // Fib(8) padding
      'border-border hover:border-primary/21 transition-colors duration-fib-normal',
      'hover:shadow-divine-md',
      className
    )}>
      {/* Label */}
      <p className="text-xs uppercase tracking-wider text-muted-foreground mb-fib-4">
        {label}
      </p>

      {/* Value */}
      <div className="flex items-baseline gap-fib-5">
        <span className="text-3xl font-mono font-bold text-foreground">
          {value}
        </span>

        {/* Delta */}
        {delta && (
          <span className={cn(
            'text-sm font-mono font-semibold',
            delta.value >= 0 ? 'text-success' : 'text-destructive'
          )}>
            {delta.value >= 0 ? '+' : ''}{delta.value}%
            {delta.label && ` ${delta.label}`}
          </span>
        )}
      </div>

      {/* Provenance */}
      {provenance && (
        <div className="mt-fib-4 flex items-center gap-fib-4 text-xs text-muted-foreground font-mono">
          <span className={cn(
            'px-fib-4 py-fib-2 rounded-fib-sm border',
            isFresh
              ? 'border-success/21 text-success'
              : 'border-warning/21 text-warning'
          )}>
            {provenance.pack_id.slice(0, 8)}
          </span>
          <span>•</span>
          <span>{provenance.ledger_hash.slice(0, 7)}</span>
        </div>
      )}
    </Card>
  )
}
```

#### Rating Badge (Buffett Scores 0-10)

```tsx
// components/ui/rating-badge.tsx
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

interface RatingBadgeProps {
  score: number  // 0-10
  type: 'moat' | 'dividend' | 'resilience'
  components?: Record<string, number>
  size?: 'sm' | 'md' | 'lg'
}

export function RatingBadge({ score, type, components, size = 'md' }: RatingBadgeProps) {
  const color = score >= 8 ? 'success' : score >= 5 ? 'warning' : 'destructive'
  const label = type === 'moat' ? 'M' : type === 'dividend' ? 'D' : 'R'

  const sizeClasses = {
    sm: 'h-6 w-6 text-xs',
    md: 'h-8 w-8 text-sm',
    lg: 'h-10 w-10 text-base'
  }

  const badge = (
    <div className={cn(
      'rounded-full border-2 flex items-center justify-center font-bold font-mono',
      `border-${color} text-${color}`,
      sizeClasses[size],
      'cursor-help transition-all duration-fib-normal',
      'hover:scale-110 hover:shadow-divine-sm'
    )}>
      {label}
      <span className="text-[0.65em] ml-0.5">{score.toFixed(1)}</span>
    </div>
  )

  if (!components) return badge

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          {badge}
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">
          <div className="space-y-fib-4">
            <p className="font-semibold capitalize">{type} Score: {score.toFixed(1)}/10</p>
            {Object.entries(components).map(([key, value]) => (
              <div key={key} className="flex justify-between gap-fib-5 text-sm">
                <span className="text-muted-foreground capitalize">{key.replace('_', ' ')}</span>
                <span className="font-mono">{value.toFixed(1)}</span>
              </div>
            ))}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
```

#### Pack Status Indicator

```tsx
// components/ui/pack-status.tsx
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, Clock, AlertCircle } from 'lucide-react'

export function PackStatus() {
  const { data: pack } = usePricingPack()

  const status = pack?.is_fresh ? 'fresh' : pack?.prewarm_done ? 'stale' : 'warming'

  const config = {
    fresh: {
      icon: CheckCircle2,
      color: 'success',
      label: 'Pack Fresh',
      description: 'All data is current and ready'
    },
    stale: {
      icon: Clock,
      color: 'warning',
      label: 'Pack Stale',
      description: 'Warming in progress'
    },
    warming: {
      icon: AlertCircle,
      color: 'warning',
      label: 'Warming',
      description: 'Please wait for data to refresh'
    }
  }

  const { icon: Icon, color, label, description } = config[status]

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant={color as any} className="gap-fib-4 cursor-help">
            <Icon className="h-3 w-3" />
            {label}
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <div className="space-y-fib-4">
            <p className="font-semibold">{label}</p>
            <p className="text-sm text-muted-foreground">{description}</p>
            {pack && (
              <div className="text-xs font-mono text-muted-foreground">
                Pack: {pack.id}
              </div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
```

---

## 5. Data Visualization System

### 5.1 Chart Library: Recharts

**Why Recharts**:
- Built for React
- Responsive by default
- Customizable with Tailwind classes
- Supports all DawsOS chart types

**Install**:
```bash
npm install recharts
```

### 5.2 Chart Theme Configuration

```tsx
// lib/chart-config.ts
export const chartConfig = {
  colors: {
    primary: 'hsl(180, 100%, 32%)',
    electric: 'hsl(209, 100%, 48%)',
    provenance: 'hsl(245, 67%, 48%)',
    accent: 'hsl(72, 88%, 42%)',
    success: 'hsl(142, 76%, 36%)',
    warning: 'hsl(38, 92%, 50%)',
    destructive: 'hsl(0, 72%, 51%)',
  },

  defaults: {
    margin: { top: 13, right: 34, bottom: 21, left: 21 },  // Fibonacci
    fontSize: 13,  // Fib(7)
    fontFamily: 'var(--font-mono)',
    strokeWidth: 2,  // Fib(3)
    gridStroke: 'hsl(220, 10%, 25%)',
    gridOpacity: 0.13,  // φ-based
    tooltipBg: 'hsl(217, 12%, 14%)',
    tooltipBorder: 'hsl(220, 10%, 25%)',
  },

  // Axis styling
  axis: {
    stroke: 'hsl(220, 10%, 48%)',
    tickLine: false,
    axisLine: true,
  },

  // Tooltip styling
  tooltip: {
    cursor: { stroke: 'hsl(180, 100%, 32%)', strokeWidth: 1 },
    contentStyle: {
      backgroundColor: 'hsl(217, 12%, 14%)',
      border: '1px solid hsl(220, 10%, 25%)',
      borderRadius: '5px',  // Fib(5)
      padding: '8px 13px',  // Fib(6) × Fib(7)
    },
    labelStyle: {
      color: 'hsl(220, 10%, 96%)',
      fontFamily: 'var(--font-mono)',
      fontSize: '13px',
      fontWeight: 600,
    },
    itemStyle: {
      color: 'hsl(220, 10%, 72%)',
      fontFamily: 'var(--font-mono)',
      fontSize: '13px',
    },
  },
}
```

### 5.3 Example Charts

#### Performance Line Chart

```tsx
// components/charts/performance-chart.tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { chartConfig } from '@/lib/chart-config'

interface PerformanceChartProps {
  data: Array<{
    date: string
    portfolio: number
    benchmark: number
  }>
}

export function PerformanceChart({ data }: PerformanceChartProps) {
  return (
    <Card className="p-fib-7">
      <h3 className="text-xl font-bold mb-fib-6">Performance</h3>
      <ResponsiveContainer width="100%" height={377}>  {/* Fib(14) */}
        <LineChart data={data} margin={chartConfig.defaults.margin}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke={chartConfig.defaults.gridStroke}
            opacity={chartConfig.defaults.gridOpacity}
          />
          <XAxis
            dataKey="date"
            stroke={chartConfig.axis.stroke}
            style={{ fontSize: chartConfig.defaults.fontSize, fontFamily: chartConfig.defaults.fontFamily }}
            tickLine={chartConfig.axis.tickLine}
            axisLine={chartConfig.axis.axisLine}
          />
          <YAxis
            stroke={chartConfig.axis.stroke}
            style={{ fontSize: chartConfig.defaults.fontSize, fontFamily: chartConfig.defaults.fontFamily }}
            tickLine={chartConfig.axis.tickLine}
            axisLine={chartConfig.axis.axisLine}
            tickFormatter={(value) => `${(value * 100).toFixed(1)}%`}
          />
          <Tooltip {...chartConfig.tooltip} />
          <Legend wrapperStyle={{ paddingTop: '21px' }} />  {/* Fib(8) */}
          <Line
            type="monotone"
            dataKey="portfolio"
            stroke={chartConfig.colors.primary}
            strokeWidth={chartConfig.defaults.strokeWidth}
            dot={false}
            name="Portfolio"
          />
          <Line
            type="monotone"
            dataKey="benchmark"
            stroke={chartConfig.colors.electric}
            strokeWidth={chartConfig.defaults.strokeWidth}
            dot={false}
            strokeDasharray="5 5"
            name="Benchmark"
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  )
}
```

#### Allocation Pie Chart

```tsx
// components/charts/allocation-pie.tsx
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import { chartConfig } from '@/lib/chart-config'

export function AllocationPie({ data }: { data: Array<{ name: string; value: number }> }) {
  const colors = Object.values(chartConfig.colors)

  return (
    <Card className="p-fib-7">
      <h3 className="text-xl font-bold mb-fib-6">Sector Allocation</h3>
      <ResponsiveContainer width="100%" height={377}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
            outerRadius={80}
            fill={chartConfig.colors.primary}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip {...chartConfig.tooltip} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </Card>
  )
}
```

#### Waterfall Chart (Currency Attribution)

```tsx
// components/charts/waterfall-chart.tsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { chartConfig } from '@/lib/chart-config'

export function WaterfallChart({ localReturn, fxReturn, interaction }: {
  localReturn: number
  fxReturn: number
  interaction: number
}) {
  const data = [
    { name: 'Local Return', value: localReturn, fill: chartConfig.colors.primary },
    { name: 'FX Return', value: fxReturn, fill: fxReturn >= 0 ? chartConfig.colors.success : chartConfig.colors.destructive },
    { name: 'Interaction', value: interaction, fill: chartConfig.colors.accent },
    { name: 'Total', value: localReturn + fxReturn + interaction, fill: chartConfig.colors.electric },
  ]

  return (
    <Card className="p-fib-7">
      <h3 className="text-xl font-bold mb-fib-6">Currency Attribution</h3>
      <ResponsiveContainer width="100%" height={377}>
        <BarChart data={data} margin={chartConfig.defaults.margin}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke={chartConfig.defaults.gridStroke}
            opacity={chartConfig.defaults.gridOpacity}
          />
          <XAxis
            dataKey="name"
            stroke={chartConfig.axis.stroke}
            style={{ fontSize: chartConfig.defaults.fontSize }}
          />
          <YAxis
            stroke={chartConfig.axis.stroke}
            style={{ fontSize: chartConfig.defaults.fontSize }}
            tickFormatter={(value) => `${(value * 100).toFixed(1)}%`}
          />
          <Tooltip {...chartConfig.tooltip} />
          <ReferenceLine y={0} stroke={chartConfig.axis.stroke} />
          <Bar dataKey="value" fill={(data) => data.fill} />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )
}
```

---

## 6. shadcn/ui Integration Guide

### 6.1 Installation & Setup

```bash
# Initialize Next.js project
npx create-next-app@latest dawsos-ui --typescript --tailwind --app

cd dawsos-ui

# Install shadcn/ui
npx shadcn-ui@latest init

# Configure when prompted:
# - Style: Default
# - Base color: Zinc (we'll override)
# - CSS variables: Yes
```

### 6.2 Customizing shadcn/ui with Divine Proportions

Update `components.json`:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "app/globals.css",
    "baseColor": "zinc",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

Update `app/globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Divine Proportions Dark Theme */
    --background: 220 13% 9%;
    --foreground: 220 10% 96%;

    --card: 217 12% 14%;
    --card-foreground: 220 10% 96%;

    --popover: 217 12% 14%;
    --popover-foreground: 220 10% 96%;

    --primary: 180 100% 32%;
    --primary-foreground: 220 13% 9%;

    --secondary: 217 12% 18%;
    --secondary-foreground: 220 10% 96%;

    --muted: 220 10% 48%;
    --muted-foreground: 220 10% 72%;

    --accent: 209 100% 48%;
    --accent-foreground: 220 10% 96%;

    --destructive: 0 72% 51%;
    --destructive-foreground: 0 0% 100%;

    --border: 220 10% 25%;
    --input: 220 10% 25%;
    --ring: 180 100% 32%;

    --radius: 0.5rem;  /* Override with Fib values in components */
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
}
```

### 6.3 Adding Components

```bash
# Install all needed shadcn/ui components at once
npx shadcn-ui@latest add button card table select dialog form input label tabs badge tooltip popover command dropdown-menu switch progress skeleton alert-dialog checkbox radio-group textarea hover-card separator sheet toast
```

### 6.4 Component Customization Examples

**Button with Fibonacci padding**:

```tsx
// Extend shadcn/ui Button
import { Button as ShadButton } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function Button({ className, ...props }: ButtonProps) {
  return (
    <ShadButton
      className={cn(
        'px-fib-5 py-fib-4',  // Override default padding
        'rounded-fib-md',      // Fibonacci border radius
        'transition-all duration-fib-normal',
        'hover:shadow-divine-sm',
        className
      )}
      {...props}
    />
  )
}
```

**Card with divine shadow**:

```tsx
import { Card as ShadCard } from '@/components/ui/card'
import { cn } from '@/lib/utils'

export function Card({ className, ...props }: CardProps) {
  return (
    <ShadCard
      className={cn(
        'shadow-divine-md',
        'hover:shadow-divine-lg transition-shadow duration-fib-normal',
        'border-border/21',  // φ opacity
        className
      )}
      {...props}
    />
  )
}
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

**Goal**: Get basic navigation and layout working with divine proportions

```
Week 1:
- ✅ Day 1-2: Next.js setup, shadcn/ui installation, Tailwind config
- ✅ Day 3-4: TopNav + ContextBar with Fibonacci measurements
- ✅ Day 5: Layout component, routing structure

Week 2:
- ✅ Day 1-2: Typography system, color variables, spacing utilities
- ✅ Day 3-4: Card, Button, MetricCard components
- ✅ Day 5: Chart configuration, first Recharts integration
```

**Deliverables**:
- [ ] Navigation renders with divine proportions (89px + 55px = 144px)
- [ ] All colors use golden angle distribution
- [ ] All spacing uses Fibonacci values
- [ ] Basic portfolio page renders with fake data

### Phase 2: Core Pages (Week 3-4)

**Goal**: Implement all main pages with real API integration

```
Week 3:
- ✅ Day 1-2: Portfolio Overview page + components
- ✅ Day 3: Macro Dashboard page + regime cards
- ✅ Day 4: Holdings table + detail page
- ✅ Day 5: API client setup, data fetching hooks

Week 4:
- ✅ Day 1-2: Scenarios page + scenario selector
- ✅ Day 3: Alerts page + alert creation form
- ✅ Day 4: Reports page + report generator
- ✅ Day 5: Integration testing, bug fixes
```

**Deliverables**:
- [ ] All 6 main pages functional
- [ ] Real data from FastAPI backend
- [ ] All charts rendering correctly
- [ ] Navigation between pages works

### Phase 3: Polish & Advanced Features (Week 5-6)

**Goal**: Add animations, loading states, error handling, advanced interactions

```
Week 5:
- ✅ Day 1: Loading skeletons with Fibonacci timing
- ✅ Day 2: Error states, retry logic
- ✅ Day 3: Optimistic UI updates
- ✅ Day 4: Micro-interactions (hover effects, transitions)
- ✅ Day 5: Toast notifications, command palette

Week 6:
- ✅ Day 1-2: Explain drawer with execution traces
- ✅ Day 3: Pack status real-time updates
- ✅ Day 4: Search functionality
- ✅ Day 5: Performance optimization (code splitting, lazy loading)
```

**Deliverables**:
- [ ] All animations use Fibonacci timing
- [ ] Loading states everywhere
- [ ] Error handling everywhere
- [ ] Smooth transitions between states
- [ ] Command palette (Cmd+K) works

### Phase 4: Production Ready (Week 7-8)

**Goal**: Testing, accessibility, performance, deployment

```
Week 7:
- ✅ Day 1-2: Accessibility audit (WCAG AA)
- ✅ Day 3: Visual regression tests
- ✅ Day 4: E2E tests (Playwright)
- ✅ Day 5: Performance testing (Lighthouse)

Week 8:
- ✅ Day 1-2: Bug fixes from testing
- ✅ Day 3: Documentation (Storybook)
- ✅ Day 4: Deployment setup (Vercel/Docker)
- ✅ Day 5: Launch! 🚀
```

**Deliverables**:
- [ ] Lighthouse score 90+ (all categories)
- [ ] WCAG AA compliant
- [ ] E2E tests passing
- [ ] Deployed to production

---

## 8. Technical Stack

### 8.1 Core Dependencies

```json
{
  "dependencies": {
    "next": "14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "typescript": "^5.4.0",

    // Styling
    "tailwindcss": "^3.4.0",
    "tailwindcss-animate": "^1.0.7",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0",

    // UI Components (shadcn/ui dependencies)
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-tooltip": "^1.0.7",
    "@radix-ui/react-popover": "^1.0.7",
    "@radix-ui/react-switch": "^1.0.3",
    "@radix-ui/react-progress": "^1.0.3",
    "@radix-ui/react-toast": "^1.1.5",

    // Charts
    "recharts": "^2.12.0",

    // Data Fetching
    "@tanstack/react-query": "^5.28.0",
    "axios": "^1.6.7",

    // Forms
    "react-hook-form": "^7.51.0",
    "@hookform/resolvers": "^3.3.4",
    "zod": "^3.22.4",

    // Icons
    "lucide-react": "^0.358.0",

    // Date/Time
    "date-fns": "^3.4.0",

    // Utilities
    "cmdk": "^1.0.0"  // Command palette
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "autoprefixer": "^10.4.18",
    "postcss": "^8.4.35",
    "eslint": "^8.57.0",
    "eslint-config-next": "14.2.0",

    // Testing
    "@playwright/test": "^1.42.0",
    "@testing-library/react": "^14.2.0",
    "vitest": "^1.3.0",

    // Storybook (optional)
    "@storybook/react": "^8.0.0",
    "@storybook/addon-essentials": "^8.0.0"
  }
}
```

### 8.2 Project Structure

```
dawsos-ui/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/
│   │   ├── layout.tsx          # TopNav + ContextBar
│   │   ├── portfolio/
│   │   │   └── page.tsx
│   │   ├── macro/
│   │   │   └── page.tsx
│   │   ├── holdings/
│   │   │   ├── page.tsx
│   │   │   └── [symbol]/
│   │   │       └── page.tsx
│   │   ├── scenarios/
│   │   │   └── page.tsx
│   │   ├── alerts/
│   │   │   └── page.tsx
│   │   └── reports/
│   │       └── page.tsx
│   ├── layout.tsx              # Root layout
│   ├── globals.css
│   └── api/                    # API routes (if needed)
├── components/
│   ├── ui/                     # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── ...
│   ├── navigation/
│   │   ├── top-nav.tsx
│   │   ├── context-bar.tsx
│   │   ├── logo.tsx
│   │   └── user-menu.tsx
│   ├── portfolio/
│   │   ├── kpis.tsx
│   │   ├── holdings-table.tsx
│   │   └── ...
│   ├── macro/
│   │   ├── regime-card.tsx
│   │   ├── cycle-card.tsx
│   │   └── ...
│   ├── charts/
│   │   ├── performance-chart.tsx
│   │   ├── allocation-pie.tsx
│   │   ├── waterfall-chart.tsx
│   │   └── ...
│   └── common/
│       ├── metric-card.tsx
│       ├── rating-badge.tsx
│       ├── pack-status.tsx
│       └── ...
├── lib/
│   ├── utils.ts                # cn() helper
│   ├── api.ts                  # API client
│   ├── chart-config.ts         # Recharts theme
│   ├── fonts.ts                # Next.js fonts
│   └── hooks/
│       ├── use-portfolio.ts
│       ├── use-macro.ts
│       └── ...
├── public/
│   └── ...
├── tailwind.config.ts
├── next.config.js
├── tsconfig.json
└── package.json
```

### 8.3 API Integration

```typescript
// lib/api.ts
import axios from 'axios'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Pattern execution helper
export async function executePattern<T>(
  pattern_id: string,
  inputs: Record<string, any>
): Promise<T> {
  const response = await api.post('/v1/execute', {
    pattern_id,
    inputs,
  })
  return response.data
}

// Hook: Portfolio Overview
export function usePortfolioOverview(portfolio_id?: string) {
  return useQuery({
    queryKey: ['portfolio', 'overview', portfolio_id],
    queryFn: () => executePattern('portfolio_overview', {
      portfolio_id: portfolio_id || 'default'
    }),
    staleTime: 5 * 60 * 1000,  // 5 minutes
    refetchOnWindowFocus: false,
  })
}

// Hook: Macro Overview
export function useMacroOverview() {
  return useQuery({
    queryKey: ['macro', 'overview'],
    queryFn: () => executePattern('macro_cycles_overview', {}),
    staleTime: 15 * 60 * 1000,  // 15 minutes
  })
}

// Hook: Scenario Analysis (mutation)
export function useScenarioAnalysis() {
  return useMutation({
    mutationFn: (params: { scenario_id: string; with_hedge?: any }) =>
      executePattern('portfolio_scenario_analysis', params),
  })
}
```

---

## 9. Key Takeaways

### 9.1 What Makes This Plan Special

1. **Divine Proportions Throughout**
   - Every spacing value is Fibonacci
   - Every color distributed via golden angle
   - Every animation timed with Fibonacci ms
   - Every shadow uses φ-based opacity

2. **shadcn/ui Integration**
   - Professional, accessible components out-of-the-box
   - Customizable with Tailwind (divine proportions applied)
   - Built on Radix UI (robust, tested primitives)
   - TypeScript-first

3. **Product Roadmap Alignment**
   - Every page maps to a backend pattern
   - Every component reflects a backend capability
   - All 12 production patterns supported
   - Real-time data integration ready

4. **Bloomberg-Level Polish**
   - Data-dense layouts without clutter
   - Professional dark theme
   - Instant feedback everywhere
   - Expensive feel through subtle details

### 9.2 Implementation Priority

**Must Have (Week 1-4)**:
- ✅ Navigation with divine proportions
- ✅ Portfolio Overview page
- ✅ Macro Dashboard page
- ✅ Holdings table + detail
- ✅ Basic charts (line, pie, bar)

**Should Have (Week 5-6)**:
- ✅ Scenarios page
- ✅ Alerts page
- ✅ Reports page
- ✅ Loading states
- ✅ Error handling

**Nice to Have (Week 7-8)**:
- ✅ Command palette
- ✅ Explain drawer
- ✅ Real-time pack status
- ✅ Advanced animations
- ✅ Storybook docs

### 9.3 Success Metrics

**Design Quality**:
- [ ] All spacing is Fibonacci (no arbitrary values)
- [ ] All colors from golden angle distribution
- [ ] All animations timed naturally (Fibonacci ms)
- [ ] Lighthouse accessibility score 90+

**Technical Quality**:
- [ ] TypeScript strict mode (no `any`)
- [ ] All components have prop types
- [ ] All API calls have error handling
- [ ] All pages have loading states

**User Experience**:
- [ ] Sub-second page transitions
- [ ] Instant feedback on interactions
- [ ] Clear error messages
- [ ] Helpful empty states

---

## 🎉 **Conclusion**

This comprehensive UI plan provides:

1. ✅ **Complete design system** with divine proportions
2. ✅ **shadcn/ui integration** with customizations
3. ✅ **Page-by-page specifications** for all routes
4. ✅ **Component library** with code examples
5. ✅ **Chart system** with Recharts
6. ✅ **Implementation roadmap** (8 weeks)
7. ✅ **Technical stack** with all dependencies

**The result**: A UI that looks like it was designed by a **professional firm**, with **Bloomberg-level data density**, **Apple-level polish**, and **mathematical precision** through divine proportions.

**Next Steps**:
1. Review this plan with team
2. Set up Next.js project with shadcn/ui
3. Start with Phase 1 (Foundation)
4. Build incrementally following roadmap

**This is production-ready. This is beautiful. This is DawsOS.**

---

**Created**: October 28, 2025
**Status**: ✅ Complete Specification
**Ready**: For immediate implementation
**Philosophy**: Divine Geometry × Professional Restraint × Subtle Luxury
