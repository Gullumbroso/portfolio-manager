import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { RecommendationCard } from "../RecommendationCard"
import { mockRecommendation } from "@/test/fixtures"
import { MemoryRouter } from "react-router-dom"

// Mock the API client
vi.mock("@/api/client", () => ({
  recordDecision: vi.fn().mockResolvedValue({
    id: "dec-1",
    recommendation_id: "rec-1",
    decision: "accepted",
    notes: "",
    created_at: "2026-03-07T00:00:00Z",
  }),
}))

function renderCard(overrides = {}) {
  const rec = { ...mockRecommendation, ...overrides }
  return render(
    <MemoryRouter>
      <RecommendationCard recommendation={rec} portfolioId="p1" />
    </MemoryRouter>
  )
}

describe("RecommendationCard", () => {
  it("shows strategy name, ticker, and confidence", () => {
    renderCard()
    expect(screen.getByText("Bull Call Spread")).toBeInTheDocument()
    expect(screen.getByText("AAPL")).toBeInTheDocument()
    expect(screen.getByText("75% confidence")).toBeInTheDocument()
  })

  it("shows risk score", () => {
    renderCard()
    expect(screen.getByText("Risk 4/10")).toBeInTheDocument()
  })

  it("shows accept and reject buttons when no decision", () => {
    renderCard()
    expect(screen.getByText("Accept")).toBeInTheDocument()
    expect(screen.getByText("Reject")).toBeInTheDocument()
  })

  it("shows decision state when decision exists", () => {
    renderCard({
      decision: {
        id: "dec-1",
        recommendation_id: "rec-1",
        decision: "accepted",
        notes: "",
        created_at: "2026-03-07T00:00:00Z",
      },
    })
    expect(screen.getByText("Accepted")).toBeInTheDocument()
    expect(screen.queryByText("Accept")).not.toBeInTheDocument()
  })

  it("shows risk flag badges", () => {
    renderCard({ has_unlimited_risk: true })
    expect(screen.getByText("Unlimited Risk")).toBeInTheDocument()
  })

  it("toggles analysis details on click", () => {
    renderCard()
    expect(screen.queryByText("Strategy Reasoning")).not.toBeInTheDocument()
    fireEvent.click(screen.getByText("Show analysis details"))
    expect(screen.getByText("Strategy Reasoning")).toBeInTheDocument()
    expect(screen.getByText("Bullish on AAPL")).toBeInTheDocument()
  })
})
