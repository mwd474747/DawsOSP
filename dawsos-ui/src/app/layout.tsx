import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { QueryProvider } from '@/lib/query-provider'
import { SimpleNavigation } from '@/components/simple-navigation'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'DawsOS - Portfolio Intelligence Platform',
  description: 'Professional portfolio analytics with macro regime detection, Buffett quality ratings, and scenario analysis',
  keywords: ['portfolio', 'finance', 'analytics', 'macro', 'buffett', 'scenarios'],
}

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
            <SimpleNavigation />
            <main>
              {children}
            </main>
          </div>
        </QueryProvider>
      </body>
    </html>
  )
}