import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { ProfitDisplay } from "@/components/common/ProfitDisplay"
import { formatCurrency, formatNumber } from "@/lib/utils"
import type { Holding } from "@/types"

interface Props {
  holding: Holding | undefined
}

export function PositionDetails({ holding }: Props) {
  if (!holding) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Position</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No position in this stock.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Your Position</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Shares</span>
          <span className="font-mono">{formatNumber(holding.total_shares, holding.total_shares % 1 === 0 ? 0 : 4)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Avg Cost</span>
          <span className="font-mono">{formatCurrency(holding.avg_cost_per_share)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Cost Basis</span>
          <span className="font-mono">{formatCurrency(holding.total_cost_basis)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Market Value</span>
          <span className="font-mono">
            {holding.market_value != null ? formatCurrency(holding.market_value) : "—"}
          </span>
        </div>
        <div className="flex justify-between border-t pt-3">
          <span className="text-muted-foreground">Total P/L</span>
          {holding.total_gain_dollars != null ? (
            <ProfitDisplay
              dollars={holding.total_gain_dollars}
              percent={holding.total_gain_percent ?? undefined}
              size="sm"
            />
          ) : (
            <span>—</span>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
