import { NavLink } from "react-router-dom"
import { cn } from "@/lib/utils"
import { LayoutDashboard, ArrowLeftRight, List, Plus, X } from "lucide-react"
import { Button } from "@/components/ui/button"

interface SidebarProps {
  portfolioId: string | undefined
  onCreatePortfolio: () => void
  mobileOpen?: boolean
  onMobileClose?: () => void
}

const linkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
    isActive ? "bg-sidebar-accent text-sidebar-accent-foreground" : "text-sidebar-foreground hover:bg-sidebar-accent/50"
  )

function SidebarNav({ portfolioId, onCreatePortfolio, onNavigate }: {
  portfolioId: string | undefined
  onCreatePortfolio: () => void
  onNavigate?: () => void
}) {
  const navItems = portfolioId
    ? [
        { to: `/portfolio/${portfolioId}`, icon: LayoutDashboard, label: "Dashboard", end: true },
        { to: `/portfolio/${portfolioId}/transactions`, icon: ArrowLeftRight, label: "Transactions" },
      ]
    : []

  return (
    <>
      <nav className="flex-1 p-4 space-y-1">
        <NavLink to="/" end className={linkClass} onClick={onNavigate}>
          <List className="h-4 w-4" />
          All Portfolios
        </NavLink>
        {navItems.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={linkClass} onClick={onNavigate}>
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t">
        <Button variant="outline" size="sm" className="w-full" onClick={() => { onNavigate?.(); onCreatePortfolio() }}>
          <Plus className="h-4 w-4 mr-2" />
          New Portfolio
        </Button>
      </div>
    </>
  )
}

export function Sidebar({ portfolioId, onCreatePortfolio, mobileOpen = false, onMobileClose }: SidebarProps) {
  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-56 flex-col border-r bg-sidebar-background">
        <SidebarNav portfolioId={portfolioId} onCreatePortfolio={onCreatePortfolio} />
      </aside>

      {/* Mobile drawer */}
      <div
        className={cn(
          "fixed inset-0 z-50 md:hidden transition-opacity duration-300",
          mobileOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
      >
        <div className="absolute inset-0 bg-black/50" onClick={onMobileClose} />
        <aside
          className={cn(
            "absolute inset-y-0 left-0 w-64 flex flex-col bg-sidebar-background border-r shadow-lg transition-transform duration-300",
            mobileOpen ? "translate-x-0" : "-translate-x-full"
          )}
        >
          <div className="flex h-14 items-center justify-between px-4 border-b">
            <span className="font-semibold text-sm">Menu</span>
            <button onClick={onMobileClose} className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors">
              <X className="h-5 w-5" />
            </button>
          </div>
          <SidebarNav portfolioId={portfolioId} onCreatePortfolio={onCreatePortfolio} onNavigate={onMobileClose} />
        </aside>
      </div>
    </>
  )
}
