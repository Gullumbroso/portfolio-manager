import type { OptionsRecommendation } from "@/types"
import { Badge } from "@/components/ui/badge"

interface RiskFlagBadgesProps {
  recommendation: OptionsRecommendation
}

export function RiskFlagBadges({ recommendation }: RiskFlagBadgesProps) {
  const flags: { label: string; active: boolean; variant: "destructive" | "secondary" }[] = [
    { label: "Unlimited Risk", active: recommendation.has_unlimited_risk, variant: "destructive" },
    { label: "Assignment Risk", active: recommendation.has_assignment_risk, variant: "secondary" },
    { label: "High Gamma", active: recommendation.has_high_gamma, variant: "secondary" },
    { label: "Vol Sensitive", active: recommendation.has_volatility_sensitivity, variant: "secondary" },
  ]

  const activeFlags = flags.filter(f => f.active)
  if (activeFlags.length === 0) return null

  return (
    <div className="flex flex-wrap gap-1.5">
      {activeFlags.map(f => (
        <Badge key={f.label} variant={f.variant} className="text-[10px]">
          {f.label}
        </Badge>
      ))}
    </div>
  )
}
