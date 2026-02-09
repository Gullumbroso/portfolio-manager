import { useState } from "react"
import { useParams } from "react-router-dom"
import { PortfolioSummaryCards } from "@/components/dashboard/PortfolioSummaryCard"
import { HoldingsTable } from "@/components/dashboard/HoldingsTable"
import { PerformanceChart } from "@/components/dashboard/PerformanceChart"
import { AddTransactionDialog } from "@/components/holdings/AddTransactionDialog"
import { usePortfolioSummary, usePortfolioPerformance } from "@/hooks/usePortfolio"
import { useHoldings } from "@/hooks/useHoldings"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"

export function DashboardPage() {
  const { portfolioId } = useParams<{ portfolioId: string }>()
  const [showAddTxn, setShowAddTxn] = useState(false)
  const [perfPeriod, setPerfPeriod] = useState("1M")

  const { data: summary, isLoading: summaryLoading } = usePortfolioSummary(portfolioId)
  const { data: holdings, isLoading: holdingsLoading } = useHoldings(portfolioId)
  const { data: performance, isLoading: perfLoading } = usePortfolioPerformance(portfolioId, perfPeriod)

  if (!portfolioId) return null

  return (
    <div className="space-y-6">
      <PortfolioSummaryCards summary={summary} isLoading={summaryLoading} />
      <PerformanceChart
        data={performance}
        period={perfPeriod}
        onPeriodChange={setPerfPeriod}
        isLoading={perfLoading}
      />
      <HoldingsTable
        holdings={holdings}
        portfolioId={portfolioId}
        isLoading={holdingsLoading}
        onAddTransaction={() => setShowAddTxn(true)}
      />
      <AddTransactionDialog
        open={showAddTxn}
        onOpenChange={setShowAddTxn}
        portfolioId={portfolioId}
      />

      {/* Mobile FAB for adding transactions */}
      <Button
        size="icon"
        className="fixed bottom-6 right-6 z-50 h-14 w-14 rounded-full shadow-lg md:hidden"
        onClick={() => setShowAddTxn(true)}
      >
        <Plus className="h-6 w-6" />
      </Button>
    </div>
  )
}
