import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { StockPriceChart } from "@/components/holdings/StockPriceChart"
import { PositionDetails } from "@/components/holdings/PositionDetails"
import { NewsFeed } from "@/components/news/NewsFeed"
import { useHistory, useQuote, useNews } from "@/hooks/useMarketData"
import { useHoldings } from "@/hooks/useHoldings"
import { Button } from "@/components/ui/button"
import { formatCurrency, formatPercent } from "@/lib/utils"
import { ArrowLeft } from "lucide-react"

export function StockDetailPage() {
  const { portfolioId, ticker } = useParams<{ portfolioId: string; ticker: string }>()
  const navigate = useNavigate()
  const [period, setPeriod] = useState("1M")

  const { data: quote } = useQuote(ticker)
  const { data: history, isLoading: histLoading } = useHistory(ticker, period)
  const { data: holdings } = useHoldings(portfolioId)
  const { data: news, isLoading: newsLoading } = useNews(ticker)

  const holding = holdings?.find((h) => h.ticker === ticker)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(`/portfolio/${portfolioId}`)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{ticker}</h1>
          {quote && (
            <div className="flex items-center gap-3">
              <span className="text-xl font-mono">{formatCurrency(quote.price)}</span>
              <span className={quote.change_percent >= 0 ? "text-profit" : "text-loss"}>
                {quote.change_amount >= 0 ? "+" : ""}{formatCurrency(quote.change_amount)} ({formatPercent(quote.change_percent)})
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Chart */}
      <StockPriceChart
        ticker={ticker!}
        data={history}
        period={period}
        onPeriodChange={setPeriod}
        isLoading={histLoading}
      />

      {/* Position + News */}
      <div className="grid gap-6 lg:grid-cols-2">
        <PositionDetails holding={holding} />
        <NewsFeed articles={news} isLoading={newsLoading} />
      </div>
    </div>
  )
}
