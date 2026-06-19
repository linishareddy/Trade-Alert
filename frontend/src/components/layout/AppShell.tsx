'use client'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Sidebar } from './Sidebar'
import { TopNav } from './TopNav'
import { useConfig } from '@/hooks/useHealth'
import { useAuth } from '@/providers/AuthProvider'
import { PageMotion } from '@/components/motion/PageMotion'

interface AppShellProps {
  children: React.ReactNode
  title: string
  subtitle?: string
}

export function AppShell({ children, title, subtitle }: AppShellProps) {
  const router = useRouter()
  const { user, isLoading } = useAuth()
  const { data: config } = useConfig()
  const executionOff = config?.execution_enabled === false

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace('/login')
    }
  }, [isLoading, user, router])

  if (isLoading || !user) {
    return (
      <div className="flex h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-50 dark:bg-zinc-950">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <TopNav title={title} subtitle={subtitle} />

        {/* Execution-off banner — visible on every page when execution is disabled */}
        {executionOff && (
          <div className="shrink-0 border-b border-amber-200 bg-amber-50 px-6 py-2.5 dark:border-amber-800/40 dark:bg-amber-950/20">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-600 dark:text-amber-400" />
              <p className="text-xs font-medium text-amber-700 dark:text-amber-400">
                Execution is disabled — signals will be parsed but no trades will be placed.
              </p>
              <Link
                href="/system"
                className="ml-auto shrink-0 text-xs font-medium text-amber-700 underline underline-offset-2 hover:no-underline dark:text-amber-400"
              >
                Enable in Health &amp; Config →
              </Link>
            </div>
          </div>
        )}

        <main className="flex-1 overflow-y-auto">
          <div className="w-full px-14 py-6">
            <PageMotion>{children}</PageMotion>
          </div>
        </main>
      </div>
    </div>
  )
}
