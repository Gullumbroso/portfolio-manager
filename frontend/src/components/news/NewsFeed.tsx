import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { NewsCard } from "./NewsCard"
import { Skeleton } from "@/components/ui/skeleton"
import type { NewsArticle } from "@/types"

interface Props {
  articles: NewsArticle[] | undefined
  isLoading: boolean
}

export function NewsFeed({ articles, isLoading }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>News</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          [1, 2, 3].map((i) => <Skeleton key={i} className="h-24 w-full" />)
        ) : !articles?.length ? (
          <p className="text-muted-foreground text-sm">No recent news.</p>
        ) : (
          articles.map((a, i) => <NewsCard key={i} article={a} />)
        )}
      </CardContent>
    </Card>
  )
}
