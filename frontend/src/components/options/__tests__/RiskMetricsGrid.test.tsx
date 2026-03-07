import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { RiskMetricsGrid } from "../RiskMetricsGrid"
import { mockRecommendation } from "@/test/fixtures"

describe("RiskMetricsGrid", () => {
  it("displays all metric labels", () => {
    render(<RiskMetricsGrid recommendation={mockRecommendation} />)
    expect(screen.getByText("Max Profit")).toBeInTheDocument()
    expect(screen.getByText("Max Loss")).toBeInTheDocument()
    expect(screen.getByText("Breakeven")).toBeInTheDocument()
    expect(screen.getByText("Capital Required")).toBeInTheDocument()
    expect(screen.getByText("Margin")).toBeInTheDocument()
    expect(screen.getByText("Risk/Reward")).toBeInTheDocument()
  })

  it("displays formatted currency values", () => {
    render(<RiskMetricsGrid recommendation={mockRecommendation} />)
    expect(screen.getByText("$700.00")).toBeInTheDocument()  // max profit
    expect(screen.getByText("-$300.00")).toBeInTheDocument()  // max loss
  })

  it("displays risk/reward ratio", () => {
    render(<RiskMetricsGrid recommendation={mockRecommendation} />)
    expect(screen.getByText("2.33:1")).toBeInTheDocument()
  })

  it("shows Unlimited when max_loss is null", () => {
    const rec = { ...mockRecommendation, max_loss: null }
    render(<RiskMetricsGrid recommendation={rec} />)
    expect(screen.getByText("Unlimited")).toBeInTheDocument()
  })
})
