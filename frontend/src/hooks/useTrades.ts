'use client'
import { useQuery } from '@tanstack/react-query'
import { tradesApi } from '@/lib/api/trades'

export function useTradeSummary() {
  return useQuery({
    queryKey: ['trades', 'summary'],
    queryFn: () => tradesApi.summary(),
    refetchInterval: 30_000,
    staleTime: 15_000,
  })
}

export function useTrades(params?: { symbol?: string; status?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['trades', params],
    queryFn: () => tradesApi.list(params),
    refetchInterval: 15_000,
    staleTime: 10_000,
  })
}

export function useOpenTrades() {
  return useQuery({
    queryKey: ['trades', { status: 'OPEN' }],
    queryFn: () => tradesApi.list({ status: 'OPEN', limit: 100 }),
    refetchInterval: 15_000,
    staleTime: 10_000,
  })
}

export function useClosedTrades() {
  return useQuery({
    queryKey: ['trades', { status: 'CLOSED' }],
    queryFn: () => tradesApi.list({ status: 'CLOSED', limit: 200 }),
    refetchInterval: 60_000,
    staleTime: 30_000,
  })
}

export function useAllTrades() {
  return useQuery({
    queryKey: ['trades', 'all'],
    queryFn: () => tradesApi.list({ limit: 500 }),
    refetchInterval: 15_000,
    staleTime: 10_000,
  })
}
