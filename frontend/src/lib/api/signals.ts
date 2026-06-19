import request from './client'
import type { Signal, SignalListResponse } from '@/types'

export const signalsApi = {
  list: (params?: { ticker?: string; status?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams()
    if (params?.ticker) qs.set('ticker', params.ticker)
    if (params?.status) qs.set('status', params.status)
    if (params?.limit) qs.set('limit', String(params.limit))
    if (params?.offset) qs.set('offset', String(params.offset))
    const q = qs.toString()
    return request<SignalListResponse>(`/signals${q ? `?${q}` : ''}`)
  },

  get: (id: string) => request<Signal>(`/signals/${id}`),
}
