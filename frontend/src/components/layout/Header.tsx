import { Select } from "@/components/ui/select"
import type { Portfolio } from "@/types"
import { TrendingUp } from "lucide-react"

interface HeaderProps {
  portfolios: Portfolio[]
  selectedId: string | undefined
  onSelect: (id: string) => void
}

export function Header({ portfolios, selectedId, onSelect }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur">
      <div className="flex h-14 items-center gap-4 px-6">
        <div className="flex items-center gap-2 font-semibold">
          <TrendingUp className="h-5 w-5" />
          <span>Portfolio Manager</span>
        </div>
        <div className="ml-auto w-64">
          <Select
            value={selectedId ?? ""}
            onChange={(e) => onSelect(e.target.value)}
            options={portfolios.map((p) => ({ value: p.id, label: p.name }))}
            placeholder="Select portfolio..."
          />
        </div>
      </div>
    </header>
  )
}
