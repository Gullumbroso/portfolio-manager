import { useState, useCallback, useRef } from "react"
import { getChatMessageUrl } from "@/api/client"
import type { ChatMessage, OptionsRecommendation } from "@/types"

interface StreamEvent {
  event: string
  data: Record<string, unknown>
}

interface ToolStatus {
  tool: string
  status: "running" | "done"
  summary?: string
}

interface UseChatReturn {
  messages: ChatMessage[]
  isStreaming: boolean
  streamingContent: string
  toolStatuses: ToolStatus[]
  pendingRecommendations: OptionsRecommendation[]
  sendMessage: (content: string) => Promise<void>
  setMessages: (msgs: ChatMessage[]) => void
}

export function useChat(portfolioId: string, sessionId: string): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState("")
  const [toolStatuses, setToolStatuses] = useState<ToolStatus[]>([])
  const [pendingRecommendations, setPendingRecommendations] = useState<OptionsRecommendation[]>([])
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(async (content: string) => {
    if (isStreaming) return

    // Add user message optimistically
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      session_id: sessionId,
      role: "user",
      content,
      has_recommendation: false,
      created_at: new Date().toISOString(),
      recommendations: [],
    }
    setMessages(prev => [...prev, userMsg])
    setIsStreaming(true)
    setStreamingContent("")
    setToolStatuses([])
    setPendingRecommendations([])

    const url = getChatMessageUrl(portfolioId, sessionId)
    const controller = new AbortController()
    abortRef.current = controller

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error("No response body")

      const decoder = new TextDecoder()
      let buffer = ""
      let accumulatedText = ""
      const accumulatedRecs: OptionsRecommendation[] = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        let currentEvent = ""
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7)
          } else if (line.startsWith("data: ") && currentEvent) {
            try {
              const data = JSON.parse(line.slice(6))
              handleEvent({ event: currentEvent, data }, accumulatedText, accumulatedRecs, setStreamingContent, setToolStatuses, setPendingRecommendations)

              if (currentEvent === "text") {
                accumulatedText += data.content
              } else if (currentEvent === "recommendation") {
                accumulatedRecs.push(data.recommendation as OptionsRecommendation)
              } else if (currentEvent === "title_update") {
                // Title updated - could dispatch an event but sessions will refetch
              } else if (currentEvent === "done") {
                // Finalize: add assistant message
                const assistantMsg: ChatMessage = {
                  id: data.message_id || crypto.randomUUID(),
                  session_id: sessionId,
                  role: "assistant",
                  content: accumulatedText,
                  has_recommendation: accumulatedRecs.length > 0,
                  created_at: new Date().toISOString(),
                  recommendations: accumulatedRecs,
                }
                setMessages(prev => [...prev, assistantMsg])
                setStreamingContent("")
                setToolStatuses([])
              } else if (currentEvent === "error") {
                const errorMsg: ChatMessage = {
                  id: crypto.randomUUID(),
                  session_id: sessionId,
                  role: "assistant",
                  content: `Error: ${data.message || "Something went wrong"}`,
                  has_recommendation: false,
                  created_at: new Date().toISOString(),
                  recommendations: [],
                }
                setMessages(prev => [...prev, errorMsg])
              }
            } catch {
              // Skip malformed JSON
            }
            currentEvent = ""
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        const errorMsg: ChatMessage = {
          id: crypto.randomUUID(),
          session_id: sessionId,
          role: "assistant",
          content: "Failed to get a response. Please try again.",
          has_recommendation: false,
          created_at: new Date().toISOString(),
          recommendations: [],
        }
        setMessages(prev => [...prev, errorMsg])
      }
    } finally {
      setIsStreaming(false)
      abortRef.current = null
    }
  }, [portfolioId, sessionId, isStreaming])

  return {
    messages,
    isStreaming,
    streamingContent,
    toolStatuses,
    pendingRecommendations,
    sendMessage,
    setMessages,
  }
}

function handleEvent(
  event: StreamEvent,
  _accText: string,
  _accRecs: OptionsRecommendation[],
  setStreamingContent: React.Dispatch<React.SetStateAction<string>>,
  setToolStatuses: React.Dispatch<React.SetStateAction<ToolStatus[]>>,
  setPendingRecommendations: React.Dispatch<React.SetStateAction<OptionsRecommendation[]>>,
) {
  switch (event.event) {
    case "text":
      setStreamingContent(prev => prev + (event.data.content as string))
      break
    case "tool_start":
      setToolStatuses(prev => [
        ...prev,
        { tool: event.data.tool as string, status: "running" },
      ])
      break
    case "tool_result":
      setToolStatuses(prev =>
        prev.map(t =>
          t.tool === event.data.tool && t.status === "running"
            ? { ...t, status: "done" as const, summary: event.data.summary as string }
            : t
        )
      )
      break
    case "recommendation":
      setPendingRecommendations(prev => [...prev, event.data.recommendation as OptionsRecommendation])
      break
  }
}
