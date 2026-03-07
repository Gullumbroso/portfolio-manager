import { BrowserRouter, Routes, Route } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AppLayout } from "@/components/layout/AppLayout"
import { DashboardPage } from "@/pages/DashboardPage"
import { PortfolioListPage } from "@/pages/PortfolioListPage"
import { TransactionHistoryPage } from "@/pages/TransactionHistoryPage"
import { StockDetailPage } from "@/pages/StockDetailPage"
import { ChatListPage } from "@/pages/ChatListPage"
import { ChatPage } from "@/pages/ChatPage"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<PortfolioListPage />} />
            <Route path="/portfolio/:portfolioId" element={<DashboardPage />} />
            <Route path="/portfolio/:portfolioId/transactions" element={<TransactionHistoryPage />} />
            <Route path="/portfolio/:portfolioId/stock/:ticker" element={<StockDetailPage />} />
            <Route path="/portfolio/:portfolioId/chat" element={<ChatListPage />} />
            <Route path="/portfolio/:portfolioId/chat/:sessionId" element={<ChatPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
