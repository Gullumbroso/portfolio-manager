import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useCreateTransaction } from "@/hooks/useTransactions"
import type { TransactionType } from "@/types"
import { cn, formatCurrency } from "@/lib/utils"

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  portfolioId: string
  cashBalance?: number
}

const TYPES: { value: TransactionType; label: string }[] = [
  { value: "BUY", label: "Buy" },
  { value: "SELL", label: "Sell" },
  { value: "DEPOSIT", label: "Deposit" },
  { value: "WITHDRAWAL", label: "Withdraw" },
]

export function AddTransactionDialog({ open, onOpenChange, portfolioId, cashBalance = 0 }: Props) {
  const [type, setType] = useState<TransactionType>("BUY")
  const [ticker, setTicker] = useState("")
  const [shares, setShares] = useState("")
  const [pricePerShare, setPricePerShare] = useState("")
  const [amount, setAmount] = useState("")
  const [note, setNote] = useState("")
  const [fromCash, setFromCash] = useState("")

  const createTxn = useCreateTransaction(portfolioId)
  const isStock = type === "BUY" || type === "SELL"

  const computedTotal = isStock && shares && pricePerShare
    ? parseFloat(shares) * parseFloat(pricePerShare)
    : null

  // When the buy total or available cash changes, set a smart default for fromCash
  useEffect(() => {
    if (type === "BUY" && computedTotal !== null && cashBalance > 0) {
      const defaultFromCash = Math.min(cashBalance, computedTotal)
      setFromCash(defaultFromCash.toFixed(2))
    } else {
      setFromCash("")
    }
  }, [type, computedTotal, cashBalance])

  const fromCashNum = parseFloat(fromCash) || 0
  const autoFundAmount = computedTotal !== null ? Math.max(0, computedTotal - fromCashNum) : 0

  function reset() {
    setType("BUY")
    setTicker("")
    setShares("")
    setPricePerShare("")
    setAmount("")
    setNote("")
    setFromCash("")
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (isStock) {
      await createTxn.mutateAsync({
        type,
        ticker: ticker.toUpperCase(),
        shares: parseFloat(shares),
        price_per_share: parseFloat(pricePerShare),
        note,
        ...(type === "BUY" && { auto_fund_amount: autoFundAmount }),
      })
    } else {
      await createTxn.mutateAsync({
        type,
        amount: parseFloat(amount),
        note,
      })
    }

    reset()
    onOpenChange(false)
  }

  const maxFromCash = computedTotal !== null ? Math.min(cashBalance, computedTotal) : cashBalance

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Transaction</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          {/* Type selector */}
          <div className="grid grid-cols-4 gap-2">
            {TYPES.map((t) => (
              <Button
                key={t.value}
                type="button"
                variant={type === t.value ? "default" : "outline"}
                size="sm"
                onClick={() => setType(t.value)}
                className={cn(
                  type === t.value && (t.value === "BUY" || t.value === "DEPOSIT")
                    ? "bg-profit text-white hover:bg-profit/90"
                    : type === t.value
                      ? "bg-loss text-white hover:bg-loss/90"
                      : ""
                )}
              >
                {t.label}
              </Button>
            ))}
          </div>

          {isStock ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="ticker">Ticker</Label>
                <Input
                  id="ticker"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value)}
                  placeholder="AAPL"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="shares">Shares</Label>
                  <Input
                    id="shares"
                    type="number"
                    step="any"
                    min="0.0001"
                    value={shares}
                    onChange={(e) => setShares(e.target.value)}
                    placeholder="100"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="price">Price per Share</Label>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={pricePerShare}
                    onChange={(e) => setPricePerShare(e.target.value)}
                    placeholder="182.50"
                    required
                  />
                </div>
              </div>

              {/* Funding breakdown for BUY */}
              {type === "BUY" && computedTotal !== null && (
                <div className="rounded-lg border bg-muted/40 p-3 space-y-3">
                  <div className="flex items-center justify-between text-sm font-medium">
                    <span>Total cost</span>
                    <span>{formatCurrency(computedTotal)}</span>
                  </div>

                  {cashBalance > 0 ? (
                    <>
                      <div className="flex items-center gap-3">
                        <Label htmlFor="fromCash" className="text-sm w-28 shrink-0 text-muted-foreground">
                          From cash
                        </Label>
                        <div className="relative flex-1">
                          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">$</span>
                          <Input
                            id="fromCash"
                            type="number"
                            step="0.01"
                            min="0"
                            max={maxFromCash}
                            value={fromCash}
                            onChange={(e) => setFromCash(e.target.value)}
                            className="pl-7"
                          />
                        </div>
                        <span className="text-xs text-muted-foreground w-20 text-right shrink-0">
                          of {formatCurrency(cashBalance)}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">From external deposit</span>
                        <span className={cn(
                          "font-medium tabular-nums",
                          autoFundAmount > 0 ? "text-blue-600 dark:text-blue-400" : "text-muted-foreground"
                        )}>
                          {formatCurrency(autoFundAmount)}
                        </span>
                      </div>
                      {autoFundAmount > 0 && (
                        <p className="text-xs text-muted-foreground">
                          A deposit of {formatCurrency(autoFundAmount)} will be added automatically.
                        </p>
                      )}
                    </>
                  ) : (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">External deposit (auto)</span>
                      <span className="font-medium text-blue-600 dark:text-blue-400 tabular-nums">
                        {formatCurrency(computedTotal)}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="space-y-2">
              <Label htmlFor="amount">Amount ($)</Label>
              <Input
                id="amount"
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="10000"
                required
              />
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="note">Note (optional)</Label>
            <Input
              id="note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Initial investment"
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => { reset(); onOpenChange(false) }}>
              Cancel
            </Button>
            <Button type="submit" disabled={createTxn.isPending}>
              {createTxn.isPending ? "Adding..." : "Add Transaction"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
