'use client'
import { ThemeToggle } from '@/components/ui/ThemeToggle'
import { useOpenTrades } from '@/hooks/useTrades'

interface TopNavProps {
  title: string
  subtitle?: string
}

export function TopNav({ title, subtitle }: TopNavProps) {
  const { data: openTrades } = useOpenTrades()
  const openCount = openTrades?.total ?? 0

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-zinc-200 bg-white px-6 dark:border-zinc-800 dark:bg-zinc-950">
      {/* Page title */}
      <div className="min-w-0">
        <h1 className="truncate text-base font-semibold text-zinc-900 dark:text-zinc-100">{title}</h1>
        {subtitle && <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">{subtitle}</p>}
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-2">
        {openCount > 0 && (
          <div className="hidden items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1 dark:border-amber-800/50 dark:bg-amber-950/30 sm:flex">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
            </span>
            <span className="text-xs font-medium text-amber-700 dark:text-amber-400">
              {openCount} open
            </span>
          </div>
        )}

        <ThemeToggle />
      </div>
    </header>
  )
}
