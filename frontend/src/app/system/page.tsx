'use client'
import { AppShell } from '@/components/layout/AppShell'
import { SystemStatus } from '@/components/system/SystemStatus'
import { useHealth, useConfig } from '@/hooks/useHealth'

export default function SystemPage() {
  const { data: health, isLoading: healthLoading, isError } = useHealth()
  const { data: config, isLoading: configLoading } = useConfig()

  const isOnline = health?.status === 'ok' && !isError

  return (
    <AppShell title="System Health & Config" subtitle="Live runtime configuration from .env">
      <SystemStatus
        health={health}
        config={config}
        isOnline={isOnline}
        isError={isError}
        loading={healthLoading || configLoading}
      />
    </AppShell>
  )
}
