import { MessageSquare, Trash2 } from "lucide-react"
import type { ChatSession } from "@/types"
import { cn } from "@/lib/utils"

interface SessionCardProps {
  session: ChatSession
  onClick: () => void
  onDelete: () => void
}

export function SessionCard({ session, onClick, onDelete }: SessionCardProps) {
  const date = new Date(session.updated_at)
  const dateStr = date.toLocaleDateString(undefined, { month: "short", day: "numeric" })
  const timeStr = date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })

  return (
    <div
      className={cn(
        "group flex items-start gap-3 rounded-lg border p-4 cursor-pointer transition-colors",
        "hover:bg-accent/50"
      )}
      onClick={onClick}
    >
      <div className="flex-shrink-0 w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center">
        <MessageSquare className="h-4 w-4 text-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm truncate">
          {session.title || "New conversation"}
        </p>
        {session.last_message_preview && (
          <p className="text-xs text-muted-foreground truncate mt-0.5">
            {session.last_message_preview}
          </p>
        )}
        <p className="text-xs text-muted-foreground mt-1">
          {dateStr} at {timeStr}
        </p>
      </div>
      <button
        onClick={e => { e.stopPropagation(); onDelete() }}
        className="opacity-0 group-hover:opacity-100 p-1.5 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </div>
  )
}
