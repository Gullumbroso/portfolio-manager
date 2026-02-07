import { NavLink } from "react-router-dom"
import { cn } from "@/lib/utils"
import { LayoutDashboard, ArrowLeftRight, List, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"

interface SidebarProps {
  portfolioId: string | undefined
  onCreatePortfolio: () => void
}

export function Sidebar({ portfolioId, onCreatePortfolio }: SidebarProps) {
  const navItems = portfolioId
    ? [
        { to: `/portfolio/${portfolioId}`, icon: LayoutDashboard, label: "Dashboard", end: true },
        { to: `/portfolio/${portfolioId}/transactions`, icon: ArrowLeftRight, label: "Transactions" },
      ]
    : []

  return (
    <aside className="hidden md:flex w-56 flex-col border-r bg-sidebar-background">
      <nav className="flex-1 p-4 space-y-1">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
              isActive ? "bg-sidebar-accent text-sidebar-accent-foreground" : "text-sidebar-foreground hover:bg-sidebar-accent/50"
            )
          }
        >
          <List className="h-4 w-4" />
          All Portfolios
        </NavLink>

        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                isActive ? "bg-sidebar-accent text-sidebar-accent-foreground" : "text-sidebar-foreground hover:bg-sidebar-accent/50"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t">
        <Button variant="outline" size="sm" className="w-full" onClick={onCreatePortfolio}>
          <Plus className="h-4 w-4 mr-2" />
          New Portfolio
        </Button>
      </div>
    </aside>
  )
}
