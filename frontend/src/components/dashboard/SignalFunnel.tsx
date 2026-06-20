import type { PaperTrade, Signal } from '@/types'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { cn } from '@/lib/utils/cn'

interface SignalFunnelProps {
  trades: PaperTrade[]
  signals: Signal[]
  loading?: boolean
  className?: string
}

export function SignalFunnel({ trades, signals, loading, className }: SignalFunnelProps) {
  const totalSignals = signals.length
  const buySignals = signals.filter((s) => s.action === 'BUY').length
  const executed = trades.filter((t) => t.validation_passed && t.status !== 'CANCELLED').length
  const closed = trades.filter((t) => t.status === 'CLOSED').length

  const steps = [
    { label: 'Signals Received', value: totalSignals, pct: 100, color: 'bg-blue-500 dark:bg-blue-600' },
    { label: 'BUY Signals', value: buySignals, pct: totalSignals > 0 ? Math.round((buySignals / totalSignals) * 100) : 0, color: 'bg-indigo-500 dark:bg-indigo-600' },
    { label: 'EMA/VWAP Pass', value: executed, pct: totalSignals > 0 ? Math.round((executed / totalSignals) * 100) : 0, color: 'bg-violet-500 dark:bg-violet-600' },
    { label: 'Trades Closed', value: closed, pct: totalSignals > 0 ? Math.round((closed / totalSignals) * 100) : 0, color: 'bg-purple-500 dark:bg-purple-600' },
  ]

  return (
    <Card padding="md" className={cn('flex flex-col', className)}>
      <CardHeader className="mb-3 shrink-0">
        <div>
          <CardTitle>Signal Funnel</CardTitle>
          <CardDescription className="mt-0.5">Discord → Validate → Execute</CardDescription>
        </div>
      </CardHeader>

      <div className="flex min-h-0 flex-1 flex-col justify-center">
        {loading ? (
          <div className="space-y-3">
            {[100, 70, 45, 30].map((w, i) => (
              <div key={i} className="h-8 animate-pulse rounded-lg bg-zinc-200 dark:bg-zinc-800" style={{ width: `${w}%` }} />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {steps.map((step) => (
              <div key={step.label}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="text-zinc-600 dark:text-zinc-400">{step.label}</span>
                  <span className="font-semibold tabular-nums text-zinc-900 dark:text-zinc-100">
                    {step.value}
                    <span className="ml-1 font-normal text-zinc-400">({step.pct}%)</span>
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                  <div
                    className={cn('h-full rounded-full transition-all duration-700', step.color)}
                    style={{ width: `${Math.max(step.pct, step.value > 0 ? 4 : 0)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  )
}
