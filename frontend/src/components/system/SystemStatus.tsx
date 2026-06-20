'use client'
import { useState } from 'react'
import type { HealthResponse, ConfigResponse, GroqModel } from '@/types'
import { useUpdateConfig, useResetConfig, useModels } from '@/hooks/useHealth'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Select } from '@/components/ui/Select'
import {
  Server, Database, Zap, Clock, TrendingUp, Shield, Bell, Brain,
  Pencil, Check, X, RotateCcw, Cpu,
} from 'lucide-react'
import { cn } from '@/lib/utils/cn'

// ── Speed badge colours ───────────────────────────────────────────────────────

const SPEED_COLOR: Record<string, string> = {
  fast:   'bg-green-50 text-green-700 dark:bg-green-950/50 dark:text-green-400',
  medium: 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400',
  slow:   'bg-red-50  text-red-700  dark:bg-red-950/50  dark:text-red-400',
}

// ── Toggle switch row (booleans) ──────────────────────────────────────────────

function ToggleRow({
  icon: Icon,
  label,
  configKey,
  value,
  isLoading,
  globalDisabled,
  onToggle,
  onReset,
}: {
  icon: React.ElementType
  label: string
  configKey: string
  value: boolean
  isLoading: boolean
  globalDisabled: boolean
  onToggle: (key: string, val: boolean) => void
  onReset: (key: string) => void
}) {
  return (
    <div className="group flex items-center justify-between py-2.5">
      <div className="flex items-center gap-2.5">
        <Icon className="h-4 w-4 text-zinc-400 dark:text-zinc-500" />
        <span className="text-sm text-zinc-600 dark:text-zinc-400">{label}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <button
          onClick={() => onReset(configKey)}
          disabled={isLoading || globalDisabled}
          title="Reset to .env default"
          className="rounded p-1 text-zinc-300 opacity-0 transition-opacity hover:bg-zinc-100 hover:text-zinc-500 group-hover:opacity-100 disabled:pointer-events-none dark:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-400"
        >
          <RotateCcw className="h-3 w-3" />
        </button>
        <button
          role="switch"
          aria-checked={value}
          aria-label={`Toggle ${label}`}
          disabled={isLoading || globalDisabled}
          onClick={() => onToggle(configKey, !value)}
          className={cn(
            'relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent',
            'transition-colors duration-200 ease-in-out',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2',
            'disabled:cursor-not-allowed disabled:opacity-40',
            value ? 'bg-green-500' : 'bg-zinc-300 dark:bg-zinc-600',
            isLoading && 'opacity-60',
          )}
        >
          <span className={cn(
            'pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow transition-transform duration-200',
            value ? 'translate-x-4' : 'translate-x-0',
          )} />
        </button>
      </div>
    </div>
  )
}

// ── Read-only status row ──────────────────────────────────────────────────────

function StatusRow({ icon: Icon, label, value, status }: {
  icon: React.ElementType
  label: string
  value: string
  status?: 'ok' | 'warn' | 'off' | 'info'
}) {
  const dotColor = {
    ok:   'bg-green-500',
    warn: 'bg-amber-500',
    off:  'bg-red-500',
    info: 'bg-blue-500',
  }[status ?? 'info']

  return (
    <div className="flex items-center justify-between py-2.5">
      <div className="flex items-center gap-2.5">
        <Icon className="h-4 w-4 text-zinc-400 dark:text-zinc-500" />
        <span className="text-sm text-zinc-600 dark:text-zinc-400">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        {status && <span className={cn('h-2 w-2 rounded-full', dotColor)} />}
        <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{value}</span>
      </div>
    </div>
  )
}

// ── Editable numeric row ──────────────────────────────────────────────────────

