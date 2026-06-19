import { cn } from '@/lib/utils/cn'

export interface StatStripItem {
  label: string
  value: string
  color?: string
  positive?: boolean
}

interface StatStripProps {
  items: StatStripItem[]
  columns?: 4 | 6
}

export function StatStrip({ items, columns = 6 }: StatStripProps) {
  return (
    <div className={cn(
      'mb-4 grid gap-3',
      columns === 4
        ? 'grid-cols-2 lg:grid-cols-4'
        : 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-6',
    )}>
      {items.map(({ label, value, color, positive }) => (
        <div
          key={label}
          className="flex min-h-[4.5rem] flex-col justify-center rounded-lg border border-zinc-200 bg-white px-3 py-2.5 dark:border-zinc-800 dark:bg-zinc-900"
        >
          <p className="text-[10px] uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
            {label}
          </p>
          <p className={cn(
            'mt-0.5 text-lg font-semibold tabular-nums leading-tight',
            color ??
            (positive === true ? 'text-green-600 dark:text-green-400' :
             positive === false ? 'text-red-600 dark:text-red-400' :
             'text-zinc-900 dark:text-zinc-100'),
          )}>
            {value}
          </p>
        </div>
      ))}
    </div>
  )
}
