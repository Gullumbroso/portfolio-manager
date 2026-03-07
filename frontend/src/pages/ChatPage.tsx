import { useEffect, useRef } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { ArrowLeft, Bot } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ChatMessage, StreamingMessage } from "@/components/chat/ChatMessage"
import { ChatInput } from "@/components/chat/ChatInput"
import { ToolStatusIndicator } from "@/components/chat/ToolStatusIndicator"
import { RecommendationCard } from "@/components/options/RecommendationCard"
import { useChatSession } from "@/hooks/useSessions"
import { useChat } from "@/hooks/useChat"

export function ChatPage() {
  const { portfolioId, sessionId } = useParams<{ portfolioId: string; sessionId: string }>()
  const navigate = useNavigate()
  const scrollRef = useRef<HTMLDivElement>(null)

  const { data: sessionData, isLoading: loadingSession } = useChatSession(portfolioId, sessionId)
  const {
    messages,
    isStreaming,
    streamingContent,
    toolStatuses,
    pendingRecommendations,
    sendMessage,
    setMessages,
  } = useChat(portfolioId!, sessionId!)

  // Load existing messages when session data arrives
  useEffect(() => {
    if (sessionData?.messages) {
      setMessages(sessionData.messages)
    }
  }, [sessionData, setMessages])

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, streamingContent, toolStatuses])

  const title = sessionData?.title || "New conversation"

  return (
    <div className="flex flex-col h-full -m-4 md:-m-6">
      {/* Header */}
      <div className="flex items-center gap-3 border-b px-4 py-3 flex-shrink-0">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(`/portfolio/${portfolioId}/chat`)}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="min-w-0">
          <h1 className="text-sm font-medium truncate">{title}</h1>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto p-4 space-y-4">
          {loadingSession ? (
            <div className="space-y-4">
              {[1, 2].map(i => (
                <div key={i} className="h-16 rounded-lg bg-muted/50 animate-pulse" />
              ))}
            </div>
          ) : messages.length === 0 ? (
            <div className="text-center py-20 space-y-3">
              <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="h-6 w-6 text-primary" />
              </div>
              <p className="font-medium">How can I help with your portfolio?</p>
              <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                Ask about your holdings, get stock analysis, discuss market conditions, or explore options strategies.
              </p>
              <div className="flex flex-wrap justify-center gap-2 pt-2">
                {[
                  "How is my portfolio doing?",
                  "What's happening with AAPL?",
                  "Suggest a covered call strategy",
                ].map(suggestion => (
                  <button
                    key={suggestion}
                    onClick={() => sendMessage(suggestion)}
                    className="text-xs border rounded-full px-3 py-1.5 text-muted-foreground hover:bg-accent transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map(msg => (
              <ChatMessage key={msg.id} message={msg} portfolioId={portfolioId!} />
            ))
          )}

          {/* Streaming content */}
          {isStreaming && (
            <>
              {toolStatuses.map((ts, i) => (
                <ToolStatusIndicator key={i} tool={ts.tool} status={ts.status} summary={ts.summary} />
              ))}
              {pendingRecommendations.map((rec, i) => (
                <RecommendationCard key={i} recommendation={rec} portfolioId={portfolioId!} />
              ))}
              <StreamingMessage content={streamingContent} />
            </>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="flex-shrink-0">
        <ChatInput onSend={sendMessage} disabled={isStreaming} />
      </div>
    </div>
  )
}
