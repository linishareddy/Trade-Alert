'use client'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { healthApi } from '@/lib/api/health'
import type { ConfigResponse, ConfigUpdateRequest } from '@/types'

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => healthApi.check(),
    refetchInterval: 30_000,
    staleTime: 15_000,
    retry: 1,
  })
}

export function useConfig() {
  return useQuery({
    queryKey: ['config'],
    queryFn: () => healthApi.config(),
    refetchInterval: 60_000,
    staleTime: 30_000,
    retry: 1,
  })
}

export function useModels() {
  return useQuery({
    queryKey: ['models'],
    queryFn: () => healthApi.models(),
    staleTime: Infinity,  // model list never changes during a session
    retry: 1,
  })
}

export function useUpdateConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (req: ConfigUpdateRequest) => healthApi.updateConfig(req),

    onMutate: async (req) => {
      await queryClient.cancelQueries({ queryKey: ['config'] })
      const snapshot = queryClient.getQueryData<ConfigResponse>(['config'])
      queryClient.setQueryData<ConfigResponse>(['config'], (old) =>
        old ? { ...old, [req.key]: req.value } : old
      )
      return { snapshot }
    },

    onSuccess: (data) => {
      queryClient.setQueryData(['config'], data.config)
      toast.success('Setting saved')
    },

    onError: (_err, _req, ctx) => {
      if (ctx?.snapshot) queryClient.setQueryData(['config'], ctx.snapshot)
      toast.error('Failed to update setting')
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] })
    },
  })
}

export function useResetConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (key: string) => healthApi.resetConfig(key),

    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ['config'] })
      const snapshot = queryClient.getQueryData<ConfigResponse>(['config'])
      return { snapshot }
    },

    onSuccess: (data) => {
      queryClient.setQueryData(['config'], data.config)
      toast.success('Reset to default')
    },

    onError: (_err, _key, ctx) => {
      if (ctx?.snapshot) queryClient.setQueryData(['config'], ctx.snapshot)
      toast.error('Failed to reset setting')
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] })
    },
  })
}
