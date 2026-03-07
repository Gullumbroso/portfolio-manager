import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { ChatMessage, ThinkingIndicator } from "../ChatMessage"
import { mockUserMessage, mockAssistantMessage } from "@/test/fixtures"
import { MemoryRouter } from "react-router-dom"

// Wrap in MemoryRouter since RecommendationCard may use routing
function renderWithRouter(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

describe("ChatMessage", () => {
  it("renders user message content", () => {
    renderWithRouter(<ChatMessage message={mockUserMessage} portfolioId="p1" />)
    expect(screen.getByText("Give me a strategy for AAPL")).toBeInTheDocument()
  })

  it("renders assistant message with markdown", () => {
    renderWithRouter(<ChatMessage message={mockAssistantMessage} portfolioId="p1" />)
    // Markdown bold should render
    expect(screen.getByText(/bull call spread/)).toBeInTheDocument()
  })

  it("renders recommendation cards for assistant messages", () => {
    renderWithRouter(<ChatMessage message={mockAssistantMessage} portfolioId="p1" />)
    // RecommendationCard renders strategy name
    expect(screen.getByText("Bull Call Spread")).toBeInTheDocument()
  })
})

describe("ThinkingIndicator", () => {
  it("renders animated dots", () => {
    const { container } = render(<ThinkingIndicator />)
    // 3 bouncing dots
    const dots = container.querySelectorAll("span.rounded-full")
    expect(dots.length).toBe(3)
  })
})
