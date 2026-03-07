export interface Portfolio {
  id: string
  name: string
  description: string
  created_at: string
  updated_at: string
}

export interface PortfolioSummary {
  id: string
  name: string
  total_value: number
  market_value: number
  cash_balance: number
  total_deposits: number
  profit_dollars: number
  profit_percent: number
}

export interface PortfolioPerformancePoint {
  date: string
  total_value: number
  cash_balance: number
  market_value: number
  total_deposits: number
  profit: number
}

export type TransactionType = "BUY" | "SELL" | "DEPOSIT" | "WITHDRAWAL"

export interface Transaction {
  id: string
  portfolio_id: string
  type: TransactionType
  ticker: string | null
  shares: number | null
  price_per_share: number | null
  amount: number
  note: string
  transacted_at: string
  created_at: string
}

export interface TransactionCreate {
  type: TransactionType
  ticker?: string
  shares?: number
  price_per_share?: number
  amount?: number
  note?: string
  transacted_at?: string
  auto_fund_amount?: number
}

export interface Holding {
  portfolio_id: string
  ticker: string
  total_shares: number
  total_cost_basis: number
  avg_cost_per_share: number
  current_price: number | null
  market_value: number | null
  day_change_amount: number | null
  day_change_percent: number | null
  total_gain_dollars: number | null
  total_gain_percent: number | null
}

export interface Quote {
  ticker: string
  price: number
  change_amount: number
  change_percent: number
  name?: string
}

export interface HistoryPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface NewsArticle {
  headline: string
  summary: string
  source: string
  url: string
  image: string | null
  datetime: number
}

// --- Chat / AI Consultant ---

export interface ChatSession {
  id: string
  portfolio_id: string
  title: string | null
  status: string
  created_at: string
  updated_at: string
  last_message_preview: string | null
}

export interface ChatMessage {
  id: string
  session_id: string
  role: "user" | "assistant"
  content: string
  has_recommendation: boolean
  created_at: string
  recommendations: OptionsRecommendation[]
}

export interface ChatSessionDetail {
  id: string
  portfolio_id: string
  title: string | null
  status: string
  created_at: string
  updated_at: string
  messages: ChatMessage[]
}

export interface RecommendationLeg {
  id: string
  leg_order: number
  action: "buy" | "sell"
  option_type: "call" | "put"
  strike: number
  contracts: number
  premium: number | null
  bid: number | null
  ask: number | null
  implied_volatility: number | null
  open_interest: number | null
  volume: number | null
  delta: number | null
  gamma: number | null
  theta: number | null
  vega: number | null
}

export interface OptionsRecommendation {
  id: string
  message_id: string
  session_id: string
  ticker: string
  strategy_type: string
  strategy_name: string
  confidence_score: number | null
  strategy_reasoning: string | null
  strike_reasoning: string | null
  expiration_reasoning: string | null
  entry_conditions: string | null
  exit_conditions: string | null
  adverse_scenario: string | null
  max_profit: number | null
  max_loss: number | null
  breakeven_prices: number[]
  capital_required: number | null
  margin_requirement: number | null
  risk_reward_ratio: number | null
  risk_score: number | null
  has_unlimited_risk: boolean
  has_assignment_risk: boolean
  has_high_gamma: boolean
  has_volatility_sensitivity: boolean
  spot_price_at_analysis: number | null
  expiration_date: string | null
  days_to_expiry: number | null
  legs: RecommendationLeg[]
  decision: OptionsDecision | null
  created_at: string
}

export interface OptionsDecision {
  id: string
  recommendation_id: string
  decision: "accepted" | "rejected"
  notes: string
  created_at: string
}
