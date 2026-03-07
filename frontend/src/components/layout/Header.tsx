import { Select } from "@/components/ui/select"
import type { Portfolio } from "@/types"
import { Pencil, Trash2, Menu } from "lucide-react"

const CREATE_NEW_VALUE = "__create_new__"

interface HeaderProps {
  portfolios: Portfolio[]
  selectedId: string | undefined
  onSelect: (id: string) => void
  onCreatePortfolio: () => void
  onEditPortfolio: () => void
  onDeletePortfolio: () => void
  onToggleMobileMenu?: () => void
}

export function Header({ portfolios, selectedId, onSelect, onCreatePortfolio, onEditPortfolio, onDeletePortfolio, onToggleMobileMenu }: HeaderProps) {
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
      <div className="flex h-14 items-center gap-3 px-4 sm:px-6">
        <button
          onClick={onToggleMobileMenu}
          className="md:hidden rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-2 font-semibold">
          <img src="/logo.svg" alt="Tech Invest" className="h-5 w-5" />
          <span className="hidden sm:inline">Tech Invest</span>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <div className="min-w-0 flex-1 max-w-48 sm:max-w-64 sm:flex-none sm:w-64">
            <Select
              value={selectedId ?? ""}
              onChange={handleChange}
              options={options}
              placeholder="Select portfolio..."
            />
          </div>
          {selectedId && (
            <>
              <button
                onClick={onEditPortfolio}
                className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                title="Rename portfolio"
              >
                <Pencil className="h-4 w-4" />
              </button>
              <button
                onClick={onDeletePortfolio}
                className="rounded-md p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                title="Delete portfolio"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
