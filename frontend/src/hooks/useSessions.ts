import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { fetchChatSessions, fetchChatSession, createChatSession, deleteChatSession } from "@/api/client"

export function useChatSessions(portfolioId: string | undefined) {
  return useQuery({
    queryKey: ["chat-sessions", portfolioId],
    queryFn: () => fetchChatSessions(portfolioId!),
    enabled: !!portfolioId,
  })
}

export function useChatSession(portfolioId: string | undefined, sessionId: string | undefined) {
  return useQuery({
    queryKey: ["chat-session", portfolioId, sessionId],
    queryFn: () => fetchChatSession(portfolioId!, sessionId!),
    enabled: !!portfolioId && !!sessionId,
  })
}

export function useCreateChatSession(portfolioId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => createChatSession(portfolioId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat-sessions", portfolioId] })
    },
  })
}

export function useDeleteChatSession(portfolioId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) => deleteChatSession(portfolioId, sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat-sessions", portfolioId] })
    },
  })
}
