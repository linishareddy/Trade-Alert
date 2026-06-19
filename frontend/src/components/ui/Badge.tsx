import { cn } from '@/lib/utils/cn'

type Variant = 'green' | 'red' | 'yellow' | 'blue' | 'gray' | 'purple'

const variants: Record<Variant, string> = {
  green:  'bg-green-50 text-green-700 ring-green-600/20 dark:bg-green-950/50 dark:text-green-400 dark:ring-green-500/20',
  red:    'bg-red-50 text-red-700 ring-red-600/20 dark:bg-red-950/50 dark:text-red-400 dark:ring-red-500/20',
  yellow: 'bg-amber-50 text-amber-700 ring-amber-600/20 dark:bg-amber-950/50 dark:text-amber-400 dark:ring-amber-500/20',
  blue:   'bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-950/50 dark:text-blue-400 dark:ring-blue-500/20',
  gray:   'bg-zinc-100 text-zinc-600 ring-zinc-500/20 dark:bg-zinc-800 dark:text-zinc-400 dark:ring-zinc-500/20',
  purple: 'bg-purple-50 text-purple-700 ring-purple-600/20 dark:bg-purple-950/50 dark:text-purple-400 dark:ring-purple-500/20',
}

interface BadgeProps {
  variant?: Variant
  children: React.ReactNode
  className?: string
  dot?: boolean
  pulse?: boolean
}

export function Badge({ variant = 'gray', children, className, dot, pulse }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset',
        variants[variant],
        className
      )}
    >
      {dot && (
        <span className="relative flex h-1.5 w-1.5">
          <span
            className={cn(
              'absolute inline-flex h-full w-full rounded-full opacity-75',
              pulse && 'animate-ping',
              variant === 'green' && 'bg-green-500 dark:bg-green-400',
              variant === 'red' && 'bg-red-500 dark:bg-red-400',
              variant === 'yellow' && 'bg-amber-500 dark:bg-amber-400',
              variant === 'blue' && 'bg-blue-500 dark:bg-blue-400',
              variant === 'gray' && 'bg-zinc-500 dark:bg-zinc-400',
            )}
          />
          <span
            className={cn(
              'relative inline-flex h-1.5 w-1.5 rounded-full',
              variant === 'green' && 'bg-green-500 dark:bg-green-400',
              variant === 'red' && 'bg-red-500 dark:bg-red-400',
              variant === 'yellow' && 'bg-amber-500 dark:bg-amber-400',
              variant === 'blue' && 'bg-blue-500 dark:bg-blue-400',
              variant === 'gray' && 'bg-zinc-500 dark:bg-zinc-400',
            )}
          />
        </span>
      )}
      {children}
    </span>
  )
}

export function ExitReasonBadge({ reason }: { reason: string | null }) {
  if (!reason) return <Badge variant="gray">—</Badge>
  if (reason === 'TP_HIT') return <Badge variant="green" dot>TP HIT</Badge>
  if (reason === 'SL_HIT') return <Badge variant="red" dot>SL HIT</Badge>
  return <Badge variant="gray">{reason}</Badge>
}

export function StatusBadge({ status }: { status: string }) {
  if (status === 'OPEN') return <Badge variant="yellow" dot pulse>OPEN</Badge>
  if (status === 'CLOSED') return <Badge variant="gray">CLOSED</Badge>
  if (status === 'CANCELLED') return <Badge variant="red">CANCELLED</Badge>
  return <Badge variant="gray">{status}</Badge>
}

export function ActionBadge({ action }: { action: string }) {
  if (action === 'BUY') return <Badge variant="green">{action}</Badge>
  if (action === 'SELL') return <Badge variant="red">{action}</Badge>
  if (action === 'EXIT') return <Badge variant="yellow">{action}</Badge>
  if (action === 'SL_HIT') return <Badge variant="red">{action}</Badge>
  if (action === 'SCALE_IN') return <Badge variant="blue">{action}</Badge>
  if (action === 'SCALE_OUT') return <Badge variant="purple">{action}</Badge>
  return <Badge variant="gray">{action}</Badge>
}

export function ContractBadge({ type }: { type: string }) {
  if (type === 'CALL') return <Badge variant="green">CALL</Badge>
  if (type === 'PUT') return <Badge variant="red">PUT</Badge>
  if (type === 'STOCK') return <Badge variant="blue">STOCK</Badge>
  return <Badge variant="gray">{type}</Badge>
}

export function ValidationBadge({ passed }: { passed: boolean }) {
  if (passed) return <Badge variant="green" dot>PASS</Badge>
  return <Badge variant="red" dot>FAIL</Badge>
}
