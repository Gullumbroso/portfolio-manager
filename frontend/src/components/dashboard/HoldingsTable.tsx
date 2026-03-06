import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { TickerBadge } from "@/components/common/TickerBadge"
import { ProfitDisplay } from "@/components/common/ProfitDisplay"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils"
import type { Holding } from "@/types"
import { Plus } from "lucide-react"

interface Props {
  holdings: Holding[] | undefined
  portfolioId: string
  isLoading: boolean
  onAddTransaction: () => void
}

export function HoldingsTable({ holdings, portfolioId, isLoading, onAddTransaction }: Props) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Holdings</CardTitle>
        <Button size="sm" onClick={onAddTransaction}>
          <Plus className="h-4 w-4 mr-1" />
          Add Trade
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : !holdings?.length ? (
          <div className="text-center py-8 text-muted-foreground">
            <p>No holdings yet.</p>
            <p className="text-sm mt-1">Add a deposit and buy some stocks to get started.</p>
          </div>
        ) : (
          <>
            {/* Desktop table */}
            <div className="hidden md:block">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Ticker</TableHead>
                    <TableHead className="text-right">Shares</TableHead>
                    <TableHead className="text-right">Price</TableHead>
                    <TableHead className="text-right">Day Change</TableHead>
                    <TableHead className="text-right">Value</TableHead>
                    <TableHead className="text-right">P/L</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {holdings.map((h) => (
                    <TableRow key={h.ticker}>
                      <TableCell>
                        <TickerBadge ticker={h.ticker} portfolioId={portfolioId} />
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {formatNumber(h.total_shares, h.total_shares % 1 === 0 ? 0 : 2)}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {h.current_price != null ? formatCurrency(h.current_price) : "—"}
                      </TableCell>
                      <TableCell className="text-right">
                        {h.day_change_percent != null ? (
                          <span className={h.day_change_percent >= 0 ? "text-profit" : "text-loss"}>
                            {formatPercent(h.day_change_percent)}
                          </span>
                        ) : "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {h.market_value != null ? formatCurrency(h.market_value) : "—"}
                      </TableCell>
                      <TableCell className="text-right">
                        {h.total_gain_dollars != null ? (
                          <ProfitDisplay
                            dollars={h.total_gain_dollars}
                            percent={h.total_gain_percent ?? undefined}
                            size="sm"
                          />
                        ) : "—"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Mobile card list */}
            <div className="md:hidden space-y-3">
              {holdings.map((h) => (
                <div key={h.ticker} className="rounded-lg border p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <TickerBadge ticker={h.ticker} portfolioId={portfolioId} />
                    <span className="font-mono font-medium">
                      {h.market_value != null ? formatCurrency(h.market_value) : "—"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>
                      {formatNumber(h.total_shares, h.total_shares % 1 === 0 ? 0 : 2)} shares @ {h.current_price != null ? formatCurrency(h.current_price) : "—"}
                    </span>
                    {h.day_change_percent != null ? (
                      <span className={h.day_change_percent >= 0 ? "text-profit" : "text-loss"}>
                        {formatPercent(h.day_change_percent)}
                      </span>
                    ) : null}
                  </div>
                  {h.total_gain_dollars != null && (
                    <div className="flex justify-end">
                      <ProfitDisplay
                        dollars={h.total_gain_dollars}
                        percent={h.total_gain_percent ?? undefined}
                        size="sm"
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
