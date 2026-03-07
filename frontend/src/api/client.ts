import axios from "axios"
import type {
  Portfolio,
  PortfolioSummary,
  PortfolioPerformancePoint,
  Transaction,
  TransactionCreate,
  Holding,
  Quote,
  HistoryPoint,
  NewsArticle,
  ChatSession,
  ChatSessionDetail,
  OptionsDecision,
} from "@/types"

const API_BASE = import.meta.env.VITE_API_URL || "/api"
const api = axios.create({ baseURL: API_BASE })

// Portfolios
export async function fetchPortfolios(): Promise<Portfolio[]> {
  const { data } = await api.get("/portfolios")
  return data
}

export async function fetchPortfolio(id: string): Promise<Portfolio> {
  const { data } = await api.get(`/portfolios/${id}`)
  return data
}

export async function createPortfolio(payload: { name: string; description?: string }): Promise<Portfolio> {
  const { data } = await api.post("/portfolios", payload)
  return data
}

export async function updatePortfolio(id: string, payload: { name?: string; description?: string }): Promise<Portfolio> {
  const { data } = await api.put(`/portfolios/${id}`, payload)
  return data
}

export async function deletePortfolio(id: string): Promise<void> {
  await api.delete(`/portfolios/${id}`)
}

export async function fetchPortfolioSummary(id: string): Promise<PortfolioSummary> {
  const { data } = await api.get(`/portfolios/${id}/summary`)
  return data
}

export async function fetchPortfolioPerformance(id: string, period = "1M"): Promise<PortfolioPerformancePoint[]> {
  const { data } = await api.get(`/portfolios/${id}/performance`, { params: { period } })
  return data
}

// Transactions
export async function fetchTransactions(portfolioId: string, limit = 50, offset = 0): Promise<Transaction[]> {
  const { data } = await api.get(`/portfolios/${portfolioId}/transactions`, { params: { limit, offset } })
  return data
}

export async function createTransaction(portfolioId: string, payload: TransactionCreate): Promise<Transaction> {
  const { data } = await api.post(`/portfolios/${portfolioId}/transactions`, payload)
  return data
}

export async function deleteTransaction(portfolioId: string, transactionId: string): Promise<void> {
  await api.delete(`/portfolios/${portfolioId}/transactions/${transactionId}`)
}

// Holdings
export async function fetchHoldings(portfolioId: string): Promise<Holding[]> {
  const { data } = await api.get(`/portfolios/${portfolioId}/holdings`)
  return data
}

// Market Data
export async function fetchQuote(ticker: string): Promise<Quote> {
  const { data } = await api.get(`/market/quote/${ticker}`)
  return data
}

export async function fetchBatchQuotes(tickers: string[]): Promise<Record<string, Quote>> {
  const { data } = await api.get("/market/batch-quotes", { params: { tickers: tickers.join(",") } })
  return data
}

export async function fetchHistory(ticker: string, period = "1M"): Promise<HistoryPoint[]> {
  const { data } = await api.get(`/market/history/${ticker}`, { params: { period } })
  return data
}

export async function fetchNews(ticker: string): Promise<NewsArticle[]> {
  const { data } = await api.get(`/market/news/${ticker}`)
  return data
}

// Chat / AI Consultant
export async function createChatSession(portfolioId: string): Promise<ChatSession> {
  const { data } = await api.post(`/portfolios/${portfolioId}/chat/sessions`)
  return data
}

export async function fetchChatSessions(portfolioId: string): Promise<ChatSession[]> {
  const { data } = await api.get(`/portfolios/${portfolioId}/chat/sessions`)
  return data
}

export async function fetchChatSession(portfolioId: string, sessionId: string): Promise<ChatSessionDetail> {
  const { data } = await api.get(`/portfolios/${portfolioId}/chat/sessions/${sessionId}`)
  return data
}

export async function deleteChatSession(portfolioId: string, sessionId: string): Promise<void> {
  await api.delete(`/portfolios/${portfolioId}/chat/sessions/${sessionId}`)
}

export function getChatMessageUrl(portfolioId: string, sessionId: string): string {
  const baseUrl = api.defaults.baseURL || "/api"
  return `${baseUrl}/portfolios/${portfolioId}/chat/sessions/${sessionId}/messages`
}

export async function recordDecision(
  portfolioId: string,
  recommendationId: string,
  decision: string,
  notes: string = ""
): Promise<OptionsDecision> {
  const { data } = await api.post(
    `/portfolios/${portfolioId}/chat/recommendations/${recommendationId}/decision`,
    { decision, notes }
  )
  return data
}
