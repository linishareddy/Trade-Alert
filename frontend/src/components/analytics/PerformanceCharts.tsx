'use client'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { useTheme } from 'next-themes'
import type { PaperTrade, Signal, ConfigResponse } from '@/types'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { getHours } from 'date-fns'
import { cn } from '@/lib/utils/cn'

const CHART_H = 160

function EmptyChart({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center rounded-lg border border-dashed border-zinc-200 bg-zinc-50/50 text-sm text-zinc-400 dark:border-zinc-800 dark:bg-zinc-900/50 dark:text-zinc-500" style={{ height: CHART_H }}>
      {label}
    </div>
  )
}

export function PnLBySymbolChart({ trades, className }: { trades: PaperTrade[]; className?: string }) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const bySymbol: Record<string, number> = {}
  for (const t of trades) {
    if (t.status === 'CLOSED' && t.pnl_dollars != null) {
      bySymbol[t.symbol] = (bySymbol[t.symbol] ?? 0) + t.pnl_dollars
    }
  }

  const data = Object.entries(bySymbol)
    .map(([symbol, pnl]) => ({ symbol, pnl: parseFloat(pnl.toFixed(2)) }))
    .sort((a, b) => b.pnl - a.pnl)
    .slice(0, 10)

  const axisColor = isDark ? '#52525b' : '#a1a1aa'
  const gridColor = isDark ? '#27272a' : '#f4f4f5'
  const hasData = data.length > 0
  const yMax = hasData ? Math.max(...data.map((d) => Math.abs(d.pnl)), 1) : 1

  return (
    <Card padding="md" className={cn('flex flex-col', className)}>
      <CardHeader className="mb-2 shrink-0">
        <div>
          <CardTitle>P&L by Symbol</CardTitle>
          <CardDescription className="mt-0.5">Total realized P&L per ticker</CardDescription>
        </div>
      </CardHeader>
      {!hasData ? (
        <EmptyChart label="No closed trades yet" />
      ) : (
        <ResponsiveContainer width="100%" height={CHART_H}>
          <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
            <CartesianGrid stroke={gridColor} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="symbol" tick={{ fontSize: 10, fill: axisColor }} axisLine={false} tickLine={false} />
            <YAxis
              tick={{ fontSize: 10, fill: axisColor }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `$${v}`}
              width={48}
              domain={[-yMax * 1.1, yMax * 1.1]}
            />
            <Tooltip
              contentStyle={{ background: isDark ? '#18181b' : '#fff', border: `1px solid ${isDark ? '#27272a' : '#e4e4e7'}`, borderRadius: '8px', fontSize: '12px' }}
              formatter={(v: number) => [`$${v.toFixed(2)}`, 'P&L']}
            />
            <Bar dataKey="pnl" radius={[4, 4, 0, 0]}>
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.pnl >= 0 ? (isDark ? '#22c55e' : '#16a34a') : (isDark ? '#ef4444' : '#dc2626')} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  )
}

