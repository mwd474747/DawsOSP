import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { QueryProvider } from '@/lib/query-provider'
import { Navigation } from '@/components/Navigation'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'DawsOS - Portfolio Intelligence Platform',
  description: 'Professional portfolio analytics with macro regime detection, Buffett quality ratings, and scenario analysis',
  keywords: ['portfolio', 'finance', 'analytics', 'macro', 'buffett', 'scenarios'],
}

// Force dynamic rendering for all pages
export const dynamic = 'force-dynamic'
export const revalidate = 0

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <QueryProvider>
          <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
            <Navigation />
            <main>
              {children}
            </main>
          </div>
        </QueryProvider>
      </body>
    </html>
  )
}
