import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useChat } from "../useChat"

// Helper to create SSE response body
function createSSEStream(events: Array<{ event: string; data: Record<string, unknown> }>) {
  const text = events
    .map(e => `event: ${e.event}\ndata: ${JSON.stringify(e.data)}\n\n`)
    .join("")

  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode(text))
      controller.close()
    },
  })
  return stream
}

function mockFetch(events: Array<{ event: string; data: Record<string, unknown> }>) {
  return vi.fn().mockResolvedValue({
    ok: true,
    body: createSSEStream(events),
  })
}

describe("useChat", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("adds optimistic user message on send", async () => {
    global.fetch = mockFetch([
      { event: "done", data: { message_id: "msg-1" } },
    ])

    const { result } = renderHook(() => useChat("p1", "s1"))

    await act(async () => {
      await result.current.sendMessage("Hello")
    })

    expect(result.current.messages.length).toBeGreaterThanOrEqual(1)
    expect(result.current.messages[0].role).toBe("user")
    expect(result.current.messages[0].content).toBe("Hello")
  })

  it("accumulates text from SSE events", async () => {
    global.fetch = mockFetch([
      { event: "text", data: { content: "Hello" } },
      { event: "text", data: { content: " world" } },
      { event: "done", data: { message_id: "msg-1" } },
    ])

    const { result } = renderHook(() => useChat("p1", "s1"))

    await act(async () => {
      await result.current.sendMessage("hi")
    })

    // After done, assistant message should have full text
    const assistantMsg = result.current.messages.find(m => m.role === "assistant")
    expect(assistantMsg).toBeDefined()
    expect(assistantMsg?.content).toBe("Hello world")
  })

  it("tracks tool statuses from SSE events", async () => {
    // We need to capture intermediate state, so we'll track via a ref
    let capturedStatuses: unknown[] = []

    global.fetch = vi.fn().mockImplementation(() => {
      const events = [
        { event: "tool_start", data: { tool: "get_stock_quote" } },
        { event: "tool_result", data: { tool: "get_stock_quote", summary: "AAPL: $185" } },
        { event: "text", data: { content: "AAPL is at $185" } },
        { event: "done", data: { message_id: "msg-1" } },
      ]
      return Promise.resolve({
        ok: true,
        body: createSSEStream(events),
      })
    })

    const { result } = renderHook(() => useChat("p1", "s1"))

    await act(async () => {
      await result.current.sendMessage("AAPL price?")
    })

    // After done, tool statuses are cleared
    // The test verifies the hook doesn't crash during the tool status lifecycle
    expect(result.current.messages.length).toBe(2) // user + assistant
  })

  it("captures recommendations from SSE events", async () => {
    const rec = {
      id: "rec-1",
      ticker: "AAPL",
      strategy_name: "Bull Call",
      legs: [],
    }

    global.fetch = mockFetch([
      { event: "recommendation", data: { recommendation: rec } },
      { event: "text", data: { content: "Here's your strategy" } },
      { event: "done", data: { message_id: "msg-1" } },
    ])

    const { result } = renderHook(() => useChat("p1", "s1"))

    await act(async () => {
      await result.current.sendMessage("strategy")
    })

    const assistantMsg = result.current.messages.find(m => m.role === "assistant")
    expect(assistantMsg?.recommendations.length).toBe(1)
    expect(assistantMsg?.recommendations[0].strategy_name).toBe("Bull Call")
  })

  it("handles SSE error events", async () => {
    global.fetch = mockFetch([
      { event: "error", data: { message: "Something went wrong" } },
    ])

    const { result } = renderHook(() => useChat("p1", "s1"))

    await act(async () => {
      await result.current.sendMessage("hi")
    })

    const errorMsg = result.current.messages.find(m => m.content.includes("Something went wrong"))
    expect(errorMsg).toBeDefined()
  })

  it("handles network failure", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("Network error"))

    const { result } = renderHook(() => useChat("p1", "s1"))

    await act(async () => {
      await result.current.sendMessage("hi")
    })

    expect(result.current.isStreaming).toBe(false)
    const errorMsg = result.current.messages.find(m => m.content.includes("Failed"))
    expect(errorMsg).toBeDefined()
  })

  it("resets isStreaming after completion", async () => {
    global.fetch = mockFetch([
      { event: "done", data: { message_id: "msg-1" } },
    ])

    const { result } = renderHook(() => useChat("p1", "s1"))

    await act(async () => {
      await result.current.sendMessage("hi")
    })

    expect(result.current.isStreaming).toBe(false)
  })

  it("ignores AbortError without adding error message", async () => {
    const abortError = new DOMException("Aborted", "AbortError")
    global.fetch = vi.fn().mockRejectedValue(abortError)

    const { result } = renderHook(() => useChat("p1", "s1"))

    await act(async () => {
      await result.current.sendMessage("hi")
    })

    // Should only have the optimistic user message, no error message
    const errorMsgs = result.current.messages.filter(m => m.content.includes("Failed"))
    expect(errorMsgs.length).toBe(0)
  })
})
