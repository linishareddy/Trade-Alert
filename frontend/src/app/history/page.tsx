'use client'
import { AppShell } from '@/components/layout/AppShell'
import { TradeTable } from '@/components/trades/TradeTable'
import { StatStrip } from '@/components/ui/StatStrip'
import { useTradeSummary, useTrades } from '@/hooks/useTrades'
import { fmtCurrency } from '@/lib/utils/format'

export default function HistoryPage() {
  const { data: tradesData, isLoading } = useTrades({ limit: 500 })
  const { data: summary } = useTradeSummary()
  const trades = tradesData?.trades ?? []

  const closed = trades.filter((t) => t.status === 'CLOSED')
  const tpHit = closed.filter((t) => t.exit_reason === 'TP_HIT').length
  const slHit = closed.filter((t) => t.exit_reason === 'SL_HIT').length
  const winRate = closed.length > 0 ? Math.round((tpHit / closed.length) * 100) : 0

  const stats = [
    { label: 'Total Trades', value: String(summary?.total_trades ?? '—') },
    { label: 'Closed', value: String(summary?.closed_trades ?? '—') },
    { label: 'Win Rate', value: `${winRate}%`, positive: winRate > 50 },
    { label: 'TP Hits', value: String(tpHit), positive: true },
    { label: 'SL Hits', value: String(slHit), positive: false },
    { label: 'Total P&L', value: fmtCurrency(summary?.total_pnl_dollars), positive: (summary?.total_pnl_dollars ?? 0) >= 0 },
  ]

  return (
    <AppShell title="Trade History" subtitle="All executed and cancelled trades">
      <StatStrip items={stats} />
      <TradeTable trades={trades} loading={isLoading} showFilters title="All Trades" />
    </AppShell>
  )
}
