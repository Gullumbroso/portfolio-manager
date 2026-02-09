import { Select } from "@/components/ui/select"
import type { Portfolio } from "@/types"
import { TrendingUp } from "lucide-react"

const CREATE_NEW_VALUE = "__create_new__"

interface HeaderProps {
  portfolios: Portfolio[]
  selectedId: string | undefined
  onSelect: (id: string) => void
  onCreatePortfolio: () => void
}

export function Header({ portfolios, selectedId, onSelect, onCreatePortfolio }: HeaderProps) {
  function handleChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const value = e.target.value
    if (value === CREATE_NEW_VALUE) {
      e.target.value = selectedId ?? ""
      onCreatePortfolio()
    } else {
      onSelect(value)
    }
  }

  const options = [
    ...portfolios.map((p) => ({ value: p.id, label: p.name })),
    { value: CREATE_NEW_VALUE, label: "+ New Portfolio..." },
  ]

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur">
      <div className="flex h-14 items-center gap-4 px-4 sm:px-6">
        <div className="flex items-center gap-2 font-semibold">
          <TrendingUp className="h-5 w-5" />
          <span className="hidden sm:inline">Portfolio Manager</span>
        </div>
        <div className="ml-auto w-48 sm:w-64">
          <Select
            value={selectedId ?? ""}
            onChange={handleChange}
            options={options}
            placeholder="Select portfolio..."
          />
        </div>
      </div>
    </header>
  )
}
