import { useState, useEffect } from "react"
import { Outlet, useNavigate, useParams, useLocation } from "react-router-dom"
import { Header } from "./Header"
import { Sidebar } from "./Sidebar"
import { usePortfolios, useCreatePortfolio, useUpdatePortfolio, useDeletePortfolio } from "@/hooks/usePortfolio"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2 } from "lucide-react"

export function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { portfolioId } = useParams()
  const { data: portfolios = [] } = usePortfolios()
  const createPortfolio = useCreatePortfolio()
  const updatePortfolio = useUpdatePortfolio()
  const deletePortfolioMutation = useDeletePortfolio()
  const [showCreate, setShowCreate] = useState(false)
  const [showEdit, setShowEdit] = useState(false)
  const [showDelete, setShowDelete] = useState(false)
  const [newName, setNewName] = useState("")
  const [editName, setEditName] = useState("")
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const selectedPortfolio = portfolios.find((p) => p.id === portfolioId)

  useEffect(() => {
    setMobileMenuOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (showEdit && selectedPortfolio) {
      setEditName(selectedPortfolio.name)
    }
  }, [showEdit, selectedPortfolio])

  function handleSelect(id: string) {
    navigate(`/portfolio/${id}`)
  }

  async function handleCreate() {
    if (!newName.trim() || createPortfolio.isPending) return
    try {
      const portfolio = await createPortfolio.mutateAsync({ name: newName.trim() })
      setShowCreate(false)
      setNewName("")
      navigate(`/portfolio/${portfolio.id}`)
    } catch {
      // mutation error state is tracked by react-query and displayed in the dialog
    }
  }

  async function handleEdit() {
    if (!editName.trim() || !portfolioId || updatePortfolio.isPending) return
    await updatePortfolio.mutateAsync({ id: portfolioId, name: editName.trim() })
    setShowEdit(false)
  }

  async function handleDelete() {
    if (!portfolioId || deletePortfolioMutation.isPending) return
    await deletePortfolioMutation.mutateAsync(portfolioId)
    setShowDelete(false)
    navigate("/")
  }

  return (
    <div className="flex h-screen flex-col">
      <Header
        portfolios={portfolios}
        selectedId={portfolioId}
        onSelect={handleSelect}
        onCreatePortfolio={() => setShowCreate(true)}
        onEditPortfolio={() => setShowEdit(true)}
        onDeletePortfolio={() => setShowDelete(true)}
        onToggleMobileMenu={() => setMobileMenuOpen((o) => !o)}
      />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          portfolioId={portfolioId}
          onCreatePortfolio={() => setShowCreate(true)}
          mobileOpen={mobileMenuOpen}
          onMobileClose={() => setMobileMenuOpen(false)}
        />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet context={{ onCreatePortfolio: () => setShowCreate(true) }} />
        </main>
      </div>

      {/* Create Portfolio Dialog */}
      <Dialog open={showCreate} onOpenChange={(open) => { if (!createPortfolio.isPending) { setShowCreate(open); if (!open) createPortfolio.reset() } }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Portfolio</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="create-name">Portfolio Name</Label>
              <Input
                id="create-name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="My Tech Portfolio"
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              />
            </div>
            {createPortfolio.isError && (
              <p className="text-sm text-destructive">
                {(createPortfolio.error as any)?.response?.data?.detail || "Failed to create portfolio. Please try again."}
              </p>
            )}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreate(false)} disabled={createPortfolio.isPending}>Cancel</Button>
              <Button onClick={handleCreate} disabled={!newName.trim() || createPortfolio.isPending} className={createPortfolio.isPending ? "disabled:opacity-100" : ""}>
                {createPortfolio.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Create
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Portfolio Dialog */}
      <Dialog open={showEdit} onOpenChange={(open) => !updatePortfolio.isPending && setShowEdit(open)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Portfolio</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">Portfolio Name</Label>
              <Input
                id="edit-name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                placeholder="Portfolio name"
                onKeyDown={(e) => e.key === "Enter" && handleEdit()}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowEdit(false)} disabled={updatePortfolio.isPending}>Cancel</Button>
              <Button onClick={handleEdit} disabled={!editName.trim() || editName.trim() === selectedPortfolio?.name || updatePortfolio.isPending} className={updatePortfolio.isPending ? "disabled:opacity-100" : ""}>
                {updatePortfolio.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Save
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Portfolio Dialog */}
      <Dialog open={showDelete} onOpenChange={(open) => !deletePortfolioMutation.isPending && setShowDelete(open)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Portfolio</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete <span className="font-semibold">{selectedPortfolio?.name}</span>? This will permanently remove the portfolio and all its transactions. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setShowDelete(false)} disabled={deletePortfolioMutation.isPending}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete} disabled={deletePortfolioMutation.isPending} className={deletePortfolioMutation.isPending ? "disabled:opacity-100" : ""}>
              {deletePortfolioMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Delete
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
