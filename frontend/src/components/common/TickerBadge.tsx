import { Badge } from "@/components/ui/badge"
import { useNavigate } from "react-router-dom"

interface TickerBadgeProps {
  ticker: string
  portfolioId: string
}

export function TickerBadge({ ticker, portfolioId }: TickerBadgeProps) {
  const navigate = useNavigate()
  return (
    <Badge
      variant="secondary"
      className="cursor-pointer font-mono hover:bg-secondary/60"
      onClick={() => navigate(`/portfolio/${portfolioId}/stock/${ticker}`)}
    >
      {ticker}
    </Badge>
  )
}
