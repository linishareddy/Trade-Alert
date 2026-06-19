'use client'
import { useState } from 'react'
import type { DerivedNotification, NotificationType } from '@/types'
import { fmtTime, fmtDate, fmtPrice, fmtPercent, fmtCurrency } from '@/lib/utils/format'
import {
  MessageCircle, TrendingUp, XCircle, CheckCircle2, TrendingDown,
  ChevronDown, ChevronUp,
} from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import { format, isToday, isYesterday } from 'date-fns'

// ── Type config (Lucide icons only, no emojis) ─────────────────────────────────

const TYPE_CONFIG: Record<NotificationType, {
  icon: React.ElementType
  label: string
  dot: string
  leftBorder: string
  iconRing: string
  iconColor: string
}> = {
  SIGNAL_RECEIVED: {
    icon: MessageCircle,
    label: 'Signal Received',
    dot: 'bg-blue-500',
    leftBorder: 'border-l-blue-500',
    iconRing: 'bg-blue-50 ring-blue-500/20 dark:bg-blue-950/60 dark:ring-blue-500/30',
    iconColor: 'text-blue-600 dark:text-blue-400',
  },
  TRADE_OPENED: {
    icon: TrendingUp,
    label: 'Trade Opened',
    dot: 'bg-amber-500',
    leftBorder: 'border-l-amber-500',
    iconRing: 'bg-amber-50 ring-amber-500/20 dark:bg-amber-950/60 dark:ring-amber-500/30',
    iconColor: 'text-amber-600 dark:text-amber-400',
  },
  SIGNAL_SKIPPED: {
    icon: XCircle,
    label: 'Signal Skipped',
    dot: 'bg-zinc-400',
    leftBorder: 'border-l-zinc-300 dark:border-l-zinc-600',
    iconRing: 'bg-zinc-100 ring-zinc-400/20 dark:bg-zinc-800/60 dark:ring-zinc-500/20',
    iconColor: 'text-zinc-500 dark:text-zinc-400',
  },
  TP_HIT: {
    icon: CheckCircle2,
    label: 'Take Profit Hit',
    dot: 'bg-green-500',
    leftBorder: 'border-l-green-500',
    iconRing: 'bg-green-50 ring-green-500/20 dark:bg-green-950/60 dark:ring-green-500/30',
    iconColor: 'text-green-600 dark:text-green-400',
  },
  SL_HIT: {
    icon: TrendingDown,
    label: 'Stop Loss Hit',
    dot: 'bg-red-500',
    leftBorder: 'border-l-red-500',
    iconRing: 'bg-red-50 ring-red-500/20 dark:bg-red-950/60 dark:ring-red-500/30',
    iconColor: 'text-red-600 dark:text-red-400',
  },
}

// ── Filter config (icons, no emoji) ──────────────────────────────────────────

const FILTERS: { label: string; type: NotificationType | 'ALL'; icon?: React.ElementType }[] = [
  { label: 'All',      type: 'ALL' },
  { label: 'Received', type: 'SIGNAL_RECEIVED', icon: MessageCircle },
  { label: 'Opened',   type: 'TRADE_OPENED',    icon: TrendingUp    },
  { label: 'Skipped',  type: 'SIGNAL_SKIPPED',  icon: XCircle       },
  { label: 'TP Hit',   type: 'TP_HIT',          icon: CheckCircle2  },
  { label: 'SL Hit',   type: 'SL_HIT',          icon: TrendingDown  },
]

// ── Notification body ─────────────────────────────────────────────────────────

