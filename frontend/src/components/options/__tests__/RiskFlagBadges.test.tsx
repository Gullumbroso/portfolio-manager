import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { RiskFlagBadges } from "../RiskFlagBadges"
import { mockRecommendation } from "@/test/fixtures"

describe("RiskFlagBadges", () => {
  it("renders nothing when no flags active", () => {
    const { container } = render(<RiskFlagBadges recommendation={mockRecommendation} />)
    expect(container.innerHTML).toBe("")
  })

  it("renders unlimited risk badge with destructive variant", () => {
    const rec = { ...mockRecommendation, has_unlimited_risk: true }
    render(<RiskFlagBadges recommendation={rec} />)
    expect(screen.getByText("Unlimited Risk")).toBeInTheDocument()
  })

  it("renders assignment risk badge", () => {
    const rec = { ...mockRecommendation, has_assignment_risk: true }
    render(<RiskFlagBadges recommendation={rec} />)
    expect(screen.getByText("Assignment Risk")).toBeInTheDocument()
  })

  it("renders high gamma badge", () => {
    const rec = { ...mockRecommendation, has_high_gamma: true }
    render(<RiskFlagBadges recommendation={rec} />)
    expect(screen.getByText("High Gamma")).toBeInTheDocument()
  })

  it("renders vol sensitive badge", () => {
    const rec = { ...mockRecommendation, has_volatility_sensitivity: true }
    render(<RiskFlagBadges recommendation={rec} />)
    expect(screen.getByText("Vol Sensitive")).toBeInTheDocument()
  })

  it("renders multiple flags", () => {
    const rec = {
      ...mockRecommendation,
      has_unlimited_risk: true,
      has_high_gamma: true,
    }
    render(<RiskFlagBadges recommendation={rec} />)
    expect(screen.getByText("Unlimited Risk")).toBeInTheDocument()
    expect(screen.getByText("High Gamma")).toBeInTheDocument()
  })
})
