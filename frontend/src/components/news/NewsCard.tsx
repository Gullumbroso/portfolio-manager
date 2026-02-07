import { Card, CardContent } from "@/components/ui/card"
import type { NewsArticle } from "@/types"

interface Props {
  article: NewsArticle
}

export function NewsCard({ article }: Props) {
  const date = new Date(article.datetime * 1000)

  return (
    <a href={article.url} target="_blank" rel="noopener noreferrer" className="block">
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4 flex gap-4">
          {article.image && (
            <img
              src={article.image}
              alt=""
              className="w-20 h-20 rounded object-cover flex-shrink-0"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
          )}
          <div className="min-w-0">
            <h4 className="font-medium text-sm line-clamp-2">{article.headline}</h4>
            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{article.summary}</p>
            <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
              <span>{article.source}</span>
              <span>{date.toLocaleDateString()}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </a>
  )
}
