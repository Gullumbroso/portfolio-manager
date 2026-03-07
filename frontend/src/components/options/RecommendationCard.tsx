import { useState } from "react"
import { ChevronDown, ChevronUp, Check, X, Shield } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { StrategyLegTable } from "./StrategyLegTable"
import { RiskMetricsGrid } from "./RiskMetricsGrid"
import { RiskFlagBadges } from "./RiskFlagBadges"
import { recordDecision } from "@/api/client"
import type { OptionsRecommendation } from "@/types"
import { cn } from "@/lib/utils"

interface RecommendationCardProps {
  recommendation: OptionsRecommendation
  portfolioId: string
}

export function RecommendationCard({ recommendation, portfolioId }: RecommendationCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [decision, setDecision] = useState(recommendation.decision)
  const [deciding, setDeciding] = useState(false)

  const handleDecision = async (choice: "accepted" | "rejected") => {
    setDeciding(true)
    try {
      const result = await recordDecision(portfolioId, recommendation.id, choice)
      setDecision(result)
    } catch {
      // silently fail
    } finally {
      setDeciding(false)
    }
  }

  const riskColor =
    (recommendation.risk_score ?? 0) >= 8 ? "text-red-600 dark:text-red-400" :
    (recommendation.risk_score ?? 0) >= 5 ? "text-yellow-600 dark:text-yellow-400" :
    "text-green-600 dark:text-green-400"

  return (
    <Card className="border-primary/20">
      <CardHeader className="p-4 pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-1">
            <CardTitle className="text-sm flex items-center gap-2">
              {recommendation.strategy_name}
              <Badge variant="outline" className="text-[10px] font-normal">
                {recommendation.ticker}
              </Badge>
              {recommendation.confidence_score != null && (
                <Badge variant="secondary" className="text-[10px]">
                  {recommendation.confidence_score}% confidence
                </Badge>
              )}
            </CardTitle>
            {recommendation.expiration_date && (
              <p className="text-xs text-muted-foreground">
                Exp: {recommendation.expiration_date} ({recommendation.days_to_expiry}d)
                {recommendation.spot_price_at_analysis && ` | Spot: $${recommendation.spot_price_at_analysis.toFixed(2)}`}
              </p>
            )}
          </div>
          <div className={cn("flex items-center gap-1 text-xs font-medium", riskColor)}>
            <Shield className="h-3.5 w-3.5" />
            Risk {recommendation.risk_score}/10
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4 pt-0 space-y-3">
        <RiskFlagBadges recommendation={recommendation} />
        <StrategyLegTable legs={recommendation.legs} />
        <RiskMetricsGrid recommendation={recommendation} />

        {/* Collapsible reasoning */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          {expanded ? "Hide" : "Show"} analysis details
        </button>

        {expanded && (
          <div className="space-y-2 text-xs border-t pt-2">
            {recommendation.strategy_reasoning && (
              <div>
                <p className="font-medium text-muted-foreground">Strategy Reasoning</p>
                <p>{recommendation.strategy_reasoning}</p>
              </div>
            )}
            {recommendation.strike_reasoning && (
              <div>
                <p className="font-medium text-muted-foreground">Strike Selection</p>
                <p>{recommendation.strike_reasoning}</p>
              </div>
            )}
            {recommendation.expiration_reasoning && (
              <div>
                <p className="font-medium text-muted-foreground">Expiration Selection</p>
                <p>{recommendation.expiration_reasoning}</p>
              </div>
            )}
            {recommendation.entry_conditions && (
              <div>
                <p className="font-medium text-muted-foreground">Entry Conditions</p>
                <p>{recommendation.entry_conditions}</p>
              </div>
            )}
            {recommendation.exit_conditions && (
              <div>
                <p className="font-medium text-muted-foreground">Exit Conditions</p>
                <p>{recommendation.exit_conditions}</p>
              </div>
            )}
            {recommendation.adverse_scenario && (
              <div>
                <p className="font-medium text-muted-foreground">Adverse Scenario</p>
                <p>{recommendation.adverse_scenario}</p>
              </div>
            )}
          </div>
        )}

        {/* Accept/Reject */}
        {!decision ? (
          <div className="flex gap-2 pt-1">
            <Button
              size="sm"
              variant="outline"
              className="text-green-600 border-green-200 hover:bg-green-50 dark:hover:bg-green-950"
              onClick={() => handleDecision("accepted")}
              disabled={deciding}
            >
              <Check className="h-3.5 w-3.5 mr-1" />
              Accept
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="text-red-600 border-red-200 hover:bg-red-50 dark:hover:bg-red-950"
              onClick={() => handleDecision("rejected")}
              disabled={deciding}
            >
              <X className="h-3.5 w-3.5 mr-1" />
              Reject
            </Button>
          </div>
        ) : (
          <Badge variant={decision.decision === "accepted" ? "default" : "secondary"}>
            {decision.decision === "accepted" ? "Accepted" : "Rejected"}
          </Badge>
        )}
      </CardContent>
    </Card>
  )
}
