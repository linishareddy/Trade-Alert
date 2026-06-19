'use client'
import Link from 'next/link'
import { AppShell } from '@/components/layout/AppShell'
import { KPICard } from '@/components/dashboard/KPICard'
import { PnLChart } from '@/components/dashboard/PnLChart'
import { OutcomeDonut } from '@/components/dashboard/OutcomeDonut'
import { SignalFunnel } from '@/components/dashboard/SignalFunnel'
import {
  PnLBySymbolChart,
  PnLDistributionChart,
  SignalsByHourChart,
} from '@/components/analytics/PerformanceCharts'
import { useTradeSummary, useAllTrades } from '@/hooks/useTrades'
import { useAllSignals } from '@/hooks/useSignals'
import { useConfig } from '@/hooks/useHealth'
import { DollarSign, TrendingUp, Activity, Target } from 'lucide-react'
import { fmtCurrency, fmtPercent } from '@/lib/utils/format'
import { Stagger, StaggerItem } from '@/components/motion/PageMotion'

export default function DashboardPage() {
  const { data: summary, isLoading: sumLoading } = useTradeSummary()
  const { data: tradesData, isLoading: tradesLoading } = useAllTrades()
  const { data: signalsData } = useAllSignals()
  const { data: config } = useConfig()

  const trades = tradesData?.trades ?? []
  const signals = signalsData?.signals ?? []

  const closed = trades.filter((t) => t.status === 'CLOSED')
  const tpHit = closed.filter((t) => t.exit_reason === 'TP_HIT').length
  const winRate = closed.length > 0 ? Math.round((tpHit / closed.length) * 100) : 0
  const kpiLoad = sumLoading || tradesLoading

  return (
    <AppShell title="Dashboard" subtitle="Trading overview and performance analytics">

      <Stagger className="space-y-4">
        <Stagger className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StaggerItem>
            <KPICard
              title="Total P&L"
              value={fmtCurrency(summary?.total_pnl_dollars)}
              subtitle={`${summary?.closed_trades ?? 0} closed trades`}
              icon={DollarSign}
              iconBg={(summary?.total_pnl_dollars ?? 0) >= 0 ? 'bg-green-50 dark:bg-green-950/50' : 'bg-red-50 dark:bg-red-950/50'}
              iconColor={(summary?.total_pnl_dollars ?? 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}
              trend={(summary?.total_pnl_dollars ?? 0) >= 0 ? 'up' : 'down'}
              loading={kpiLoad}
            />
          </StaggerItem>
          <StaggerItem>
            <KPICard
              title="Avg P&L per Trade"
              value={fmtPercent(summary?.avg_pnl_pct)}
              subtitle="Closed trades only"
              icon={TrendingUp}
              iconBg={(summary?.avg_pnl_pct ?? 0) >= 0 ? 'bg-blue-50 dark:bg-blue-950/50' : 'bg-red-50 dark:bg-red-950/50'}
              iconColor={(summary?.avg_pnl_pct ?? 0) >= 0 ? 'text-blue-600 dark:text-blue-400' : 'text-red-600 dark:text-red-400'}
              loading={kpiLoad}
            />
          </StaggerItem>
          <StaggerItem>
            <KPICard
              title="Win Rate"
              value={`${winRate}%`}
              subtitle={`${tpHit} TP hits of ${closed.length} closed`}
              icon={Target}
              iconBg="bg-amber-50 dark:bg-amber-950/50"
              iconColor="text-amber-600 dark:text-amber-400"
              change={winRate - 50}
              loading={kpiLoad}
            />
          </StaggerItem>
          <StaggerItem>
            <KPICard
              title="Open Positions"
              value={String(summary?.open_trades ?? 0)}
              subtitle={`${summary?.total_trades ?? 0} total trades`}
              icon={Activity}
              iconBg="bg-violet-50 dark:bg-violet-950/50"
              iconColor="text-violet-600 dark:text-violet-400"
              loading={kpiLoad}
            />
          </StaggerItem>
        </Stagger>

        <StaggerItem>
          <PnLChart trades={trades} loading={tradesLoading} />
        </StaggerItem>

        <Stagger className="grid gap-4 lg:grid-cols-2">
          <StaggerItem>
            <OutcomeDonut trades={trades} loading={tradesLoading} />
          </StaggerItem>
          <StaggerItem>
            <SignalFunnel trades={trades} signals={signals} loading={kpiLoad} />
          </StaggerItem>
        </Stagger>

        <Stagger className="grid gap-4 lg:grid-cols-2">
          <StaggerItem>
            <PnLDistributionChart trades={trades} config={config} />
          </StaggerItem>
          <StaggerItem>
            <PnLBySymbolChart trades={trades} />
          </StaggerItem>
          <StaggerItem>
            <SignalsByHourChart signals={signals} config={config} />
          </StaggerItem>
        </Stagger>

        <StaggerItem>
          <p className="text-center text-xs text-zinc-400 dark:text-zinc-500">
            Signal pipeline events live on{' '}
            <Link href="/notifications" className="font-medium text-blue-600 hover:underline dark:text-blue-400">
              Notifications
            </Link>
          </p>
        </StaggerItem>
      </Stagger>

    </AppShell>
  )
}
