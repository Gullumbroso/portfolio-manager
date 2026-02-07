import { cn, formatCurrency, formatPercent } from "@/lib/utils"

interface ProfitDisplayProps {
  dollars: number
  percent?: number
  size?: "sm" | "md" | "lg"
  showSign?: boolean
}

export function ProfitDisplay({ dollars, percent, size = "md", showSign = true }: ProfitDisplayProps) {
  const isPositive = dollars >= 0
  const colorClass = isPositive ? "text-profit" : "text-loss"

  const sizeClasses = {
    sm: "text-sm",
    md: "text-base",
    lg: "text-xl font-semibold",
  }

  const sign = showSign && dollars > 0 ? "+" : ""

  return (
    <span className={cn(colorClass, sizeClasses[size])}>
      {sign}{formatCurrency(dollars)}
      {percent !== undefined && (
        <span className="ml-1">({formatPercent(percent)})</span>
      )}
    </span>
  )
}
