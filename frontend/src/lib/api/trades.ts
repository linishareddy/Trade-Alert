import request from './client'
import type { PaperTrade, TradeListResponse, TradeSummary } from '@/types'

export const tradesApi = {
  list: (params?: { symbol?: string; status?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams()
    if (params?.symbol) qs.set('symbol', params.symbol)
    if (params?.status) qs.set('status', params.status)
    if (params?.limit) qs.set('limit', String(params.limit))
    if (params?.offset) qs.set('offset', String(params.offset))
    const q = qs.toString()
    return request<TradeListResponse>(`/trades${q ? `?${q}` : ''}`)
  },

  summary: () => request<TradeSummary>('/trades/summary'),

  get: (id: string) => request<PaperTrade>(`/trades/${id}`),
}
