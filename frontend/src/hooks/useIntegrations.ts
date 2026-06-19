import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { integrationsApi } from '@/lib/api/integrations'
import type { IntegrationsResponse } from '@/types'

export function useIntegrations() {
  return useQuery({
    queryKey: ['integrations'],
    queryFn: integrationsApi.getAll,
    staleTime: 30_000,
  })
}

export function useUpdateIntegration() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: integrationsApi.update,
    onSuccess: (data) => {
      queryClient.setQueryData<IntegrationsResponse>(['integrations'], data.integrations)
      toast.success('Credential saved')
    },
    onError: () => toast.error('Failed to save credential'),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['integrations'] }),
  })
}

export function useResetIntegration() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (key: string) => integrationsApi.reset(key),
    onSuccess: (data) => {
      queryClient.setQueryData<IntegrationsResponse>(['integrations'], data.integrations)
      toast.success('Reset to .env default')
    },
    onError: () => toast.error('Failed to reset credential'),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['integrations'] }),
  })
}

export function useSetGroupEnvDefault() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ groupId, use_env_default }: { groupId: string; use_env_default: boolean }) =>
      integrationsApi.setGroupEnvDefault(groupId, { use_env_default }),
    onSuccess: (data) => {
      queryClient.setQueryData<IntegrationsResponse>(['integrations'], data.integrations)
      toast.success('Using .env defaults')
    },
    onError: () => toast.error('Failed to update integration group'),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['integrations'] }),
  })
}

export function useTestWhatsApp() {
  return useMutation({
    mutationFn: integrationsApi.testWhatsApp,
    onSuccess: (data) => {
      if (data.ok) toast.success(data.message)
      else toast.error(data.message)
    },
    onError: () => toast.error('Test failed — check network or backend'),
  })
}
