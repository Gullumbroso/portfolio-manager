import { useQuery } from "@tanstack/react-query"
import { fetchQuote, fetchHistory, fetchNews } from "@/api/client"

export function useQuote(ticker: string | undefined) {
  return useQuery({
    queryKey: ["quote", ticker],
    queryFn: () => fetchQuote(ticker!),
    enabled: !!ticker,
  })
}

export function useHistory(ticker: string | undefined, period = "1M") {
  return useQuery({
    queryKey: ["history", ticker, period],
    queryFn: () => fetchHistory(ticker!, period),
    enabled: !!ticker,
  })
}

export function useNews(ticker: string | undefined) {
  return useQuery({
    queryKey: ["news", ticker],
    queryFn: () => fetchNews(ticker!),
    enabled: !!ticker,
    staleTime: 5 * 60 * 1000,
  })
}