function NotifBody({ notif }: { notif: DerivedNotification }) {
  const d = notif.details

  switch (notif.type) {
    case 'SIGNAL_RECEIVED':
      return (
        <div className="flex flex-wrap gap-x-4 gap-y-0.5 text-xs">
          <span className="text-zinc-500 dark:text-zinc-400">
            Action{' '}
            <span className="font-semibold text-green-600 dark:text-green-400">
              {String(d.action)}
            </span>
          </span>
          <span className="text-zinc-500 dark:text-zinc-400">
            Entry{' '}
            <span className="font-medium text-zinc-800 dark:text-zinc-200">
              {fmtPrice(d.entry_price as number)}
            </span>
          </span>
          <span className="text-zinc-500 dark:text-zinc-400">
            SL{' '}
            <span className="font-medium text-red-500 dark:text-red-400">
              {fmtPrice(d.stop_loss as number)}
            </span>
          </span>
        </div>
      )

    case 'TRADE_OPENED':
      return (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-x-4 gap-y-0.5 text-xs">
            <span className="text-zinc-500 dark:text-zinc-400">
              Qty <span className="font-medium text-zinc-800 dark:text-zinc-200">×{String(d.qty)}</span>
            </span>
            <span className="text-zinc-500 dark:text-zinc-400">
              Entry <span className="font-medium text-zinc-800 dark:text-zinc-200">{fmtPrice(d.entry_price as number)}</span>
            </span>
            <span className="text-zinc-500 dark:text-zinc-400">
              TP <span className="font-medium text-green-600 dark:text-green-400">{fmtPrice(d.take_profit_price as number)}</span>
            </span>
            <span className="text-zinc-500 dark:text-zinc-400">
              SL <span className="font-medium text-red-500 dark:text-red-400">{fmtPrice(d.stop_loss_price as number)}</span>
            </span>
          </div>
          <div className="flex gap-1">
            {(['ema9', 'ema13', 'ema21', 'vwap'] as const).map((k) => (
              <span
                key={k}
                className={cn(
                  'rounded px-1.5 py-0.5 text-[10px] font-semibold',
                  d[k]
                    ? 'bg-green-50 text-green-700 dark:bg-green-950/50 dark:text-green-400'
                    : 'bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-400',
                )}
              >
                {k.toUpperCase()}
              </span>
            ))}
          </div>
        </div>
      )

    case 'SIGNAL_SKIPPED':
      return (
        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          {String(d.validation_reason ?? 'EMA/VWAP validation did not pass')}
        </p>
      )

    case 'TP_HIT':
      return (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-0.5 text-xs">
          <span className="text-zinc-500 dark:text-zinc-400">
            Entry <span className="font-medium text-zinc-700 dark:text-zinc-200">{fmtPrice(d.entry_price as number)}</span>
          </span>
          <span className="text-zinc-500 dark:text-zinc-400">
            Exit <span className="font-medium text-zinc-700 dark:text-zinc-200">{fmtPrice(d.exit_price as number)}</span>
          </span>
          <span className="font-bold text-green-600 dark:text-green-400">
            {fmtPercent(d.pnl_pct as number)} · {fmtCurrency(d.pnl_dollars as number)}
          </span>
        </div>
      )

    case 'SL_HIT':
      return (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-0.5 text-xs">
          <span className="text-zinc-500 dark:text-zinc-400">
            Entry <span className="font-medium text-zinc-700 dark:text-zinc-200">{fmtPrice(d.entry_price as number)}</span>
          </span>
          <span className="text-zinc-500 dark:text-zinc-400">
            Exit <span className="font-medium text-zinc-700 dark:text-zinc-200">{fmtPrice(d.exit_price as number)}</span>
          </span>
          <span className="font-bold text-red-600 dark:text-red-400">
            {fmtPercent(d.pnl_pct as number)} · {fmtCurrency(d.pnl_dollars as number)}
          </span>
        </div>
      )
  }
}

// ── Single notification card ──────────────────────────────────────────────────

function NotifCard({ notif, isLast }: { notif: DerivedNotification; isLast: boolean }) {
  const cfg = TYPE_CONFIG[notif.type]
  const Icon = cfg.icon

  return (
    <div className="relative flex gap-4">
      {/* Timeline spine */}
      {!isLast && (
        <div className="absolute left-[19px] top-10 h-full w-px bg-zinc-200 dark:bg-zinc-800" />
      )}

      {/* Icon bubble */}
      <div className={cn(
        'relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full ring-1',
        cfg.iconRing,
      )}>
        <Icon className={cn('h-4 w-4', cfg.iconColor)} />
      </div>

      {/* Card — colored left border stripe */}
      <div className={cn(
        'mb-3 flex-1 overflow-hidden rounded-xl border border-zinc-200 border-l-4 bg-white p-4',
        'shadow-sm transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900',
        cfg.leftBorder,
      )}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
              {cfg.label}
              <span className="ml-2 font-bold">{notif.symbol}</span>
            </p>
          </div>
          <time
            className="shrink-0 text-[11px] text-zinc-400 dark:text-zinc-500"
            title={fmtDate(notif.timestamp)}
          >
            {fmtTime(notif.timestamp)}
          </time>
        </div>

        <div className="mt-2.5">
          <NotifBody notif={notif} />
        </div>
      </div>
    </div>
  )
}

// ── Date group label ──────────────────────────────────────────────────────────

function dateLabel(dateStr: string): string {
  const d = new Date(dateStr)
  if (isToday(d))     return 'Today'
  if (isYesterday(d)) return 'Yesterday'
  return format(d, 'MMMM d, yyyy')
}

