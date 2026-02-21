import { useState } from "react"
import { useParams } from "react-router-dom"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { AddTransactionDialog } from "@/components/holdings/AddTransactionDialog"
import { useTransactions, useDeleteTransaction } from "@/hooks/useTransactions"
import { usePortfolioSummary } from "@/hooks/usePortfolio"
import { formatCurrency } from "@/lib/utils"
import { LoadingPage } from "@/components/common/LoadingSpinner"
import { Plus, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"

function isAutoTransaction(note: string) {
  return note.startsWith("[auto:buy:")
}

function cleanNote(note: string) {
  // Strip the [auto:buy:{uuid}] prefix, show the human-readable part
  return note.replace(/^\[auto:buy:[^\]]+\] /, "")
}

const TYPE_COLORS: Record<string, string> = {
  BUY: "bg-profit/10 text-profit border-profit/20",
  SELL: "bg-loss/10 text-loss border-loss/20",
  DEPOSIT: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  WITHDRAWAL: "bg-orange-500/10 text-orange-600 border-orange-500/20",
}

export function TransactionHistoryPage() {
  const { portfolioId } = useParams<{ portfolioId: string }>()
  const [showAddTxn, setShowAddTxn] = useState(false)
  const { data: transactions, isLoading } = useTransactions(portfolioId, 200)
  const { data: summary } = usePortfolioSummary(portfolioId)
  const deleteTxn = useDeleteTransaction(portfolioId!)

  if (!portfolioId) return null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Transaction History</h1>
        <Button size="sm" onClick={() => setShowAddTxn(true)}>
          <Plus className="h-4 w-4 mr-1" />
          Add Transaction
        </Button>
      </div>

      <Card>
        <CardContent className="pt-6">
          {isLoading ? (
            <LoadingPage />
          ) : !transactions?.length ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No transactions yet.</p>
              <p className="text-sm mt-1">Start by making a deposit.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Ticker</TableHead>
                  <TableHead className="text-right">Shares</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Note</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactions.map((txn) => {
                  const auto = isAutoTransaction(txn.note)
                  return (
                    <TableRow key={txn.id} className={cn(auto && "opacity-60")}>
                      <TableCell className="text-sm">
                        {new Date(txn.transacted_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5">
                          <Badge variant="outline" className={cn("text-xs", TYPE_COLORS[txn.type])}>
                            {txn.type}
                          </Badge>
                          {auto && (
                            <Badge variant="outline" className="text-xs text-muted-foreground border-muted">
                              Auto
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="font-mono font-medium">
                        {txn.ticker ?? "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {txn.shares != null ? txn.shares : "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {txn.price_per_share != null ? formatCurrency(txn.price_per_share) : "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono font-medium">
                        {formatCurrency(txn.amount)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground max-w-[200px] truncate">
                        {auto ? cleanNote(txn.note) : (txn.note || "—")}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-destructive"
                          onClick={() => {
                            if (confirm("Delete this transaction? This will affect your portfolio balance.")) {
                              deleteTxn.mutate(txn.id)
                            }
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <AddTransactionDialog
        open={showAddTxn}
        onOpenChange={setShowAddTxn}
        portfolioId={portfolioId}
        cashBalance={summary?.cash_balance}
      />
    </div>
  )
}
