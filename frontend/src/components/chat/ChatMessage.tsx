import { cn } from "@/lib/utils"
import type { ChatMessage as ChatMessageType } from "@/types"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { RecommendationCard } from "@/components/options/RecommendationCard"
import { User, Bot } from "lucide-react"

interface ChatMessageProps {
  message: ChatMessageType
  portfolioId: string
}

export function ChatMessage({ message, portfolioId }: ChatMessageProps) {
  const isUser = message.role === "user"

  return (
    <div className={cn("flex gap-3", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center mt-1">
          <Bot className="h-4 w-4 text-primary" />
        </div>
      )}
      <div className={cn("max-w-[85%] md:max-w-[75%] space-y-3", isUser ? "order-first" : "")}>
        <div
          className={cn(
            "rounded-lg px-4 py-2.5 text-sm",
            isUser
              ? "bg-primary text-primary-foreground ml-auto"
              : "bg-muted"
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none overflow-x-auto [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>
        {message.recommendations?.map(rec => (
          <RecommendationCard key={rec.id} recommendation={rec} portfolioId={portfolioId} />
        ))}
      </div>
      {isUser && (
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-secondary flex items-center justify-center mt-1">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  )
}

interface StreamingMessageProps {
  content: string
}

export function StreamingMessage({ content }: StreamingMessageProps) {
  if (!content) return null

  return (
    <div className="flex gap-3 justify-start">
      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center mt-1">
        <Bot className="h-4 w-4 text-primary" />
      </div>
      <div className="max-w-[85%] md:max-w-[75%]">
        <div className="rounded-lg px-4 py-2.5 text-sm bg-muted">
          <div className="prose prose-sm dark:prose-invert max-w-none overflow-x-auto [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </div>
          <span className="inline-block w-1.5 h-4 bg-primary/60 animate-pulse ml-0.5 align-middle" />
        </div>
      </div>
    </div>
  )
}

export function ThinkingIndicator() {
  return (
    <div className="flex gap-3 justify-start">
      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center mt-1">
        <Bot className="h-4 w-4 text-primary" />
      </div>
      <div className="rounded-lg px-4 py-3 bg-muted">
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-foreground/40 animate-[bounce_1.4s_ease-in-out_infinite]" />
          <span className="w-2 h-2 rounded-full bg-foreground/40 animate-[bounce_1.4s_ease-in-out_0.2s_infinite]" />
          <span className="w-2 h-2 rounded-full bg-foreground/40 animate-[bounce_1.4s_ease-in-out_0.4s_infinite]" />
        </div>
      </div>
    </div>
  )
}
