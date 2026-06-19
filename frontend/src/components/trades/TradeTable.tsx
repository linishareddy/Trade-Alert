'use client'
import { useState } from 'react'
import { ChevronDown, ChevronUp, Search, Filter } from 'lucide-react'
import type { PaperTrade } from '@/types'
import { fmtPrice, fmtPercent, fmtCurrency, fmtDate, fmtDuration } from '@/lib/utils/format'
import { ExitReasonBadge, StatusBadge, ValidationBadge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { TableRowSkeleton } from '@/components/ui/Skeleton'
import { cn } from '@/lib/utils/cn'
import { TrendingUp } from 'lucide-react'

type SortKey = 'symbol' | 'created_at' | 'pnl_pct' | 'status' | 'entry_price'
type SortDir = 'asc' | 'desc'

interface TradeTableProps {
  trades: PaperTrade[]
  loading?: boolean
  showFilters?: boolean
  title?: string
}

function EmaVwapCell({ trade }: { trade: PaperTrade }) {
  if (!trade.ema9) return <span className="text-zinc-400 dark:text-zinc-500">—</span>
  const checks = [
    { label: 'EMA9', pass: trade.entry_price > (trade.ema9 ?? 0) },
    { label: 'EMA13', pass: trade.entry_price > (trade.ema13 ?? 0) },
    { label: 'EMA21', pass: trade.entry_price > (trade.ema21 ?? 0) },
    { label: 'VWAP', pass: trade.entry_price > (trade.vwap ?? 0) },
  ]
  return (
    <div className="flex gap-0.5">
      {checks.map((c) => (
        <span
          key={c.label}
          title={`${c.label}: ${c.pass ? 'PASS' : 'FAIL'}`}
          className={cn(
            'inline-flex items-center rounded px-1 py-0.5 text-[9px] font-medium',
            c.pass
              ? 'bg-green-50 text-green-700 dark:bg-green-950/50 dark:text-green-400'
              : 'bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-400'
          )}
        >
          {c.label.replace('EMA', 'E')}
        </span>
      ))}
    </div>
  )
}

export function TradeTable({ trades, loading, showFilters = true, title }: TradeTableProps) {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('ALL')
  const [exitFilter, setExitFilter] = useState<string>('ALL')
  const [sortKey, setSortKey] = useState<SortKey>('created_at')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [page, setPage] = useState(0)
  const pageSize = 10

  const filtered = trades
    .filter((t) => {
      const matchSearch = !search || t.symbol.toLowerCase().includes(search.toLowerCase())
      const matchStatus = statusFilter === 'ALL' || t.status === statusFilter
      const matchExit = exitFilter === 'ALL' || t.exit_reason === exitFilter
      return matchSearch && matchStatus && matchExit
    })
    .sort((a, b) => {
      let av: number | string, bv: number | string
      switch (sortKey) {
        case 'symbol': av = a.symbol; bv = b.symbol; break
        case 'created_at': av = a.created_at; bv = b.created_at; break
        case 'pnl_pct': av = a.pnl_pct ?? -999; bv = b.pnl_pct ?? -999; break
        case 'entry_price': av = a.entry_price; bv = b.entry_price; break
        case 'status': av = a.status; bv = b.status; break
        default: av = a.created_at; bv = b.created_at
      }
      if (av < bv) return sortDir === 'asc' ? -1 : 1
      if (av > bv) return sortDir === 'asc' ? 1 : -1
      return 0
    })

  const totalPages = Math.ceil(filtered.length / pageSize)
  const paginated = filtered.slice(page * pageSize, (page + 1) * pageSize)

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortKey(key); setSortDir('desc') }
    setPage(0)
  }

  function SortIcon({ col }: { col: SortKey }) {
    if (sortKey !== col) return <ChevronUp className="h-3 w-3 text-zinc-300 dark:text-zinc-600" />
    return sortDir === 'asc'
      ? <ChevronUp className="h-3 w-3 text-blue-500" />
      : <ChevronDown className="h-3 w-3 text-blue-500" />
  }

  return (
    <div className="overflow-hidden rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      {/* Toolbar */}
      {showFilters && (
        <div className="flex flex-col gap-3 border-b border-zinc-100 px-4 py-3 dark:border-zinc-800 sm:flex-row sm:items-center sm:justify-between">
          {title && <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{title}</h3>}
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-400" />
              <input
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(0) }}
                placeholder="Symbol..."
                className="h-8 w-32 rounded-lg border border-zinc-200 bg-zinc-50 pl-8 pr-3 text-xs focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(0) }}
              className="h-8 rounded-lg border border-zinc-200 bg-zinc-50 px-2 text-xs text-zinc-700 focus:border-blue-400 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
            >
              <option value="ALL">All Status</option>
              <option value="OPEN">Open</option>
              <option value="CLOSED">Closed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
            <select
              value={exitFilter}
              onChange={(e) => { setExitFilter(e.target.value); setPage(0) }}
              className="h-8 rounded-lg border border-zinc-200 bg-zinc-50 px-2 text-xs text-zinc-700 focus:border-blue-400 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
            >
              <option value="ALL">All Exits</option>
              <option value="TP_HIT">TP Hit</option>
              <option value="SL_HIT">SL Hit</option>
              <option value="MANUAL">Manual</option>
            </select>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-zinc-100 dark:divide-zinc-800">
          <thead className="bg-zinc-50 dark:bg-zinc-800/50">
            <tr>
              {[
                { key: 'symbol' as SortKey, label: 'SYMBOL' },
                { key: 'entry_price' as SortKey, label: 'ENTRY' },
                { key: null, label: 'TP / SL' },
                { key: 'pnl_pct' as SortKey, label: 'P&L' },
                { key: 'status' as SortKey, label: 'STATUS' },
                { key: null, label: 'EXIT' },
                { key: null, label: 'EMA/VWAP' },
                { key: 'created_at' as SortKey, label: 'OPENED' },
                { key: null, label: 'DURATION' },
              ].map(({ key, label }) => (
                <th
                  key={label}
                  onClick={key ? () => toggleSort(key) : undefined}
                  className={cn(
                    'px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400',
                    key && 'cursor-pointer select-none hover:text-zinc-700 dark:hover:text-zinc-200'
                  )}
                >
                  <div className="flex items-center gap-1">
                    {label}
                    {key && <SortIcon col={key} />}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => <TableRowSkeleton key={i} cols={9} />)
            ) : paginated.length === 0 ? (
              <tr>
                <td colSpan={9}>
                  <EmptyState
                    icon={TrendingUp}
                    title="No trades found"
                    description="Trades will appear here once the system processes signals."
                  />
                </td>
              </tr>
            ) : (
              paginated.map((trade) => (
                <>
                  <tr
                    key={trade.id}
                    onClick={() => setExpanded(expanded === trade.id ? null : trade.id)}
                    className="cursor-pointer transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-800/40"
                  >
                    <td className="px-4 py-3">
                      <div>
                        <span className="font-semibold text-zinc-900 dark:text-zinc-100">{trade.symbol}</span>
                        <p className="text-[10px] text-zinc-400 dark:text-zinc-500">{trade.broker.toUpperCase()}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-zinc-700 dark:text-zinc-300">
                      {fmtPrice(trade.entry_price)}
                    </td>
                    <td className="px-4 py-3 text-xs">
                      <span className="text-green-600 dark:text-green-400">{fmtPrice(trade.take_profit_price)}</span>
                      {' / '}
                      <span className="text-red-600 dark:text-red-400">{fmtPrice(trade.stop_loss_price)}</span>
                    </td>
                    <td className="px-4 py-3">
                      {trade.pnl_pct != null ? (
                        <div>
                          <span className={cn(
                            'text-sm font-semibold',
                            trade.pnl_pct >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                          )}>
                            {fmtPercent(trade.pnl_pct)}
                          </span>
                          <p className="text-[10px] text-zinc-400 dark:text-zinc-500">{fmtCurrency(trade.pnl_dollars)}</p>
                        </div>
                      ) : (
                        <span className="text-sm text-zinc-400 dark:text-zinc-500">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={trade.status} /></td>
                    <td className="px-4 py-3"><ExitReasonBadge reason={trade.exit_reason} /></td>
                    <td className="px-4 py-3"><EmaVwapCell trade={trade} /></td>
                    <td className="px-4 py-3 text-xs text-zinc-500 dark:text-zinc-400">{fmtDate(trade.created_at)}</td>
                    <td className="px-4 py-3 text-xs text-zinc-500 dark:text-zinc-400">
                      {fmtDuration(trade.created_at, trade.closed_at)}
                    </td>
                  </tr>

                  {expanded === trade.id && (
                    <tr key={`exp-${trade.id}`} className="bg-zinc-50/50 dark:bg-zinc-800/20">
                      <td colSpan={9} className="px-6 py-4">
                        <div className="grid grid-cols-2 gap-4 text-xs sm:grid-cols-4">
                          {[
                            ['Broker Order ID', trade.broker_order_id ?? '—'],
                            ['EMA9', trade.ema9 != null ? `$${trade.ema9.toFixed(2)}` : '—'],
                            ['EMA13', trade.ema13 != null ? `$${trade.ema13.toFixed(2)}` : '—'],
                            ['EMA21', trade.ema21 != null ? `$${trade.ema21.toFixed(2)}` : '—'],
                            ['VWAP', trade.vwap != null ? `$${trade.vwap.toFixed(2)}` : '—'],
                            ['Exit Price', fmtPrice(trade.exit_price)],
                            ['Closed At', fmtDate(trade.closed_at)],
                            ['Qty', trade.qty],
                          ].map(([label, val]) => (
                            <div key={String(label)}>
                              <p className="text-[10px] uppercase tracking-wide text-zinc-400 dark:text-zinc-500">{label}</p>
                              <p className="mt-0.5 font-medium text-zinc-900 dark:text-zinc-100">{val}</p>
                            </div>
                          ))}
                          {trade.validation_reason && (
                            <div className="col-span-2 sm:col-span-4">
                              <p className="text-[10px] uppercase tracking-wide text-zinc-400 dark:text-zinc-500">Validation Reason</p>
                              <p className="mt-0.5 text-zinc-600 dark:text-zinc-300">{trade.validation_reason}</p>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {!loading && filtered.length > pageSize && (
        <div className="flex items-center justify-between border-t border-zinc-100 px-4 py-3 dark:border-zinc-800">
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, filtered.length)} of {filtered.length} trades
          </p>
          <div className="flex gap-1">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="rounded px-3 py-1 text-xs text-zinc-600 hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-40 dark:text-zinc-400 dark:hover:bg-zinc-800"
            >
              Previous
            </button>
            {Array.from({ length: Math.min(5, totalPages) }).map((_, i) => {
              const pageNum = Math.max(0, Math.min(page - 2, totalPages - 5)) + i
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={cn(
                    'rounded px-2.5 py-1 text-xs',
                    pageNum === page
                      ? 'bg-blue-600 text-white'
                      : 'text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800'
                  )}
                >
                  {pageNum + 1}
                </button>
              )
            })}
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="rounded px-3 py-1 text-xs text-zinc-600 hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-40 dark:text-zinc-400 dark:hover:bg-zinc-800"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
