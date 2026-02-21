import { useQueries } from "@tanstack/react-query"
import { fetchHistory } from "@/api/client"

export const INDEX_TICKERS = [
  { ticker: "^GSPC", label: "S&P 500", color: "#ef4444" },
  { ticker: "^IXIC", label: "NASDAQ", color: "#f59e0b" },
  { ticker: "^DJI", label: "DOW", color: "#10b981" },
  { ticker: "^RUT", label: "Russell 2000", color: "#8b5cf6" },
] as const

export function useIndexHistories(tickers: string[], period: string) {
  return useQueries({
    queries: tickers.map((ticker) => ({
      queryKey: ["index-history", ticker, period],
      queryFn: () => fetchHistory(ticker, period),
      staleTime: 5 * 60 * 1000,
    })),
  })
}
