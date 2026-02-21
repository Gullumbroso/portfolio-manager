import { useMemo } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { formatCurrency, formatCompactCurrency } from "@/lib/utils"
import type { Holding } from "@/types"

const CHART_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "var(--chart-6)",
  "var(--chart-7)",
  "var(--chart-8)",
  "var(--chart-9)",
  "var(--chart-10)",
]

interface Slice {
  label: string
  value: number
  percent: number
  color: string
}

interface Props {
  holdings: Holding[] | undefined
  cashBalance: number | undefined
  totalValue: number | undefined
  isLoading: boolean
}

export function HoldingsPieChart({ holdings, cashBalance, totalValue, isLoading }: Props) {
  const slices = useMemo(() => {
    if (!holdings) return []

    const raw: { label: string; value: number }[] = []

    for (const h of holdings) {
      if (h.market_value != null && h.market_value > 0) {
        raw.push({ label: h.ticker, value: h.market_value })
      }
    }

    if (cashBalance != null && cashBalance > 0) {
      raw.push({ label: "Cash", value: cashBalance })
    }

    // Use the sum of positive assets as the denominator (not net total_value which can be negative)
    const assetsTotal = raw.reduce((sum, item) => sum + item.value, 0)
    if (assetsTotal === 0) return []

    // Sort by value descending
    raw.sort((a, b) => b.value - a.value)

    // Group holdings < 2% into "Other"
    const significant: typeof raw = []
    let otherValue = 0
    for (const item of raw) {
      if (item.value / assetsTotal < 0.02) {
        otherValue += item.value
      } else {
        significant.push(item)
      }
    }
    if (otherValue > 0) {
      significant.push({ label: "Other", value: otherValue })
    }

    return significant.map((item, i): Slice => ({
      label: item.label,
      value: item.value,
      percent: (item.value / assetsTotal) * 100,
      color: CHART_COLORS[i % CHART_COLORS.length],
    }))
  }, [holdings, cashBalance])

  // SVG donut params
  const size = 200
  const cx = size / 2
  const cy = size / 2
  const radius = 70
  const strokeWidth = 32
  const circumference = 2 * Math.PI * radius

  // Build stroke-dasharray segments
  const segments = useMemo(() => {
    let offset = 0
    return slices.map((slice) => {
      const dashLength = (slice.percent / 100) * circumference
      const gap = circumference - dashLength
      const currentOffset = offset
      offset += dashLength
      return { ...slice, dashLength, gap, offset: currentOffset }
    })
  }, [slices, circumference])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Allocation</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex flex-col items-center gap-4">
            <Skeleton className="h-[200px] w-[200px] rounded-full" />
            <div className="space-y-2 w-full">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-5 w-full" />)}
            </div>
          </div>
        ) : !slices.length ? (
          <div className="h-[200px] flex items-center justify-center text-muted-foreground text-sm">
            No holdings yet
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            {/* Donut Chart */}
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="shrink-0">
              {segments.map((seg) => (
                <circle
                  key={seg.label}
                  cx={cx}
                  cy={cy}
                  r={radius}
                  fill="none"
                  stroke={seg.color}
                  strokeWidth={strokeWidth}
                  strokeDasharray={`${seg.dashLength} ${seg.gap}`}
                  strokeDashoffset={-seg.offset}
                  transform={`rotate(-90 ${cx} ${cy})`}
                  className="transition-all duration-300"
                />
              ))}
              {/* Center label */}
              <text
                x={cx}
                y={cy - 6}
                textAnchor="middle"
                className="fill-foreground text-xs font-medium"
              >
                Total
              </text>
              <text
                x={cx}
                y={cy + 12}
                textAnchor="middle"
                className="fill-foreground text-sm font-bold"
              >
                {formatCompactCurrency(slices.reduce((sum, s) => sum + s.value, 0))}
              </text>
            </svg>

            {/* Legend */}
            <div className="w-full space-y-1.5">
              {slices.map((slice) => (
                <div key={slice.label} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className="h-2.5 w-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: slice.color }}
                    />
                    <span className="truncate font-medium">{slice.label}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 text-muted-foreground">
                    <span className="font-mono">{formatCurrency(slice.value)}</span>
                    <span className="w-12 text-right">{slice.percent.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
