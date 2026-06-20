'use client'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { useTheme } from 'next-themes'
import type { PaperTrade } from '@/types'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { cn } from '@/lib/utils/cn'

interface OutcomeDonutProps {
  trades: PaperTrade[]
  loading?: boolean
  className?: string
}

export function OutcomeDonut({ trades, loading, className }: OutcomeDonutProps) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const tpHit = trades.filter((t) => t.exit_reason === 'TP_HIT').length
  const slHit = trades.filter((t) => t.exit_reason === 'SL_HIT').length
  const cancelled = trades.filter((t) => t.status === 'CANCELLED').length
  const open = trades.filter((t) => t.status === 'OPEN').length

  const data = [
    { name: 'TP Hit', value: tpHit, color: isDark ? '#22c55e' : '#16a34a' },
    { name: 'SL Hit', value: slHit, color: isDark ? '#ef4444' : '#dc2626' },
    { name: 'Open', value: open, color: isDark ? '#f59e0b' : '#d97706' },
    { name: 'Cancelled', value: cancelled, color: isDark ? '#52525b' : '#a1a1aa' },
  ].filter((d) => d.value > 0)

  const total = tpHit + slHit + cancelled + open
  const winRate = total > 0 ? Math.round((tpHit / (tpHit + slHit || 1)) * 100) : 0

  return (
    <Card padding="md" className={cn('flex flex-col', className)}>
      <CardHeader className="mb-2 shrink-0">
        <div>
          <CardTitle>Trade Outcomes</CardTitle>
          <CardDescription className="mt-0.5">TP vs SL vs Cancelled</CardDescription>
        </div>
        {total > 0 && (
          <div className="text-right">
            <p className="text-lg font-bold text-zinc-900 dark:text-zinc-100">{winRate}%</p>
            <p className="text-[10px] text-zinc-500 dark:text-zinc-400">win rate</p>
          </div>
        )}
      </CardHeader>

      <div className="min-h-0 flex-1">
        {loading || data.length === 0 ? (
          <div className="flex h-full min-h-[160px] items-center justify-center rounded-lg border border-dashed border-zinc-200 bg-zinc-50/50 text-sm text-zinc-400 dark:border-zinc-800 dark:bg-zinc-900/50 dark:text-zinc-500">
            {loading ? 'Loading...' : 'No trade data yet'}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={160} minHeight={160}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={44}
                outerRadius={62}
                paddingAngle={3}
                dataKey="value"
                strokeWidth={0}
              >
                {data.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: isDark ? '#18181b' : '#ffffff',
                  border: `1px solid ${isDark ? '#27272a' : '#e4e4e7'}`,
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
              />
              <Legend
                iconType="circle"
                iconSize={7}
                wrapperStyle={{ fontSize: '11px', paddingTop: '4px' }}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </Card>
  )
}