function groupByDate(notifications: DerivedNotification[]) {
  const groups: { label: string; items: DerivedNotification[] }[] = []
  for (const n of notifications) {
    const label = dateLabel(n.timestamp)
    const existing = groups.find((g) => g.label === label)
    if (existing) existing.items.push(n)
    else groups.push({ label, items: [n] })
  }
  return groups
}

// ── Main feed ─────────────────────────────────────────────────────────────────

interface NotificationFeedProps {
  notifications: DerivedNotification[]
  loading?: boolean
}

export function NotificationFeed({ notifications, loading }: NotificationFeedProps) {
  const [filter, setFilter] = useState<NotificationType | 'ALL'>('ALL')
  const [showAll, setShowAll] = useState(false)

  if (loading) {
    return (
      <div className="space-y-3 pt-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex gap-4">
            <div className="h-10 w-10 animate-pulse rounded-full bg-zinc-200 dark:bg-zinc-800" />
            <div className="flex-1 animate-pulse rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
              <div className="flex justify-between">
                <div className="h-3.5 w-32 rounded bg-zinc-200 dark:bg-zinc-700" />
                <div className="h-3 w-16 rounded bg-zinc-200 dark:bg-zinc-700" />
              </div>
              <div className="mt-3 space-y-2">
                <div className="h-3 w-56 rounded bg-zinc-200 dark:bg-zinc-700" />
                <div className="h-3 w-40 rounded bg-zinc-200 dark:bg-zinc-700" />
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (notifications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-zinc-200 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800/50">
          <MessageCircle className="h-7 w-7 text-zinc-300 dark:text-zinc-600" />
        </div>
        <p className="mt-4 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
          No notifications yet
        </p>
        <p className="mt-1 max-w-xs text-xs text-zinc-400 dark:text-zinc-500">
          Events appear here as signals move through the pipeline — received, validated, traded, or skipped.
        </p>
      </div>
    )
  }

  const filtered = filter === 'ALL' ? notifications : notifications.filter((n) => n.type === filter)
  const visible  = showAll ? filtered : filtered.slice(0, 20)
  const groups   = groupByDate(visible)

  return (
    <div>
      {/* Filter chips — icon + label, no emoji */}
      <div className="mb-5 flex flex-wrap gap-2">
        {FILTERS.map(({ label, type, icon: FilterIcon }) => {
          const count = type === 'ALL'
            ? notifications.length
            : notifications.filter((n) => n.type === type).length
          const active = filter === type
          return (
            <button
              key={type}
              onClick={() => { setFilter(type); setShowAll(false) }}
              className={cn(
                'inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-all',
                active
                  ? 'border-blue-500 bg-blue-500 text-white shadow-sm'
                  : 'border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-400 dark:hover:border-zinc-600 dark:hover:bg-zinc-800',
              )}
            >
              {FilterIcon && (
                <FilterIcon className={cn('h-3 w-3', active ? 'text-white' : 'text-zinc-400 dark:text-zinc-500')} />
              )}
              {label}
              <span className={cn(
                'rounded-full px-1.5 py-0.5 text-[10px] font-semibold',
                active
                  ? 'bg-white/20 text-white'
                  : 'bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400',
              )}>
                {count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Timeline grouped by date */}
      {filtered.length === 0 ? (
        <p className="py-12 text-center text-sm text-zinc-400 dark:text-zinc-500">
          No {label(filter)} notifications.
        </p>
      ) : (
        <div>
          {groups.map((group) => (
            <div key={group.label} className="mb-2">
              {/* Date divider */}
              <div className="mb-4 flex items-center gap-3">
                <div className="h-px flex-1 bg-zinc-200 dark:bg-zinc-800" />
                <span className="rounded-full border border-zinc-200 bg-white px-3 py-1 text-[11px] font-semibold text-zinc-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-400">
                  {group.label}
                </span>
                <div className="h-px flex-1 bg-zinc-200 dark:bg-zinc-800" />
              </div>

              {group.items.map((notif, idx) => (
                <NotifCard
                  key={notif.id}
                  notif={notif}
                  isLast={idx === group.items.length - 1}
                />
              ))}
            </div>
          ))}

          {/* Show more */}
          {filtered.length > 20 && (
            <button
              onClick={() => setShowAll(!showAll)}
              className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white py-3 text-sm font-medium text-zinc-600 transition-colors hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800"
            >
              {showAll
                ? <><ChevronUp className="h-4 w-4" /> Show less</>
                : <><ChevronDown className="h-4 w-4" /> Show {filtered.length - 20} more</>}
            </button>
          )}
        </div>
      )}
    </div>
  )
}

function label(filter: NotificationType | 'ALL'): string {
  return filter === 'ALL' ? '' : filter.replace(/_/g, ' ').toLowerCase()
}
