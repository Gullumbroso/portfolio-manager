import { useNavigate, useParams } from "react-router-dom"
import { Plus, MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { SessionCard } from "@/components/chat/SessionCard"
import { useChatSessions, useCreateChatSession, useDeleteChatSession } from "@/hooks/useSessions"

export function ChatListPage() {
  const { portfolioId } = useParams<{ portfolioId: string }>()
  const navigate = useNavigate()
  const { data: sessions, isLoading } = useChatSessions(portfolioId)
  const createSession = useCreateChatSession(portfolioId!)
  const deleteSession = useDeleteChatSession(portfolioId!)

  const handleNewChat = async () => {
    const session = await createSession.mutateAsync()
    navigate(`/portfolio/${portfolioId}/chat/${session.id}`)
  }

  const handleDelete = (sessionId: string) => {
    if (confirm("Delete this conversation?")) {
      deleteSession.mutate(sessionId)
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">AI Consultant</h1>
          <p className="text-sm text-muted-foreground">Chat with AI about your portfolio and investment strategies</p>
        </div>
        <Button onClick={handleNewChat} disabled={createSession.isPending}>
          <Plus className="h-4 w-4 mr-2" />
          New Chat
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-20 rounded-lg border bg-muted/50 animate-pulse" />
          ))}
        </div>
      ) : sessions && sessions.length > 0 ? (
        <div className="space-y-2">
          {sessions.map(session => (
            <SessionCard
              key={session.id}
              session={session}
              onClick={() => navigate(`/portfolio/${portfolioId}/chat/${session.id}`)}
              onDelete={() => handleDelete(session.id)}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-16 space-y-3">
          <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
            <MessageSquare className="h-6 w-6 text-primary" />
          </div>
          <p className="text-muted-foreground text-sm">
            No conversations yet. Start a new chat to get AI-powered investment advice.
          </p>
          <Button onClick={handleNewChat} disabled={createSession.isPending}>
            <Plus className="h-4 w-4 mr-2" />
            Start a conversation
          </Button>
        </div>
      )}
    </div>
  )
}
