import type { RecommendationLeg } from "@/types"
import { cn } from "@/lib/utils"

interface StrategyLegTableProps {
  legs: RecommendationLeg[]
}

export function StrategyLegTable({ legs }: StrategyLegTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b text-muted-foreground">
            <th className="text-left py-1.5 pr-2">Action</th>
            <th className="text-left py-1.5 pr-2">Type</th>
            <th className="text-right py-1.5 pr-2">Strike</th>
            <th className="text-right py-1.5 pr-2">Qty</th>
            <th className="text-right py-1.5 pr-2">Premium</th>
            <th className="text-right py-1.5 pr-2">Bid/Ask</th>
            <th className="text-right py-1.5 pr-2">IV</th>
            <th className="text-right py-1.5 pr-2">Delta</th>
            <th className="text-right py-1.5 pr-2">Gamma</th>
            <th className="text-right py-1.5 pr-2">Theta</th>
            <th className="text-right py-1.5">Vega</th>
          </tr>
        </thead>
        <tbody>
          {legs.map(leg => (
            <tr key={leg.id} className="border-b last:border-0">
              <td className="py-1.5 pr-2">
                <span className={cn(
                  "font-medium uppercase",
                  leg.action === "buy" ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                )}>
                  {leg.action}
                </span>
              </td>
              <td className="py-1.5 pr-2 capitalize">{leg.option_type}</td>
              <td className="text-right py-1.5 pr-2">${leg.strike.toFixed(2)}</td>
              <td className="text-right py-1.5 pr-2">{leg.contracts}</td>
              <td className="text-right py-1.5 pr-2">{leg.premium != null ? `$${leg.premium.toFixed(2)}` : "-"}</td>
              <td className="text-right py-1.5 pr-2">
                {leg.bid != null && leg.ask != null
                  ? `${leg.bid.toFixed(2)}/${leg.ask.toFixed(2)}`
                  : "-"}
              </td>
              <td className="text-right py-1.5 pr-2">
                {leg.implied_volatility != null ? `${(leg.implied_volatility * 100).toFixed(1)}%` : "-"}
              </td>
              <td className="text-right py-1.5 pr-2">{leg.delta?.toFixed(3) ?? "-"}</td>
              <td className="text-right py-1.5 pr-2">{leg.gamma?.toFixed(4) ?? "-"}</td>
              <td className="text-right py-1.5 pr-2">{leg.theta?.toFixed(3) ?? "-"}</td>
              <td className="text-right py-1.5">{leg.vega?.toFixed(3) ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
