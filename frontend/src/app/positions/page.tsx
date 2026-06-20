'use client'
import { AppShell } from '@/components/layout/AppShell'
import { TradeTable } from '@/components/trades/TradeTable'
import { StatStrip } from '@/components/ui/StatStrip'
import { useOpenTrades } from '@/hooks/useTrades'
import { fmtPrice } from '@/lib/utils/format'

export default function PositionsPage() {
  const { data, isLoading } = useOpenTrades()
  const trades = data?.trades ?? []

  const symbols = [...new Set(trades.map((t) => t.symbol))]
  const totalQty = trades.reduce((sum, t) => sum + t.qty, 0)
  const avgEntry = trades.length
    ? trades.reduce((sum, t) => sum + t.entry_price, 0) / trades.length
    : null
  const validated = trades.filter((t) => t.validation_passed).length

  const stats = [
    { label: 'Open Positions', value: String(trades.length) },
    { label: 'Symbols', value: symbols.length ? symbols.join(', ') : '—' },
    { label: 'Total Shares', value: String(totalQty) },
    { label: 'Avg Entry', value: avgEntry != null ? fmtPrice(avgEntry) : '—' },
    { label: 'EMA/VWAP Pass', value: String(validated), positive: validated > 0 },
    { label: 'Broker', value: trades[0]?.broker.toUpperCase() ?? '—' },
  ]

  return (
    <AppShell title="Active Positions" subtitle="Live open trades on Alpaca">
      <StatStrip items={stats} columns={6} />
      <TradeTable
        trades={trades}
        loading={isLoading}
        showFilters
        hideStatusFilter
        title="Open Positions"
      />
    </AppShell>
  )
}
