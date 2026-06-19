'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  TrendingUp,
  History,
  Radio,
  Bell,
  Settings,
  Plug,
  Zap,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import { APP_NAME } from '@/lib/brand'
import { useState } from 'react'
import { useHealth } from '@/hooks/useHealth'
import { useAuth } from '@/providers/AuthProvider'

const navGroups = [
  {
    label: 'OVERVIEW',
    items: [
      { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    ],
  },
  {
    label: 'TRADING',
    items: [
      { href: '/positions', label: 'Active Positions', icon: TrendingUp },
      { href: '/history', label: 'Trade History', icon: History },
      { href: '/signals', label: 'Signal Feed', icon: Radio },
    ],
  },
  {
    label: 'ANALYTICS',
    items: [
      { href: '/notifications', label: 'Notifications', icon: Bell },
    ],
  },
  {
    label: 'SYSTEM',
    items: [
      { href: '/integrations', label: 'Integrations', icon: Plug },
      { href: '/system', label: 'Health & Config', icon: Settings },
    ],
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)
  const { data: health, isError } = useHealth()
  const { user, logout } = useAuth()

  const isOnline = health?.status === 'ok' && !isError

  return (
    <aside
      className={cn(
        'flex h-screen flex-col border-r border-zinc-200 bg-white transition-all duration-200 dark:border-zinc-800 dark:bg-zinc-950',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Logo + collapse */}
      <div className={cn(
        'flex shrink-0 items-center border-b border-zinc-200 dark:border-zinc-800',
        collapsed ? 'flex-col justify-center gap-1 py-3' : 'h-16 gap-2.5 px-3',
      )}>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600 shadow-sm">
          <Zap className="h-4 w-4 text-white" />
        </div>
        {!collapsed && (
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-zinc-900 dark:text-zinc-100">
              {APP_NAME}
            </p>
            <div className="flex items-center gap-1">
              <span className={cn(
                'h-1.5 w-1.5 rounded-full',
                isOnline ? 'bg-green-500' : 'bg-red-500'
              )} />
              <span className="text-[10px] text-zinc-500 dark:text-zinc-400">
                {isOnline ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className={cn(
            'flex shrink-0 items-center justify-center rounded-md p-1.5',
            'text-zinc-400 transition-colors hover:bg-zinc-100 hover:text-zinc-600',
            'dark:text-zinc-500 dark:hover:bg-zinc-800 dark:hover:text-zinc-300',
            collapsed && 'mt-0',
          )}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4">
        {navGroups.map((group) => (
          <div key={group.label} className="mb-4">
            {!collapsed && (
              <p className="mb-1 px-4 text-[10px] font-semibold uppercase tracking-widest text-zinc-400 dark:text-zinc-600">
                {group.label}
              </p>
            )}
            <ul className="space-y-0.5 px-2">
              {group.items.map(({ href, label, icon: Icon }) => {
                const active = pathname === href || pathname.startsWith(href + '/')
                return (
                  <li key={href}>
                    <Link
                      href={href}
                      title={collapsed ? label : undefined}
                      className={cn(
                        'flex items-center gap-2.5 rounded-lg px-2 py-2 text-sm font-medium transition-colors',
                        active
                          ? 'border-l-2 border-blue-600 bg-blue-50 text-blue-700 dark:border-blue-500 dark:bg-blue-950/50 dark:text-blue-400'
                          : 'text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800/50 dark:hover:text-zinc-100',
                        collapsed && 'justify-center px-0'
                      )}
                    >
                      <Icon className={cn('h-4 w-4 shrink-0', active && 'text-blue-600 dark:text-blue-400')} />
                      {!collapsed && <span className="truncate">{label}</span>}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* User */}
      <div className="shrink-0 border-t border-zinc-200 p-2 dark:border-zinc-800">
        {user && (
          <div className={cn(
            'flex items-center gap-2 rounded-lg px-2 py-2',
            collapsed && 'justify-center px-0',
          )}>
            <button
              type="button"
              onClick={collapsed ? logout : undefined}
              title={collapsed ? 'Sign out' : undefined}
              className={cn(
                'flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700',
                'dark:bg-blue-950/50 dark:text-blue-400',
                collapsed && 'cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-900/50',
              )}
            >
              {user.username.charAt(0).toUpperCase()}
            </button>
            {!collapsed && (
              <>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-medium text-zinc-900 dark:text-zinc-100">{user.username}</p>
                  <p className="truncate text-[10px] text-zinc-500 dark:text-zinc-400">{user.role}</p>
                </div>
                <button
                  onClick={logout}
                  title="Sign out"
                  className="rounded p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-300"
                >
                  <LogOut className="h-3.5 w-3.5" />
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </aside>
  )
}
