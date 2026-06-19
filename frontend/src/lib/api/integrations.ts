import request from './client'
import type {
  IntegrationsResponse,
  IntegrationUpdateRequest,
  IntegrationUpdateResponse,
  IntegrationGroupUpdateRequest,
  IntegrationGroupUpdateResponse,
} from '@/types'

export const integrationsApi = {
  getAll: () => request<IntegrationsResponse>('/integrations'),

  update: (req: IntegrationUpdateRequest) =>
    request<IntegrationUpdateResponse>('/integrations', {
      method: 'PATCH',
      body: JSON.stringify(req),
    }),

  reset: (key: string) =>
    request<IntegrationUpdateResponse>(`/integrations/${key}`, { method: 'DELETE' }),

  setGroupEnvDefault: (groupId: string, req: IntegrationGroupUpdateRequest) =>
    request<IntegrationGroupUpdateResponse>(`/integrations/groups/${groupId}`, {
      method: 'PATCH',
      body: JSON.stringify(req),
    }),

  testWhatsApp: () =>
    request<{ ok: boolean; message: string }>('/integrations/test/whatsapp', { method: 'POST' }),
}