function EditableRow({
  label,
  configKey,
  display,
  inputDefault,
  toApiValue,
  isLoading,
  globalDisabled,
  onSave,
  onReset,
}: {
  label: string
  configKey: string
  display: string
  inputDefault: string
  toApiValue: (raw: string) => number
  isLoading: boolean
  globalDisabled: boolean
  onSave: (key: string, val: number) => void
  onReset: (key: string) => void
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(inputDefault)

  function handleEdit() {
    setDraft(inputDefault)
    setEditing(true)
  }

  function handleCancel() {
    setEditing(false)
  }

  function handleSave() {
    const parsed = toApiValue(draft)
    if (isNaN(parsed)) return
    onSave(configKey, parsed)
    setEditing(false)
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') handleSave()
    if (e.key === 'Escape') handleCancel()
  }

  return (
    <div className="group flex items-center justify-between py-2 text-sm">
      <span className="text-zinc-500 dark:text-zinc-400">{label}</span>

      {editing ? (
        <div className="flex items-center gap-1">
          <input
            autoFocus
            type="number"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            className={cn(
              'w-20 rounded-md border border-zinc-300 bg-white px-2 py-0.5 text-right text-sm',
              'text-zinc-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500',
              'dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100',
            )}
          />
          <button
            onClick={handleSave}
            className="rounded p-1 text-green-600 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-950/30"
          >
            <Check className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={handleCancel}
            className="rounded p-1 text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-1">
          <button
            onClick={() => onReset(configKey)}
            disabled={isLoading || globalDisabled}
            title="Reset to .env default"
            className="rounded p-1 text-zinc-300 opacity-0 transition-opacity hover:bg-zinc-100 hover:text-zinc-500 group-hover:opacity-100 disabled:pointer-events-none dark:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-400"
          >
            <RotateCcw className="h-3 w-3" />
          </button>
          <span className={cn(
            'font-medium',
            isLoading ? 'text-zinc-400 dark:text-zinc-500' : 'text-zinc-900 dark:text-zinc-100',
          )}>
            {display}
          </span>
          <button
            onClick={handleEdit}
            disabled={isLoading || globalDisabled}
            title={`Edit ${label}`}
            className="rounded p-1 text-zinc-400 opacity-0 transition-opacity hover:bg-zinc-100 hover:text-zinc-600 group-hover:opacity-100 disabled:pointer-events-none dark:hover:bg-zinc-800 dark:hover:text-zinc-300"
          >
            <Pencil className="h-3 w-3" />
          </button>
        </div>
      )}
    </div>
  )
}

// ── Read-only config row ──────────────────────────────────────────────────────

function ConfigRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-2 text-sm">
      <span className="text-zinc-500 dark:text-zinc-400">{label}</span>
      <span className="font-medium text-zinc-900 dark:text-zinc-100">{value}</span>
    </div>
  )
}

// ── Groq model selector ───────────────────────────────────────────────────────

