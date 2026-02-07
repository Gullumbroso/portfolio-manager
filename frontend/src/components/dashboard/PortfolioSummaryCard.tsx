import { Card, CardContent } from "@/components/ui/card"
import { ProfitDisplay } from "@/components/common/ProfitDisplay"
import { Skeleton } from "@/components/ui/skeleton"
import { formatCurrency } from "@/lib/utils"
import type { PortfolioSummary } from "@/types"
import { DollarSign, TrendingUp, Wallet } from "lucide-react"

interface Props {
  summary: PortfolioSummary | undefined
  isLoading: boolean
}

export function PortfolioSummaryCards({ summary, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-8 w-32" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (!summary) return null

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <DollarSign className="h-4 w-4" />
            Total Value
          </div>
          <div className="text-2xl font-bold">{formatCurrency(summary.total_value)}</div>
          <ProfitDisplay
            dollars={summary.profit_dollars}
            percent={summary.profit_percent}
            size="sm"
          />
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <TrendingUp className="h-4 w-4" />
            Market Value
          </div>
          <div className="text-2xl font-bold">{formatCurrency(summary.market_value)}</div>
          <div className="text-sm text-muted-foreground">
            Deposited: {formatCurrency(summary.total_deposits)}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Wallet className="h-4 w-4" />
            Cash Balance
          </div>
          <div className="text-2xl font-bold">{formatCurrency(summary.cash_balance)}</div>
          <div className="text-sm text-muted-foreground">
            Available to invest
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
