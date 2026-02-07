import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  fetchPortfolios,
  fetchPortfolio,
  createPortfolio,
  updatePortfolio,
  deletePortfolio,
  fetchPortfolioSummary,
  fetchPortfolioPerformance,
} from "@/api/client"
import { isMarketOpen } from "@/lib/utils"

export function usePortfolios() {
  return useQuery({
    queryKey: ["portfolios"],
    queryFn: fetchPortfolios,
  })
}

export function usePortfolio(id: string | undefined) {
  return useQuery({
    queryKey: ["portfolio", id],
    queryFn: () => fetchPortfolio(id!),
    enabled: !!id,
  })
}

export function usePortfolioSummary(id: string | undefined) {
  return useQuery({
    queryKey: ["portfolio-summary", id],
    queryFn: () => fetchPortfolioSummary(id!),
    enabled: !!id,
    refetchInterval: isMarketOpen() ? 60_000 : false,
  })
}

export function usePortfolioPerformance(id: string | undefined, period = "1M") {
  return useQuery({
    queryKey: ["portfolio-performance", id, period],
    queryFn: () => fetchPortfolioPerformance(id!, period),
    enabled: !!id,
  })
}

export function useCreatePortfolio() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createPortfolio,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["portfolios"] }),
  })
}

export function useUpdatePortfolio() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; name?: string; description?: string }) =>
      updatePortfolio(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["portfolios"] })
      qc.invalidateQueries({ queryKey: ["portfolio"] })
    },
  })
}

export function useDeletePortfolio() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deletePortfolio,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["portfolios"] }),
  })
}