function ModelSelector({
  currentId,
  models,
  isLoading,
  globalDisabled,
  onSave,
  onReset,
}: {
  currentId: string
  models: GroqModel[]
  isLoading: boolean
  globalDisabled: boolean
  onSave: (key: string, val: string) => void
  onReset: (key: string) => void
}) {
  const current = models.find((m) => m.id === currentId)
  const options = models.map((m) => ({
    value: m.id,
    label: m.name,
  }))

  function renderModelMeta(model: GroqModel) {
    return (
      <>
        <span className={cn(
          'rounded px-1.5 py-0.5 text-[10px] font-semibold capitalize',
          SPEED_COLOR[model.speed] ?? SPEED_COLOR.medium,
        )}>
          {model.speed}
        </span>
        <span className="text-[10px] text-zinc-400 dark:text-zinc-500">
          {model.context_k}k
        </span>
      </>
    )
  }

  return (
    <div className="group py-2.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <Cpu className="h-4 w-4 text-zinc-400 dark:text-zinc-500" />
          <span className="text-sm text-zinc-600 dark:text-zinc-400">AI Model</span>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => onReset('ai_model')}
            disabled={isLoading || globalDisabled}
            title="Reset to .env default"
            className="rounded p-1 text-zinc-300 opacity-0 transition-opacity hover:bg-zinc-100 hover:text-zinc-500 group-hover:opacity-100 disabled:pointer-events-none dark:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-400"
          >
            <RotateCcw className="h-3 w-3" />
          </button>
          <Select
            value={currentId}
            options={options}
            align="right"
            disabled={globalDisabled}
            loading={isLoading}
            menuClassName="min-w-[260px]"
            onChange={(id) => onSave('ai_model', id)}
            renderValue={(opt) => {
              const model = models.find((m) => m.id === opt?.value)
              if (!model) return opt?.label ?? 'Select model'
              return (
                <>
                  {model.name}
                  {model.recommended && <span className="text-amber-500"> ★</span>}
                </>
              )
            }}
            renderOption={(opt, selected) => {
              const model = models.find((m) => m.id === opt.value)!
              return (
                <>
                  <Check className={cn('h-3.5 w-3.5 shrink-0', selected ? 'opacity-100' : 'opacity-0')} />
                  <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                    <div className="flex items-center gap-1.5">
                      <span className="font-medium">{model.name}</span>
                      {model.recommended && (
                        <span className="text-[10px] text-amber-500">★ recommended</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5">
                      {renderModelMeta(model)}
                    </div>
                  </div>
                </>
              )
            }}
          />
        </div>
      </div>

      {current && (
        <div className="mt-1.5 flex items-center gap-2 pl-[26px]">
          {renderModelMeta(current)}
          <span className="text-[10px] text-zinc-300 dark:text-zinc-600">·</span>
          <span className="text-[10px] text-zinc-400 dark:text-zinc-500">
            {current.description}
          </span>
        </div>
      )}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

interface SystemStatusProps {
  health: HealthResponse | undefined
  config: ConfigResponse | undefined
  isOnline: boolean
  isError: boolean
  loading: boolean
}

export function SystemStatus({ health, config, isOnline, isError, loading }: SystemStatusProps) {
  const { mutate: updateMutate, isPending: updatePending, variables: updateVars } = useUpdateConfig()
  const { mutate: resetMutate, isPending: resetPending, variables: resetVars } = useResetConfig()
  const { data: models = [] } = useModels()

  const anyPending = updatePending || resetPending
  const updateKey = updatePending ? (updateVars?.key ?? null) : null
  const resetKey  = resetPending  ? (resetVars  ?? null)      : null

  function isRowLoading(key: string) {
    return updateKey === key || resetKey === key
  }

  function isRowDisabled(key: string) {
    return anyPending && !isRowLoading(key)
  }

  function handleUpdate(key: string, value: boolean | number | string) {
    updateMutate({ key, value })
  }

  function handleReset(key: string) {
    resetMutate(key)
  }

  // ── Loading skeleton ────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="animate-pulse rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
            <div className="h-4 w-24 rounded bg-zinc-200 dark:bg-zinc-700" />
            <div className="mt-4 space-y-3">
              {[1, 2, 3].map((j) => (
                <div key={j} className="flex justify-between">
                  <div className="h-3 w-28 rounded bg-zinc-200 dark:bg-zinc-700" />
                  <div className="h-3 w-16 rounded bg-zinc-200 dark:bg-zinc-700" />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  }

  const brokerLabel = config
    ? `${config.broker.toUpperCase()}${config.alpaca_paper ? ' (Paper)' : ' (Live)'}`
    : '—'

  const dbLabel = config
    ? `${config.db_name} @ ${config.db_host}:${config.db_port}`
    : '—'

  return (
    <div className="grid gap-4 sm:grid-cols-2">

      {/* ── API Health (read-only) ── */}
      <Card padding="lg">
        <CardHeader className="mb-3">
          <CardTitle>API Health</CardTitle>
          {isOnline
            ? <Badge variant="green" dot pulse>Online</Badge>
            : <Badge variant="red" dot>Offline</Badge>}
        </CardHeader>
        <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
          <StatusRow icon={Server}   label="Backend Server" value={isOnline ? 'Running' : 'Down'}       status={isOnline ? 'ok' : 'off'} />
          <StatusRow icon={Database} label="PostgreSQL"      value={isOnline ? 'Connected' : 'Unknown'}  status={isOnline ? 'ok' : 'warn'} />
          <StatusRow icon={Zap}      label="Environment"     value={health?.environment ?? '—'}          status="info" />
          <StatusRow icon={Database} label="Database"        value={dbLabel}                             status="ok" />
          {isError && (
            <div className="mt-2 rounded-lg bg-red-50 px-3 py-2 dark:bg-red-950/30">
              <span className="text-xs text-red-600 dark:text-red-400">
                Cannot reach backend at localhost:8000
              </span>
            </div>
          )}
        </div>
      </Card>

      {/* ── Broker & Execution (toggles) ── */}
      <Card padding="lg">
        <CardHeader className="mb-3">
          <CardTitle>Broker & Execution</CardTitle>
          {config
            ? <Badge variant={config.execution_enabled ? 'green' : 'red'}>
                {config.execution_enabled ? 'Active' : 'Disabled'}
              </Badge>
            : <Badge variant="gray">Loading</Badge>}
        </CardHeader>
        <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
          <StatusRow icon={Zap} label="Broker" value={brokerLabel} status="ok" />
          {config ? (
            <>
              <ToggleRow
                icon={Shield} label="Execution"
                configKey="execution_enabled" value={config.execution_enabled}
                isLoading={isRowLoading('execution_enabled')}
                globalDisabled={isRowDisabled('execution_enabled')}
                onToggle={handleUpdate} onReset={handleReset}
              />
              <ToggleRow
                icon={Zap} label="EMA/VWAP Gate"
                configKey="ema_vwap_enabled" value={config.ema_vwap_enabled}
                isLoading={isRowLoading('ema_vwap_enabled')}
                globalDisabled={isRowDisabled('ema_vwap_enabled')}
                onToggle={handleUpdate} onReset={handleReset}
              />
              <ToggleRow
                icon={Clock} label="Market Hours Only"
                configKey="market_hours_only" value={config.market_hours_only}
                isLoading={isRowLoading('market_hours_only')}
                globalDisabled={isRowDisabled('market_hours_only')}
                onToggle={handleUpdate} onReset={handleReset}
              />
              <StatusRow
                icon={Clock} label="Market Hours"
                value={`${config.market_open} – ${config.market_close} ET`}
                status="info"
              />
            </>
          ) : (
            <>
              <StatusRow icon={Shield} label="Execution"         value="—" />
              <StatusRow icon={Zap}    label="EMA/VWAP Gate"     value="—" />
              <StatusRow icon={Clock}  label="Market Hours Only"  value="—" />
            </>
          )}
        </div>
      </Card>

      {/* ── Trade Rules (editable numbers) ── */}
      <Card padding="lg">
        <CardHeader className="mb-3">
          <CardTitle>Trade Rules</CardTitle>
        </CardHeader>
        <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
          {config ? (
            <>
              <EditableRow
                label="Take Profit" configKey="take_profit_pct"
                display={`+${(config.take_profit_pct * 100).toFixed(0)}%`}
                inputDefault={String((config.take_profit_pct * 100).toFixed(0))}
                toApiValue={(raw) => Number(raw) / 100}
                isLoading={isRowLoading('take_profit_pct')}
                globalDisabled={isRowDisabled('take_profit_pct')}
                onSave={handleUpdate} onReset={handleReset}
              />
              <EditableRow
                label="Stop Loss" configKey="stop_loss_pct"
                display={`-${(config.stop_loss_pct * 100).toFixed(0)}%`}
                inputDefault={String((config.stop_loss_pct * 100).toFixed(0))}
                toApiValue={(raw) => Number(raw) / 100}
                isLoading={isRowLoading('stop_loss_pct')}
                globalDisabled={isRowDisabled('stop_loss_pct')}
                onSave={handleUpdate} onReset={handleReset}
              />
              <EditableRow
                label="Position Size" configKey="default_qty"
                display={`${config.default_qty} share${config.default_qty !== 1 ? 's' : ''}`}
                inputDefault={String(config.default_qty)}
                toApiValue={(raw) => Math.round(Number(raw))}
                isLoading={isRowLoading('default_qty')}
                globalDisabled={isRowDisabled('default_qty')}
                onSave={handleUpdate} onReset={handleReset}
              />
            </>
          ) : (
            <>
              <ConfigRow label="Take Profit"   value="—" />
              <ConfigRow label="Stop Loss"     value="—" />
              <ConfigRow label="Position Size" value="—" />
            </>
          )}
          <ConfigRow
            label="Instruments"
            value={config?.supported_contracts
              ? config.supported_contracts.split(',').join(' / ')
              : '—'}
          />
          <ConfigRow
            label="EMA Periods"
            value={config?.ema_periods
              ? config.ema_periods.split(',').map((p: string) => `EMA${p}`).join(', ')
              : '—'}
          />
          <ConfigRow
            label="Data Lookback"
            value={config?.bar_lookback
              ? `${config.bar_lookback} × ${config.bar_minutes}-min bars`
              : '—'}
          />
        </div>
      </Card>

      {/* ── Data & AI (model selector + toggles) ── */}
      <Card padding="lg">
        <CardHeader className="mb-3">
          <CardTitle>Data & AI</CardTitle>
        </CardHeader>
        <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
          <StatusRow
            icon={TrendingUp}
            label="Market Data"
            value={config?.market_data_provider ?? '—'}
            status="ok"
          />

          {config && models.length > 0 ? (
            <ModelSelector
              currentId={config.ai_model}
              models={models}
              isLoading={isRowLoading('ai_model')}
              globalDisabled={isRowDisabled('ai_model')}
              onSave={handleUpdate}
              onReset={handleReset}
            />
          ) : (
            <StatusRow icon={Cpu} label="AI Model" value={config?.ai_model ?? '—'} status="info" />
          )}

          {config ? (
            <>
              <ToggleRow
                icon={Brain} label="AI"
                configKey="ai_parsing_enabled" value={config.ai_parsing_enabled}
                isLoading={isRowLoading('ai_parsing_enabled')}
                globalDisabled={isRowDisabled('ai_parsing_enabled')}
                onToggle={handleUpdate} onReset={handleReset}
              />
              <ToggleRow
                icon={Bell} label="WhatsApp Alerts"
                configKey="whatsapp_enabled" value={config.whatsapp_enabled}
                isLoading={isRowLoading('whatsapp_enabled')}
                globalDisabled={isRowDisabled('whatsapp_enabled')}
                onToggle={handleUpdate} onReset={handleReset}
              />
            </>
          ) : (
            <>
              <StatusRow icon={Brain} label="AI Parsing"     value="—" />
              <StatusRow icon={Bell}  label="WhatsApp Alerts" value="—" />
            </>
          )}
        </div>
      </Card>

    </div>
  )
}
