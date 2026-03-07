import { Loader2, Check } from "lucide-react"

const TOOL_LABELS: Record<string, string> = {
  get_stock_quote: "Fetching stock quote",
  get_stock_history: "Fetching price history",
  get_stock_news: "Fetching news",
  get_portfolio_holdings: "Checking portfolio holdings",
  get_portfolio_summary: "Checking portfolio summary",
  get_options_expirations: "Fetching options expirations",
  get_options_chain: "Fetching options chain",
  generate_options_strategy: "Generating options strategy",
}

interface ToolStatusIndicatorProps {
  tool: string
  status: "running" | "done"
  summary?: string
}

export function ToolStatusIndicator({ tool, status, summary }: ToolStatusIndicatorProps) {
  const label = TOOL_LABELS[tool] || tool

  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground py-1">
      {status === "running" ? (
        <Loader2 className="h-3 w-3 animate-spin" />
      ) : (
        <Check className="h-3 w-3 text-green-500" />
      )}
      <span>{label}{summary ? ` - ${summary}` : "..."}</span>
    </div>
  )
}
