import type { OptionsRecommendation } from "@/types"
import { formatCurrency } from "@/lib/utils"

interface RiskMetricsGridProps {
  recommendation: OptionsRecommendation
}

export function RiskMetricsGrid({ recommendation }: RiskMetricsGridProps) {
  const metrics = [
    {
      label: "Max Profit",
      value: recommendation.max_profit != null ? formatCurrency(recommendation.max_profit) : "Unlimited",
      color: "text-green-600 dark:text-green-400",
    },
    {
      label: "Max Loss",
      value: recommendation.max_loss != null ? formatCurrency(recommendation.max_loss) : "Unlimited",
      color: "text-red-600 dark:text-red-400",
    },
    {
      label: "Breakeven",
      value: recommendation.breakeven_prices.length > 0
        ? recommendation.breakeven_prices.map(p => `$${p.toFixed(2)}`).join(", ")
        : "-",
    },
    {
      label: "Capital Required",
      value: recommendation.capital_required != null ? formatCurrency(recommendation.capital_required) : "-",
    },
    {
      label: "Margin",
      value: recommendation.margin_requirement != null ? formatCurrency(recommendation.margin_requirement) : "-",
    },
    {
      label: "Risk/Reward",
      value: recommendation.risk_reward_ratio != null ? `${recommendation.risk_reward_ratio}:1` : "-",
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
      {metrics.map(m => (
        <div key={m.label} className="space-y-0.5">
          <p className="text-xs text-muted-foreground">{m.label}</p>
          <p className={`text-sm font-medium ${m.color || ""}`}>{m.value}</p>
        </div>
      ))}
    </div>
  )
}
