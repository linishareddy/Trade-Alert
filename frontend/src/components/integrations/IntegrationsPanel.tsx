'use client'
import { useState, useRef, useEffect } from 'react'
import {
  CheckCircle2, AlertCircle, Circle, ChevronRight,
  Eye, EyeOff, Save, RotateCcw, RefreshCw, Send,
} from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import { Modal } from '@/components/ui/Modal'
import { IntegrationBrandTile, type BrandId } from '@/components/integrations/IntegrationBrandIcon'
import {
  useIntegrations,
  useUpdateIntegration,
  useResetIntegration,
  useSetGroupEnvDefault,
  useTestWhatsApp,
} from '@/hooks/useIntegrations'
import type { IntegrationGroup, IntegrationField } from '@/types'

// ── Status helpers ────────────────────────────────────────────────────────────

function StatusBadge({ group }: { group: IntegrationGroup }) {
  if (group.status === 'configured') {
    const label = group.use_env_default ? 'Configured' : 'Custom'
    return (
      <span className="flex items-center gap-1 text-xs font-medium text-green-600 dark:text-green-400">
        <CheckCircle2 className="h-3.5 w-3.5" /> {label}
      </span>
    )
  }
  if (group.status === 'partial') {
    return (
      <span className="flex items-center gap-1 text-xs font-medium text-amber-600 dark:text-amber-400">
        <AlertCircle className="h-3.5 w-3.5" /> Partial
      </span>
    )
  }
  return (
    <span className="flex items-center gap-1 text-xs font-medium text-zinc-400">
      <Circle className="h-3.5 w-3.5" /> Not configured
    </span>
  )
}

// ── Toggle switch ─────────────────────────────────────────────────────────────

function Toggle({
  checked,
  onChange,
  disabled,
  label,
}: {
  checked: boolean
  onChange: (v: boolean) => void
  disabled?: boolean
  label: string
}) {
  return (
    <label className={cn('flex cursor-pointer items-center justify-between gap-3', disabled && 'opacity-50')}>
      <span className="text-sm text-zinc-700 dark:text-zinc-300">{label}</span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative h-6 w-11 shrink-0 rounded-full transition-colors',
          checked ? 'bg-blue-600' : 'bg-zinc-300 dark:bg-zinc-600',
          disabled && 'cursor-not-allowed',
        )}
      >
        <span className={cn(
          'absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform',
          checked && 'translate-x-5',
        )} />
      </button>
    </label>
  )
}

// ── Credential row (inside modal) ─────────────────────────────────────────────

