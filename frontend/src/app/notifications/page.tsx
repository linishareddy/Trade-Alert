'use client'
import { AppShell } from '@/components/layout/AppShell'
import { NotificationFeed } from '@/components/notifications/NotificationFeed'
import { useAllTrades } from '@/hooks/useTrades'
import { useAllSignals } from '@/hooks/useSignals'
import { deriveNotifications } from '@/lib/utils/notifications'
import { cn } from '@/lib/utils/cn'
import { TrendingUp, XCircle, TrendingDown, Radio, Target } from 'lucide-react'

function PipelineMetric({
  icon: Icon,
  label,
  value,
  iconColor,
  valueColor,
}: {
  icon: React.ElementType
  label: string
  value: number | string
  iconColor?: string
  valueColor?: string
}) {
  return (
    <div className="flex flex-1 flex-col items-center gap-1.5 py-5">
      <Icon className={cn('h-5 w-5', iconColor ?? 'text-zinc-400 dark:text-zinc-500')} />
      <span className={cn('text-xl font-bold tabular-nums', valueColor ?? 'text-zinc-700 dark:text-zinc-200')}>
        {value}
      </span>
      <span className="text-[11px] text-zinc-400 dark:text-zinc-500">{label}</span>
    </div>
  )
}

export default function NotificationsPage() {
  const { data: tradesData, isLoading: tradesLoading } = useAllTrades()
  const { data: signalsData, isLoading: signalsLoading } = useAllSignals()

  const trades = tradesData?.trades ?? []
  const signals = signalsData?.signals ?? []
  const notifications = deriveNotifications(trades, signals)

  const counts = {
    received: notifications.filter((n) => n.type === 'SIGNAL_RECEIVED').length,
    opened: notifications.filter((n) => n.type === 'TRADE_OPENED').length,
    skipped: notifications.filter((n) => n.type === 'SIGNAL_SKIPPED').length,
    tp: notifications.filter((n) => n.type === 'TP_HIT').length,
    sl: notifications.filter((n) => n.type === 'SL_HIT').length,
  }

  const signalsIn = counts.received + counts.skipped
  const conversionRate = counts.received > 0
    ? Math.round((counts.opened / counts.received) * 100)
    : 0

  const loading = tradesLoading || signalsLoading

  return (
    <AppShell title="Notifications" subtitle="Signal pipeline events — received, validated, traded">

      <div className="mb-5 overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex divide-x divide-zinc-100 dark:divide-zinc-800">
          <PipelineMetric
            icon={Radio}
            label="Signals In"
            value={signalsIn}
            iconColor="text-zinc-500 dark:text-zinc-400"
          />
          <PipelineMetric
            icon={TrendingUp}
            label="Trades Opened"
            value={counts.opened}
            iconColor="text-amber-500 dark:text-amber-400"
            valueColor="text-amber-600 dark:text-amber-400"
          />
          <PipelineMetric
            icon={XCircle}
            label="Skipped"
            value={counts.skipped}
            iconColor="text-zinc-400 dark:text-zinc-500"
          />
          <PipelineMetric
            icon={Target}
            label="TP Hit"
            value={counts.tp}
            iconColor="text-green-500 dark:text-green-400"
            valueColor="text-green-600 dark:text-green-400"
          />
          <PipelineMetric
            icon={TrendingDown}
            label="SL Hit"
            value={counts.sl}
            iconColor="text-red-500 dark:text-red-400"
            valueColor="text-red-600 dark:text-red-400"
          />
          <div className="flex flex-1 flex-col items-center justify-center gap-1 py-5">
            <span className={cn(
              'text-2xl font-bold tabular-nums',
              conversionRate >= 60 ? 'text-green-600 dark:text-green-400' :
              conversionRate >= 30 ? 'text-amber-600 dark:text-amber-400' :
                                     'text-zinc-600 dark:text-zinc-300',
            )}>
              {conversionRate}%
            </span>
            <span className="text-[11px] text-zinc-400 dark:text-zinc-500">Conversion</span>
          </div>
        </div>
      </div>

      <NotificationFeed notifications={notifications} loading={loading} />

    </AppShell>
  )
}
