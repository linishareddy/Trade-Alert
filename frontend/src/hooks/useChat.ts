import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { chatApi, type ChatMessage, type ChatSession } from '@/lib/api/chat'

export function useChatSessions() {
  return useQuery({
    queryKey: ['chatSessions'],
    queryFn: chatApi.listSessions,
  })
}

export function useChatMessages(sessionId: string | null) {
  return useQuery({
    queryKey: ['chatMessages', sessionId],
    queryFn: () => (sessionId ? chatApi.getMessages(sessionId) : Promise.resolve([])),
    enabled: !!sessionId,
  })
}

export function useSendChatMessage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ message, sessionId }: { message: string; sessionId?: string }) =>
      chatApi.send(message, sessionId),
    onSuccess: (data, variables) => {
      // Invalidate both lists
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] })
      queryClient.invalidateQueries({ queryKey: ['chatMessages', data.session_id] })
    },
  })
}

export function useRenameSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, title }: { sessionId: string; title: string }) =>
      chatApi.renameSession(sessionId, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] })
    },
  })
}

export function useDeleteSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sessionId: string) => chatApi.deleteSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] })
    },
  })
}
