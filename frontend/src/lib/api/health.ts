import request from './client'
import type {
  HealthResponse,
  ConfigResponse,
  ConfigUpdateRequest,
  ConfigUpdateResponse,
  ConfigResetResponse,
  GroqModel,
} from '@/types'

export const healthApi = {
  check: () => request<HealthResponse>('/health'),
  config: () => request<ConfigResponse>('/config'),
  models: () => request<GroqModel[]>('/config/models'),
  updateConfig: (req: ConfigUpdateRequest) =>
    request<ConfigUpdateResponse>('/config', {
      method: 'PATCH',
      body: JSON.stringify(req),
    }),
  resetConfig: (key: string) =>
    request<ConfigResetResponse>(`/config/${key}`, { method: 'DELETE' }),
}
