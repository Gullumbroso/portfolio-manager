import { useEffect, useRef, useState, useMemo } from "react"
import { createChart, type IChartApi, ColorType, LineSeries } from "lightweight-charts"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { usePortfolioPerformance } from "@/hooks/usePortfolio"
import { useIndexHistories, INDEX_TICKERS } from "@/hooks/useIndexComparison"

const PERIODS = ["1M", "3M", "6M", "YTD", "1Y", "ALL"] as const
const PORTFOLIO_COLOR = "#2563eb"

interface Props {
  portfolioId: string
}

function normalizeToPercent(data: { time: string; value: number }[]): { time: string; value: number }[] {
  if (!data.length) return []
  const first = data[0].value
  if (first === 0) return []
  return data.map((d) => ({
    time: d.time,
    value: ((d.value / first) - 1) * 100,
  }))
}

export function IndexComparisonChart({ portfolioId }: Props) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<IChartApi | null>(null)
  const [period, setPeriod] = useState("1M")
  const [enabledIndices, setEnabledIndices] = useState<Set<string>>(new Set(["^GSPC"]))

  const { data: performance, isLoading: perfLoading } = usePortfolioPerformance(portfolioId, period)

  const activeTickers = useMemo(() => Array.from(enabledIndices), [enabledIndices])
  const indexQueries = useIndexHistories(activeTickers, period)

  const toggleIndex = (ticker: string) => {
    setEnabledIndices((prev) => {
      const next = new Set(prev)
      if (next.has(ticker)) {
        next.delete(ticker)
      } else {
        next.add(ticker)
      }
      return next
    })
  }

  const portfolioNormalized = useMemo(() => {
    if (!performance?.length) return []
    // Normalize market_value (holdings performance) — comparable to index returns
    // and avoids distortion from negative cash balances
    return normalizeToPercent(
      performance.map((p) => ({ time: p.date, value: p.market_value }))
    )
  }, [performance])

  const indexDataMap = useMemo(() => {
    const map: Record<string, { time: string; value: number }[]> = {}
    activeTickers.forEach((ticker, i) => {
      const query = indexQueries[i]
      if (query?.data?.length) {
        map[ticker] = normalizeToPercent(
          query.data.map((p) => ({ time: p.date, value: p.close }))
        )
      }
    })
    return map
  }, [activeTickers, indexQueries])

  const hasAnyData = portfolioNormalized.length > 0 || Object.values(indexDataMap).some((d) => d.length > 0)
  const allLoading = perfLoading && indexQueries.every((q) => q.isLoading)

  useEffect(() => {
    if (!chartRef.current || !hasAnyData) return

    if (chartInstance.current) {
      chartInstance.current.remove()
    }

    const chart = createChart(chartRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#999",
      },
      grid: {
        vertLines: { color: "rgba(0,0,0,0.06)" },
        horzLines: { color: "rgba(0,0,0,0.06)" },
      },
      width: chartRef.current.clientWidth,
      height: 350,
      timeScale: { borderColor: "rgba(0,0,0,0.1)" },
      rightPriceScale: {
        borderColor: "rgba(0,0,0,0.1)",
      },
      crosshair: {
        horzLine: { visible: true },
        vertLine: { visible: true },
      },
    })

    // Portfolio line (if data exists)
    if (portfolioNormalized.length) {
      const portfolioSeries = chart.addSeries(LineSeries, {
        color: PORTFOLIO_COLOR,
        lineWidth: 3,
        priceFormat: { type: "custom", formatter: (v: number) => `${v.toFixed(1)}%` },
      })
      portfolioSeries.setData(portfolioNormalized)
    }

    // Index lines
    for (const { ticker, color } of INDEX_TICKERS) {
      const data = indexDataMap[ticker]
      if (!data?.length) continue
      const series = chart.addSeries(LineSeries, {
        color,
        lineWidth: 2,
        priceFormat: { type: "custom", formatter: (v: number) => `${v.toFixed(1)}%` },
      })
      series.setData(data)
    }

    chart.timeScale().fitContent()

    // Clamp visible range to the longest series boundaries
    const allLengths = [
      portfolioNormalized.length,
      ...Object.values(indexDataMap).map((d) => d.length),
    ]
    const maxLength = Math.max(...allLengths)
    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (!range || maxLength === 0) return
      const from = Math.max(range.from, 0)
      const to = Math.min(range.to, maxLength - 1)
      if (from !== range.from || to !== range.to) {
        chart.timeScale().setVisibleLogicalRange({ from, to })
      }
    })

    chartInstance.current = chart

    const handleResize = () => {
      if (chartRef.current) {
        chart.applyOptions({ width: chartRef.current.clientWidth })
      }
    }
    window.addEventListener("resize", handleResize)

    return () => {
      window.removeEventListener("resize", handleResize)
      chart.remove()
      chartInstance.current = null
    }
  }, [portfolioNormalized, indexDataMap, hasAnyData])

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <CardTitle>Portfolio vs Indices</CardTitle>
        <div className="flex gap-1">
          {PERIODS.map((p) => (
            <Button
              key={p}
              variant={period === p ? "default" : "ghost"}
              size="sm"
              onClick={() => setPeriod(p)}
            >
              {p}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {/* Index toggle chips */}
        <div className="flex flex-wrap gap-2 mb-4">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-secondary text-sm font-medium">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: PORTFOLIO_COLOR }} />
            Portfolio
          </div>
          {INDEX_TICKERS.map(({ ticker, label, color }) => (
            <button
              key={ticker}
              onClick={() => toggleIndex(ticker)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm font-medium transition-colors ${
                enabledIndices.has(ticker)
                  ? "bg-secondary text-secondary-foreground"
                  : "bg-muted/50 text-muted-foreground"
              }`}
            >
              <span
                className="h-2.5 w-2.5 rounded-full transition-opacity"
                style={{
                  backgroundColor: color,
                  opacity: enabledIndices.has(ticker) ? 1 : 0.3,
                }}
              />
              {label}
            </button>
          ))}
        </div>

        {allLoading ? (
          <div className="h-[350px] flex items-center justify-center text-muted-foreground">
            Loading comparison...
          </div>
        ) : !hasAnyData ? (
          <div className="h-[350px] flex items-center justify-center text-muted-foreground">
            No data available. Enable an index or wait for portfolio data.
          </div>
        ) : (
          <div ref={chartRef} />
        )}
      </CardContent>
    </Card>
  )
}
