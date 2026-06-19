'use client'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { useTheme } from 'next-themes'
import { format } from 'date-fns'
import type { PaperTrade } from '@/types'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { ChartSkeleton } from '@/components/ui/Skeleton'

interface PnLChartProps {
  trades: PaperTrade[]
  loading?: boolean
}

export function PnLChart({ trades, loading }: PnLChartProps) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const closed = [...trades]
    .filter((t) => t.status === 'CLOSED' && t.pnl_dollars != null && t.closed_at)
    .sort((a, b) => new Date(a.closed_at!).getTime() - new Date(b.closed_at!).getTime())

  let cumulative = 0
  const data = closed.map((t) => {
    cumulative += t.pnl_dollars!
    return {
      date: format(new Date(t.closed_at!), 'MMM d HH:mm'),
      pnl: parseFloat(cumulative.toFixed(2)),
      trade: t.symbol,
      individual: parseFloat(t.pnl_dollars!.toFixed(2)),
    }
  })

  const isPositive = (data[data.length - 1]?.pnl ?? 0) >= 0
  const lineColor = isPositive
    ? isDark ? '#22c55e' : '#16a34a'
    : isDark ? '#ef4444' : '#dc2626'
  const fillId = isPositive ? 'greenGrad' : 'redGrad'

  const gridColor = isDark ? '#27272a' : '#f4f4f5'
  const axisColor = isDark ? '#52525b' : '#a1a1aa'

  return (
    <Card padding="lg">
      <CardHeader>
        <div>
          <CardTitle>Cumulative P&L</CardTitle>
          <CardDescription className="mt-0.5">Running total across all closed trades</CardDescription>
        </div>
        {data.length > 0 && (
          <p className={`text-lg font-bold ${isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
            {data[data.length - 1].pnl >= 0 ? '+' : ''}${data[data.length - 1].pnl.toFixed(2)}
          </p>
        )}
      </CardHeader>

      {loading ? (
        <ChartSkeleton height={220} />
      ) : data.length === 0 ? (
        <div className="flex h-56 items-center justify-center text-sm text-zinc-400 dark:text-zinc-500">
          No closed trades yet
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="greenGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="redGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke={gridColor} strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: axisColor }}
              axisLine={false}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 10, fill: axisColor }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `$${v}`}
              width={52}
            />
            <Tooltip
              contentStyle={{
                background: isDark ? '#18181b' : '#ffffff',
                border: `1px solid ${isDark ? '#27272a' : '#e4e4e7'}`,
                borderRadius: '8px',
                fontSize: '12px',
                color: isDark ? '#fafafa' : '#09090b',
              }}
              formatter={(value: number, _: string, props: { payload?: { trade?: string; individual?: number } }) => [
                `$${(value as number).toFixed(2)}`,
                `Cumulative (${props.payload?.trade ?? ''} ${(props.payload?.individual ?? 0) >= 0 ? '+' : ''}$${(props.payload?.individual ?? 0)})`,
              ]}
            />
            <Area
              type="monotone"
              dataKey="pnl"
              stroke={lineColor}
              strokeWidth={2}
              fill={`url(#${fillId})`}
              dot={data.length < 20 ? { r: 3, fill: lineColor, strokeWidth: 0 } : false}
              activeDot={{ r: 4, fill: lineColor }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </Card>
  )
}
