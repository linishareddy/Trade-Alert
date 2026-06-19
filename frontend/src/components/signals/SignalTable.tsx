'use client'
import { useState } from 'react'
import { Search, Radio } from 'lucide-react'
import type { Signal } from '@/types'
import { fmtPrice, fmtDate, fmtTimeAgo } from '@/lib/utils/format'
import { ActionBadge, ContractBadge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { TableRowSkeleton } from '@/components/ui/Skeleton'

interface SignalTableProps {
  signals: Signal[]
  loading?: boolean
  title?: string
}

export function SignalTable({ signals, loading, title }: SignalTableProps) {
  const [search, setSearch] = useState('')
  const [actionFilter, setActionFilter] = useState('ALL')
  const [page, setPage] = useState(0)
  const pageSize = 15

  const filtered = signals.filter((s) => {
    const matchSearch = !search || s.ticker.toLowerCase().includes(search.toLowerCase())
    const matchAction = actionFilter === 'ALL' || s.action === actionFilter
    return matchSearch && matchAction
  })

  const sorted = [...filtered].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )

  const totalPages = Math.ceil(sorted.length / pageSize)
  const paginated = sorted.slice(page * pageSize, (page + 1) * pageSize)

  const columns = ['TICKER', 'ACTION', 'TYPE', 'ENTRY', 'TARGET', 'STOP', 'RECEIVED']

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex flex-col gap-3 border-b border-zinc-100 px-4 py-3 dark:border-zinc-800 sm:flex-row sm:items-center sm:justify-between">
        {title && <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{title}</h3>}
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-400" />
            <input
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(0) }}
              placeholder="Ticker..."
              className="h-8 w-28 rounded-lg border border-zinc-200 bg-zinc-50 pl-8 pr-3 text-xs focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
            />
          </div>
          <select
            value={actionFilter}
            onChange={(e) => { setActionFilter(e.target.value); setPage(0) }}
            className="h-8 rounded-lg border border-zinc-200 bg-zinc-50 px-2 text-xs text-zinc-700 focus:border-blue-400 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
          >
            <option value="ALL">All Actions</option>
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
            <option value="EXIT">EXIT</option>
            <option value="HOLD">HOLD</option>
            <option value="SL_HIT">SL_HIT</option>
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-zinc-100 dark:divide-zinc-800">
          <thead className="bg-zinc-50 dark:bg-zinc-800/50">
            <tr>
              {columns.map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {loading ? (
              Array.from({ length: 6 }).map((_, i) => <TableRowSkeleton key={i} cols={columns.length} />)
            ) : paginated.length === 0 ? (
              <tr>
                <td colSpan={columns.length}>
                  <EmptyState icon={Radio} title="No signals yet" description="Signals from Discord will appear here." />
                </td>
              </tr>
            ) : (
              paginated.map((signal) => (
                <tr key={signal.id} className="transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-800/40">
                  <td className="px-4 py-3">
                    <span className="font-semibold text-zinc-900 dark:text-zinc-100">{signal.ticker}</span>
                  </td>
                  <td className="px-4 py-3"><ActionBadge action={signal.action} /></td>
                  <td className="px-4 py-3"><ContractBadge type={signal.contract_type} /></td>
                  <td className="px-4 py-3 text-xs text-zinc-700 dark:text-zinc-300">{fmtPrice(signal.entry_price)}</td>
                  <td className="px-4 py-3 text-xs text-green-600 dark:text-green-400">{fmtPrice(signal.target_price)}</td>
                  <td className="px-4 py-3 text-xs text-red-600 dark:text-red-400">{fmtPrice(signal.stop_loss)}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-zinc-500 dark:text-zinc-400" title={fmtDate(signal.created_at)}>
                      {fmtTimeAgo(signal.created_at)}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {!loading && filtered.length > pageSize && (
        <div className="flex items-center justify-between border-t border-zinc-100 px-4 py-3 dark:border-zinc-800">
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            {page * pageSize + 1}–{Math.min((page + 1) * pageSize, sorted.length)} of {sorted.length} signals
          </p>
          <div className="flex gap-1">
            <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}
              className="rounded px-3 py-1 text-xs text-zinc-600 hover:bg-zinc-100 disabled:opacity-40 dark:text-zinc-400 dark:hover:bg-zinc-800">
              Previous
            </button>
            <button onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}
              className="rounded px-3 py-1 text-xs text-zinc-600 hover:bg-zinc-100 disabled:opacity-40 dark:text-zinc-400 dark:hover:bg-zinc-800">
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
