import { formatDistanceToNow, format, differenceInMinutes, differenceInHours } from 'date-fns'

export function fmtCurrency(value: number | null | undefined, digits = 2): string {
  if (value == null) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)
}

export function fmtPercent(value: number | null | undefined, digits = 2): string {
  if (value == null) return '—'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(digits)}%`
}

export function fmtPrice(value: number | null | undefined): string {
  if (value == null) return '—'
  return `$${value.toFixed(2)}`
}

export function fmtNumber(value: number | null | undefined): string {
  if (value == null) return '—'
  return new Intl.NumberFormat('en-US').format(value)
}

export function fmtTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '—'
  try {
    return format(new Date(dateStr), 'h:mm a')
  } catch {
    return '—'
  }
}

export function fmtTimeAgo(dateStr: string | null | undefined): string {
  if (!dateStr) return '—'
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true })
  } catch {
    return '—'
  }
}

export function fmtDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—'
  try {
    return format(new Date(dateStr), 'MMM d, yyyy HH:mm')
  } catch {
    return '—'
  }
}

export function fmtDuration(start: string | null, end: string | null): string {
  if (!start) return '—'
  const endDate = end ? new Date(end) : new Date()
  const startDate = new Date(start)
  const mins = differenceInMinutes(endDate, startDate)
  if (mins < 60) return `${mins}m`
  const hours = differenceInHours(endDate, startDate)
  if (hours < 24) return `${hours}h ${mins % 60}m`
  return `${Math.floor(hours / 24)}d ${hours % 24}h`
}
