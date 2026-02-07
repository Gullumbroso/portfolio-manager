import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useCreateTransaction } from "@/hooks/useTransactions"
import type { TransactionType } from "@/types"
import { cn } from "@/lib/utils"

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  portfolioId: string
}

const TYPES: { value: TransactionType; label: string }[] = [
  { value: "BUY", label: "Buy" },
  { value: "SELL", label: "Sell" },
  { value: "DEPOSIT", label: "Deposit" },
  { value: "WITHDRAWAL", label: "Withdraw" },
]

export function AddTransactionDialog({ open, onOpenChange, portfolioId }: Props) {
  const [type, setType] = useState<TransactionType>("BUY")
  const [ticker, setTicker] = useState("")
  const [shares, setShares] = useState("")
  const [pricePerShare, setPricePerShare] = useState("")
  const [amount, setAmount] = useState("")
  const [note, setNote] = useState("")

  const createTxn = useCreateTransaction(portfolioId)
  const isStock = type === "BUY" || type === "SELL"

  function reset() {
    setType("BUY")
    setTicker("")
    setShares("")
    setPricePerShare("")
    setAmount("")
    setNote("")
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

  const computedAmount = isStock && shares && pricePerShare
    ? (parseFloat(shares) * parseFloat(pricePerShare)).toFixed(2)
    : null

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
              {computedAmount && (
                <div className="text-sm text-muted-foreground">
                  Total: ${computedAmount}
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
