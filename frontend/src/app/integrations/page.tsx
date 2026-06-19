'use client'
import { AppShell } from '@/components/layout/AppShell'
import { IntegrationsPanel } from '@/components/integrations/IntegrationsPanel'

export default function IntegrationsPage() {
  return (
    <AppShell
      title="Integrations"
      subtitle="Connect Discord, WhatsApp, AI parsing, and Alpaca — click a service to configure"
    >
      <IntegrationsPanel />
    </AppShell>
  )
}
