import { useEffect, useRef } from "react"
import { createChart, type IChartApi, ColorType, AreaSeries } from "lightweight-charts"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import type { PortfolioPerformancePoint } from "@/types"

const PERIODS = ["1W", "1M", "3M", "1Y", "ALL"] as const

interface Props {
  data: PortfolioPerformancePoint[] | undefined
  period: string
  onPeriodChange: (period: string) => void
  isLoading: boolean
}

export function PerformanceChart({ data, period, onPeriodChange, isLoading }: Props) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<IChartApi | null>(null)

  useEffect(() => {
    if (!chartRef.current || !data?.length) return

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
      height: chartRef.current.clientWidth < 640 ? 220 : 300,
      handleScroll: false,
      handleScale: false,
      timeScale: { borderColor: "rgba(0,0,0,0.1)" },
      rightPriceScale: { borderColor: "rgba(0,0,0,0.1)" },
    })

    const series = chart.addSeries(AreaSeries, {
      lineColor: "#2563eb",
      topColor: "rgba(37, 99, 235, 0.3)",
      bottomColor: "rgba(37, 99, 235, 0.02)",
      lineWidth: 2,
    })

    series.setData(
      data.map((p) => ({
        time: p.date,
        value: p.market_value,
      }))
    )

    chart.timeScale().fitContent()

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
  }, [data])

  return (
    <Card>
      <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <CardTitle>Performance</CardTitle>
        <div className="flex flex-wrap gap-1">
          {PERIODS.map((p) => (
            <Button
              key={p}
              variant={period === p ? "default" : "ghost"}
              size="sm"
              onClick={() => onPeriodChange(p)}
            >
              {p}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-[220px] sm:h-[300px] flex items-center justify-center text-muted-foreground">
            Loading chart...
          </div>
        ) : !data?.length ? (
          <div className="h-[220px] sm:h-[300px] flex items-center justify-center text-muted-foreground">
            No performance data yet. Data is captured daily.
          </div>
        ) : (
          <div ref={chartRef} className="min-h-[220px] sm:min-h-[300px]" />
        )}
      </CardContent>
    </Card>
  )
}
