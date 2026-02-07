import { useQuery } from "@tanstack/react-query"
import { fetchHoldings } from "@/api/client"
import { isMarketOpen } from "@/lib/utils"

export function useHoldings(portfolioId: string | undefined) {
  return useQuery({
    queryKey: ["holdings", portfolioId],
    queryFn: () => fetchHoldings(portfolioId!),
    enabled: !!portfolioId,
    refetchInterval: isMarketOpen() ? 60_000 : false,
  })
}