function CredentialRow({
  field,
  locked,
  disabled,
  onSave,
  onReset,
}: {
  field: IntegrationField
  locked: boolean
  disabled: boolean
  onSave: (key: string, value: string) => void
  onReset: (key: string) => void
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const [visible, setVisible] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  function startEdit() {
    if (locked) return
    setDraft('')
    setVisible(false)
    setEditing(true)
    setTimeout(() => inputRef.current?.focus(), 50)
  }

  function save() {
    if (!draft.trim()) { setEditing(false); return }
    onSave(field.key, draft.trim())
    setEditing(false)
    setDraft('')
  }

  return (
    <div className="py-3">
      <div className="mb-1 flex items-center gap-2">
        <span className="text-sm font-medium text-zinc-800 dark:text-zinc-200">{field.label}</span>
        {field.is_set && <span className="h-1.5 w-1.5 rounded-full bg-green-500" />}
        {field.is_overridden && (
          <span className="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-medium text-blue-600 dark:bg-blue-950/50 dark:text-blue-400">
            custom
          </span>
        )}
      </div>
      {field.hint && <p className="mb-2 text-xs text-zinc-400 dark:text-zinc-500">{field.hint}</p>}

      {editing ? (
        <div className="flex w-full items-center gap-2">
          <div className="relative min-w-0 flex-1">
            <input
              ref={inputRef}
              type={field.sensitive && !visible ? 'password' : 'text'}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') save()
                if (e.key === 'Escape') setEditing(false)
              }}
              placeholder={field.placeholder}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 pr-8 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
            />
            {field.sensitive && (
              <button type="button" onClick={() => setVisible(!visible)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400">
                {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            )}
          </div>
          <button onClick={save} disabled={!draft.trim() || disabled}
            className="flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-40">
            <Save className="h-3.5 w-3.5" /> Save
          </button>
        </div>
      ) : (
        <div className="flex w-full items-center gap-2">
          <span
            onClick={startEdit}
            className={cn(
              'block min-w-0 flex-1 truncate rounded-lg border px-3 py-2 font-mono text-xs',
              locked
                ? 'cursor-default border-zinc-200 bg-zinc-50 text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900/50'
                : 'cursor-pointer border-dashed border-zinc-300 bg-zinc-50 text-zinc-600 hover:border-blue-400 dark:border-zinc-700 dark:bg-zinc-900 dark:hover:border-blue-500',
            )}
          >
            {field.is_set ? field.value : field.placeholder}
          </span>
          {!locked && !field.is_set && (
            <button onClick={startEdit} className="text-xs text-blue-600 hover:underline dark:text-blue-400">
              Set value
            </button>
          )}
          {!locked && field.is_overridden && (
            <button onClick={() => onReset(field.key)} disabled={disabled} title="Reset to .env"
              className="rounded p-1 text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800">
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      )}
    </div>
  )
}

// ── Integration tile ──────────────────────────────────────────────────────────

function IntegrationTile({ group, onClick }: { group: IntegrationGroup; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'group flex flex-col items-center gap-3 rounded-2xl border border-zinc-200 bg-white p-5',
        'text-center transition-all hover:border-blue-300 hover:shadow-md',
        'dark:border-zinc-800 dark:bg-zinc-950 dark:hover:border-blue-700',
      )}
    >
      <IntegrationBrandTile id={group.id as BrandId} size="lg" className="h-14 w-14 rounded-2xl" />
      <div className="min-w-0 w-full">
        <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{group.name}</p>
        <div className="mt-1.5 flex justify-center">
          <StatusBadge group={group} />
        </div>
      </div>
      <ChevronRight className="h-4 w-4 text-zinc-300 transition-transform group-hover:translate-x-0.5 group-hover:text-blue-500 dark:text-zinc-600" />
    </button>
  )
}

// ── Integration modal ─────────────────────────────────────────────────────────

function IntegrationModal({
  group,
  open,
  onClose,
  isBusy,
  savingKey,
  onSave,
  onReset,
  onSetEnvDefault,
  onTestWhatsApp,
  isTesting,
}: {
  group: IntegrationGroup
  open: boolean
  onClose: () => void
  isBusy: boolean
  savingKey: string | null
  onSave: (key: string, value: string) => void
  onReset: (key: string) => void
  onSetEnvDefault: (useEnv: boolean) => void
  onTestWhatsApp: () => void
  isTesting: boolean
}) {
  const [useEnv, setUseEnv] = useState(group.use_env_default)

  useEffect(() => {
    if (open) setUseEnv(group.use_env_default)
  }, [open, group.use_env_default])

  const fieldsLocked = useEnv

  function handleToggle(checked: boolean) {
    if (checked) {
      onSetEnvDefault(true)
      setUseEnv(true)
    } else {
      setUseEnv(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={group.name}
      subtitle={group.description}
      icon={<IntegrationBrandTile id={group.id as BrandId} className="h-11 w-11 rounded-xl" />}
      footer={
        group.id === 'twilio' ? (
          <button
            onClick={onTestWhatsApp}
            disabled={isTesting || group.status === 'not_configured'}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-zinc-200 py-2.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-40 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
          >
            {isTesting ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            Send test message
          </button>
        ) : undefined
      }
    >
      <div className="space-y-4">
        <div className="rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900/50">
          <Toggle
            checked={useEnv}
            onChange={handleToggle}
            disabled={isBusy}
            label="Use .env defaults"
          />
          <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
            {useEnv
              ? 'Credentials load from your .env file. Turn off to set custom values here.'
              : 'Custom credentials are saved to the database and take effect immediately — no restart needed.'}
          </p>
        </div>

        {!group.env_configured && useEnv && (
          <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-400">
            Some values are missing in your .env file.
          </p>
        )}

        <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
          {group.fields.map((field) => (
            <CredentialRow
              key={field.key}
              field={field}
              locked={fieldsLocked}
              disabled={isBusy && savingKey !== field.key}
              onSave={onSave}
              onReset={onReset}
            />
          ))}
        </div>
      </div>
    </Modal>
  )
}

// ── Main panel ────────────────────────────────────────────────────────────────

export function IntegrationsPanel() {
  const { data, isLoading, isError, refetch } = useIntegrations()
  const { mutate: saveCredential, isPending: isSaving, variables: savingVars } = useUpdateIntegration()
  const { mutate: resetCredential, isPending: isResetting, variables: resetKey } = useResetIntegration()
  const { mutate: setGroupEnvDefault, isPending: isSettingGroup } = useSetGroupEnvDefault()
  const { mutate: testWA, isPending: isTesting } = useTestWhatsApp()

  const [activeId, setActiveId] = useState<string | null>(null)

  const isBusy = isSaving || isResetting || isSettingGroup
  const savingKey = isSaving ? (savingVars?.key ?? null) : isResetting ? (resetKey ?? null) : null
  const activeGroup = data?.groups.find((g) => g.id === activeId) ?? null

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-36 animate-pulse rounded-2xl bg-zinc-100 dark:bg-zinc-800" />
        ))}
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-center">
        <AlertCircle className="h-8 w-8 text-red-400" />
        <p className="text-sm text-zinc-500">Failed to load integrations</p>
        <button onClick={() => refetch()} className="text-xs text-blue-600 hover:underline dark:text-blue-400">
          Retry
        </button>
      </div>
    )
  }

  return (
    <>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {data.groups.map((group) => (
          <IntegrationTile key={group.id} group={group} onClick={() => setActiveId(group.id)} />
        ))}
      </div>

      {activeGroup && (
        <IntegrationModal
          group={activeGroup}
          open={!!activeId}
          onClose={() => setActiveId(null)}
          isBusy={isBusy}
          savingKey={savingKey}
          onSave={(key, value) => saveCredential({ key, value })}
          onReset={(key) => resetCredential(key)}
          onSetEnvDefault={(useEnv) => setGroupEnvDefault({ groupId: activeGroup.id, use_env_default: useEnv })}
          onTestWhatsApp={() => testWA()}
          isTesting={isTesting}
        />
      )}
    </>
  )
}
