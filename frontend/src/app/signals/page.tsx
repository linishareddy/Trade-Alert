'use client'
import { AppShell } from '@/components/layout/AppShell'
import { SignalTable } from '@/components/signals/SignalTable'
import { StatStrip } from '@/components/ui/StatStrip'
import { useAllSignals } from '@/hooks/useSignals'

export default function SignalsPage() {
  const { data, isLoading } = useAllSignals()
  const signals = data?.signals ?? []

  const byAction = signals.reduce<Record<string, number>>((acc, s) => {
    acc[s.action] = (acc[s.action] ?? 0) + 1
    return acc
  }, {})

  const statCards = [
    { label: 'Total Signals', value: String(signals.length) },
    { label: 'BUY', value: String(byAction['BUY'] ?? 0), color: 'text-green-600 dark:text-green-400' },
    { label: 'SELL / EXIT', value: String((byAction['SELL'] ?? 0) + (byAction['EXIT'] ?? 0)), color: 'text-red-600 dark:text-red-400' },
    { label: 'Options', value: String(signals.filter((s) => s.contract_type === 'CALL' || s.contract_type === 'PUT').length), color: 'text-amber-600 dark:text-amber-400' },
  ]

  return (
    <AppShell title="Signal Feed" subtitle="All parsed Discord trading signals">
      <StatStrip items={statCards} columns={4} />
      <SignalTable signals={signals} loading={isLoading} title="All Signals" />
    </AppShell>
  )
}
