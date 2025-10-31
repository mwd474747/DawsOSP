import type { Metadata } from 'next'
import './globals.css'
import { QueryProvider } from '@/lib/query-provider'
import { Sidebar } from '@/components/Sidebar'

export const metadata: Metadata = {
  title: 'DawsOS - Portfolio Intelligence Platform',
  description: 'Professional Bloomberg Terminal-style portfolio analytics platform',
  keywords: ['portfolio', 'finance', 'analytics', 'macro', 'bloomberg', 'terminal'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-mono">
        <QueryProvider>
          <div className="min-h-screen bg-[#0f172a] text-slate-100">
            <Sidebar />
            <main className="ml-64">
              <div className="p-6">
                {children}
              </div>
            </main>
          </div>
        </QueryProvider>
      </body>
    </html>
  )
}