export function PnLDistributionChart({ trades, config, className }: { trades: PaperTrade[]; config?: ConfigResponse; className?: string }) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sl = (config?.stop_loss_pct ?? 0.10) * 100
  const tp = (config?.take_profit_pct ?? 0.15) * 100
  const slH = sl / 2
  const tpT = tp / 3
  const tpTT = (tp * 2) / 3

  const buckets = [
    { label: `<-${sl}%`, min: -Infinity, max: -sl, count: 0 },
    { label: `-${sl} to -${slH}%`, min: -sl, max: -slH, count: 0 },
    { label: `-${slH} to 0%`, min: -slH, max: 0, count: 0 },
    { label: `0 to +${tpT.toFixed(0)}%`, min: 0, max: tpT, count: 0 },
    { label: `+${tpT.toFixed(0)} to +${tpTT.toFixed(0)}%`, min: tpT, max: tpTT, count: 0 },
    { label: `+${tpTT.toFixed(0)} to +${tp}%`, min: tpTT, max: tp, count: 0 },
    { label: `>+${tp}%`, min: tp, max: Infinity, count: 0 },
  ]

  for (const t of trades) {
    if (t.status === 'CLOSED' && t.pnl_pct != null) {
      const b = buckets.find((bk) => t.pnl_pct! >= bk.min && t.pnl_pct! < bk.max)
      if (b) b.count++
    }
  }

  const axisColor = isDark ? '#52525b' : '#a1a1aa'
  const gridColor = isDark ? '#27272a' : '#f4f4f5'
  const maxCount = Math.max(...buckets.map((b) => b.count), 1)

  return (
    <Card padding="md" className={cn('flex flex-col', className)}>
      <CardHeader className="mb-2 shrink-0">
        <div>
          <CardTitle>P&L Distribution</CardTitle>
          <CardDescription className="mt-0.5">Trade count by P&L bucket</CardDescription>
        </div>
      </CardHeader>
      <ResponsiveContainer width="100%" height={CHART_H}>
        <BarChart data={buckets} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={gridColor} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 8, fill: axisColor }} axisLine={false} tickLine={false} />
          <YAxis
            tick={{ fontSize: 10, fill: axisColor }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
            width={28}
            domain={[0, maxCount + 1]}
          />
          <Tooltip
            contentStyle={{ background: isDark ? '#18181b' : '#fff', border: `1px solid ${isDark ? '#27272a' : '#e4e4e7'}`, borderRadius: '8px', fontSize: '12px' }}
            formatter={(v: number) => [v, 'Trades']}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {buckets.map((b, i) => (
              <Cell
                key={i}
                fill={b.min >= 0 ? (isDark ? '#22c55e' : '#16a34a') : (isDark ? '#ef4444' : '#dc2626')}
                fillOpacity={b.min >= 0 ? 0.85 : 0.7}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )
}

export function SignalsByHourChart({ signals, config, className }: { signals: Signal[]; config?: ConfigResponse; className?: string }) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const marketOpenHour = config ? parseInt(config.market_open.split(':')[0], 10) : 9
  const marketCloseHour = config ? parseInt(config.market_close.split(':')[0], 10) : 16

  const byHour: Record<number, number> = {}
  for (const s of signals) {
    const h = getHours(new Date(s.created_at))
    byHour[h] = (byHour[h] ?? 0) + 1
  }

  const data = Array.from({ length: 24 }, (_, h) => ({
    hour: `${h}:00`,
    count: byHour[h] ?? 0,
    isMarket: h >= marketOpenHour && h < marketCloseHour,
  }))

  const axisColor = isDark ? '#52525b' : '#a1a1aa'
  const gridColor = isDark ? '#27272a' : '#f4f4f5'
  const maxCount = Math.max(...data.map((d) => d.count), 1)

  return (
    <Card padding="md" className={className}>
      <CardHeader className="mb-2 shrink-0">
        <div>
          <CardTitle>Signals by Hour</CardTitle>
          <CardDescription className="mt-0.5">When Discord sends the most signals</CardDescription>
        </div>
      </CardHeader>
      <ResponsiveContainer width="100%" height={140}>
        <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={gridColor} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="hour" tick={{ fontSize: 8, fill: axisColor }} axisLine={false} tickLine={false} interval={3} />
          <YAxis
            tick={{ fontSize: 10, fill: axisColor }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
            width={28}
            domain={[0, maxCount + 1]}
          />
          <Tooltip
            contentStyle={{ background: isDark ? '#18181b' : '#fff', border: `1px solid ${isDark ? '#27272a' : '#e4e4e7'}`, borderRadius: '8px', fontSize: '12px' }}
          />
          <Bar dataKey="count" radius={[3, 3, 0, 0]}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.isMarket ? (isDark ? '#3b82f6' : '#2563eb') : (isDark ? '#3f3f46' : '#d4d4d8')} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="mt-2 text-center text-[10px] text-zinc-400 dark:text-zinc-500">
        <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-blue-500" />
        Market hours ({config?.market_open ?? '09:30'}–{config?.market_close ?? '16:00'} ET)
      </p>
    </Card>
  )
}
