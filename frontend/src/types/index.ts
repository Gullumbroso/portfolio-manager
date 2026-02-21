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
