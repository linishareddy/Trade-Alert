'use client'
import { useQuery } from '@tanstack/react-query'
import { signalsApi } from '@/lib/api/signals'

export function useSignals(params?: { ticker?: string; status?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['signals', params],
    queryFn: () => signalsApi.list(params),
    refetchInterval: 15_000,
    staleTime: 10_000,
  })
}

export function useAllSignals() {
  return useQuery({
    queryKey: ['signals', 'all'],
    queryFn: () => signalsApi.list({ limit: 500 }),
    refetchInterval: 15_000,
    staleTime: 10_000,
  })
}
