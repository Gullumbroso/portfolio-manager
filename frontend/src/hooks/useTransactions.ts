import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { fetchTransactions, createTransaction, deleteTransaction } from "@/api/client"
import type { TransactionCreate } from "@/types"

export function useTransactions(portfolioId: string | undefined, limit = 50) {
  return useQuery({
    queryKey: ["transactions", portfolioId, limit],
    queryFn: () => fetchTransactions(portfolioId!, limit),
    enabled: !!portfolioId,
  })
}

export function useCreateTransaction(portfolioId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: TransactionCreate) => createTransaction(portfolioId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["transactions", portfolioId] })
      qc.invalidateQueries({ queryKey: ["holdings", portfolioId] })
      qc.invalidateQueries({ queryKey: ["portfolio-summary", portfolioId] })
    },
  })
}

export function useDeleteTransaction(portfolioId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (transactionId: string) => deleteTransaction(portfolioId, transactionId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["transactions", portfolioId] })
      qc.invalidateQueries({ queryKey: ["holdings", portfolioId] })
      qc.invalidateQueries({ queryKey: ["portfolio-summary", portfolioId] })
    },
  })
}
