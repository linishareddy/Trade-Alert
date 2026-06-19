'use client'
import { AppShell } from '@/components/layout/AppShell'
import { TradeTable } from '@/components/trades/TradeTable'
import { useOpenTrades } from '@/hooks/useTrades'
import { fmtPrice, fmtDuration } from '@/lib/utils/format'
import { TrendingUp } from 'lucide-react'
import { EmptyState } from '@/components/ui/EmptyState'
import { Card } from '@/components/ui/Card'
import { cn } from '@/lib/utils/cn'

function OpenPositionCard({ trade }: { trade: import('@/types').PaperTrade }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 transition-all hover:border-zinc-300 hover:shadow-sm dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-lg font-bold text-zinc-900 dark:text-zinc-100">{trade.symbol}</p>
          <p className="text-xs text-zinc-400 dark:text-zinc-500">{trade.broker.toUpperCase()} • {trade.qty} share{trade.qty !== 1 ? 's' : ''}</p>
        </div>
        <span className="flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700 dark:border-amber-800/50 dark:bg-amber-950/30 dark:text-amber-400">
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-amber-500" />
          </span>
          LIVE
        </span>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-lg bg-zinc-50 p-2 dark:bg-zinc-800/50">
          <p className="text-[10px] uppercase tracking-wide text-zinc-400 dark:text-zinc-500">Entry</p>
          <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{fmtPrice(trade.entry_price)}</p>
        </div>
        <div className="rounded-lg bg-green-50 p-2 dark:bg-green-950/30">
          <p className="text-[10px] uppercase tracking-wide text-green-500 dark:text-green-400">Take Profit</p>
          <p className="text-sm font-semibold text-green-700 dark:text-green-300">{fmtPrice(trade.take_profit_price)}</p>
        </div>
        <div className="rounded-lg bg-red-50 p-2 dark:bg-red-950/30">
          <p className="text-[10px] uppercase tracking-wide text-red-500 dark:text-red-400">Stop Loss</p>
          <p className="text-sm font-semibold text-red-700 dark:text-red-300">{fmtPrice(trade.stop_loss_price)}</p>
        </div>
      </div>

      {trade.ema9 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {[
            { label: 'EMA9', pass: trade.entry_price > (trade.ema9 ?? 0) },
            { label: 'EMA13', pass: trade.entry_price > (trade.ema13 ?? 0) },
            { label: 'EMA21', pass: trade.entry_price > (trade.ema21 ?? 0) },
            { label: 'VWAP', pass: trade.entry_price > (trade.vwap ?? 0) },
          ].map((c) => (
            <span key={c.label} className={cn(
              'rounded px-1.5 py-0.5 text-[10px] font-medium',
              c.pass ? 'bg-green-50 text-green-700 dark:bg-green-950/50 dark:text-green-400' : 'bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-400'
            )}>
              {c.label} {c.pass ? '✓' : '✗'}
            </span>
          ))}
        </div>
      )}

      <p className="mt-2 text-[10px] text-zinc-400 dark:text-zinc-500">
        Held for {fmtDuration(trade.created_at, null)}
      </p>
    </div>
  )
}

export default function PositionsPage() {
  const { data, isLoading } = useOpenTrades()
  const trades = data?.trades ?? []

  return (
    <AppShell title="Active Positions" subtitle={`${trades.length} open position${trades.length !== 1 ? 's' : ''}`}>
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-48 animate-pulse rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900" />
          ))}
        </div>
      ) : trades.length === 0 ? (
        <EmptyState
          icon={TrendingUp}
          title="No open positions"
          description="Active trades will appear here once a signal passes EMA/VWAP validation and a bracket order is placed."
        />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {trades.map((t) => <OpenPositionCard key={t.id} trade={t} />)}
          </div>
          <div className="mt-6">
            <TradeTable trades={trades} loading={isLoading} showFilters={false} title="Open Positions Table" />
          </div>
        </>
      )}
    </AppShell>
  )
}
