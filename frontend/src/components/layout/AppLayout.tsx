import { useState } from "react"
import { Outlet, useNavigate, useParams } from "react-router-dom"
import { Header } from "./Header"
import { Sidebar } from "./Sidebar"
import { usePortfolios, useCreatePortfolio } from "@/hooks/usePortfolio"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export function AppLayout() {
  const navigate = useNavigate()
  const { portfolioId } = useParams()
  const { data: portfolios = [] } = usePortfolios()
  const createPortfolio = useCreatePortfolio()
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState("")

  function handleSelect(id: string) {
    navigate(`/portfolio/${id}`)
  }

  async function handleCreate() {
    if (!newName.trim()) return
    const portfolio = await createPortfolio.mutateAsync({ name: newName.trim() })
    setShowCreate(false)
    setNewName("")
    navigate(`/portfolio/${portfolio.id}`)
  }

  return (
    <div className="flex h-screen flex-col">
      <Header portfolios={portfolios} selectedId={portfolioId} onSelect={handleSelect} onCreatePortfolio={() => setShowCreate(true)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar portfolioId={portfolioId} onCreatePortfolio={() => setShowCreate(true)} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet context={{ onCreatePortfolio: () => setShowCreate(true) }} />
        </main>
      </div>

      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Portfolio</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="name">Portfolio Name</Label>
              <Input
                id="name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="My Tech Portfolio"
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={!newName.trim()}>Create</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
