import { useEffect, useRef } from "react"
import { createChart, type IChartApi, ColorType, AreaSeries } from "lightweight-charts"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import type { HistoryPoint } from "@/types"

const PERIODS = ["1D", "1W", "1M", "3M", "1Y", "ALL"] as const

interface Props {
  ticker: string
  data: HistoryPoint[] | undefined
  period: string
  onPeriodChange: (period: string) => void
  isLoading: boolean
}

export function StockPriceChart({ ticker, data, period, onPeriodChange, isLoading }: Props) {
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
      height: 400,
      timeScale: { borderColor: "rgba(0,0,0,0.1)" },
      rightPriceScale: { borderColor: "rgba(0,0,0,0.1)" },
    })

    const isUp = data.length > 1 && data[data.length - 1].close >= data[0].close
    const color = isUp ? "#22c55e" : "#ef4444"

    const series = chart.addSeries(AreaSeries, {
      lineColor: color,
      topColor: isUp ? "rgba(34, 197, 94, 0.3)" : "rgba(239, 68, 68, 0.3)",
      bottomColor: isUp ? "rgba(34, 197, 94, 0.02)" : "rgba(239, 68, 68, 0.02)",
      lineWidth: 2,
    })

    series.setData(
      data.map((p) => ({
        time: p.date,
        value: p.close,
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
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{ticker}</CardTitle>
        <div className="flex gap-1">
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
          <div className="h-[400px] flex items-center justify-center text-muted-foreground">
            Loading chart...
          </div>
        ) : !data?.length ? (
          <div className="h-[400px] flex items-center justify-center text-muted-foreground">
            No data available
          </div>
        ) : (
          <div ref={chartRef} />
        )}
      </CardContent>
    </Card>
  )
}
