import { useNavigate, useOutletContext } from "react-router-dom"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { usePortfolios } from "@/hooks/usePortfolio"
import { Plus, Briefcase } from "lucide-react"

export function PortfolioListPage() {
  const navigate = useNavigate()
  const { onCreatePortfolio } = useOutletContext<{ onCreatePortfolio: () => void }>()
  const { data: portfolios, isLoading } = usePortfolios()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Portfolios</h1>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-6 w-32 mb-2" />
                <Skeleton className="h-4 w-48" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : !portfolios?.length ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Briefcase className="h-12 w-12 text-muted-foreground mb-4" />
            <h2 className="text-lg font-semibold mb-2">No portfolios yet</h2>
            <p className="text-muted-foreground mb-4">Create your first portfolio to start tracking investments.</p>
            <Button onClick={onCreatePortfolio}>
              <Plus className="h-4 w-4 mr-2" />
              Create Portfolio
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {portfolios.map((p) => (
            <Card
              key={p.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/portfolio/${p.id}`)}
            >
              <CardContent className="p-6">
                <h3 className="font-semibold text-lg">{p.name}</h3>
                {p.description && (
                  <p className="text-sm text-muted-foreground mt-1">{p.description}</p>
                )}
                <p className="text-xs text-muted-foreground mt-2">
                  Created {new Date(p.created_at).toLocaleDateString()}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
