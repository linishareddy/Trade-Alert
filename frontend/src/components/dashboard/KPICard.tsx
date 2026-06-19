'use client'
import { useEffect, useRef, useState } from 'react'
import { TrendingUp, TrendingDown, type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

interface KPICardProps {
  title: string
  value: string
  subtitle?: string
  change?: number
  icon: LucideIcon
  iconColor: string
  iconBg: string
  trend?: 'up' | 'down' | 'neutral'
  loading?: boolean
}

function useCountUp(target: number, duration = 800) {
  const [current, setCurrent] = useState(0)
  const frame = useRef<number>(0)

  useEffect(() => {
    const start = performance.now()
    const animate = (now: number) => {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setCurrent(target * eased)
      if (progress < 1) frame.current = requestAnimationFrame(animate)
    }
    frame.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frame.current)
  }, [target, duration])

  return current
}

export function KPICard({ title, value, subtitle, change, icon: Icon, iconColor, iconBg, trend, loading }: KPICardProps) {
  if (loading) {
    return (
      <div className="animate-pulse rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex items-start justify-between">
          <div className="h-9 w-9 rounded-lg bg-zinc-200 dark:bg-zinc-700" />
          <div className="h-4 w-12 rounded bg-zinc-200 dark:bg-zinc-700" />
        </div>
        <div className="mt-4 space-y-2">
          <div className="h-7 w-24 rounded bg-zinc-200 dark:bg-zinc-700" />
          <div className="h-3 w-32 rounded bg-zinc-200 dark:bg-zinc-700" />
        </div>
      </div>
    )
  }

  const isPositive = trend === 'up' || (change != null && change >= 0)

  return (
    <div className="group rounded-xl border border-zinc-200 bg-white p-4 transition-all duration-200 hover:border-zinc-300 hover:shadow-sm dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700">
      <div className="flex items-start justify-between">
        <div className={cn('flex h-9 w-9 items-center justify-center rounded-lg', iconBg)}>
          <Icon className={cn('h-4 w-4', iconColor)} />
        </div>
        {change != null && (
          <div
            className={cn(
              'flex items-center gap-0.5 text-xs font-medium',
              isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
            )}
          >
            {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {Math.abs(change).toFixed(1)}%
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">{value}</p>
        <p className="mt-0.5 text-xs text-zinc-500 dark:text-zinc-400">{title}</p>
        {subtitle && <p className="mt-1 text-[11px] text-zinc-400 dark:text-zinc-500">{subtitle}</p>}
      </div>
    </div>
  )
}
