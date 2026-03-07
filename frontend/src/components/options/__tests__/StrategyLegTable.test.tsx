import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { StrategyLegTable } from "../StrategyLegTable"
import { mockLeg, mockSellLeg } from "@/test/fixtures"

describe("StrategyLegTable", () => {
  it("renders all column headers", () => {
    render(<StrategyLegTable legs={[mockLeg]} />)
    for (const header of ["Action", "Type", "Strike", "Qty", "Premium", "IV", "Delta", "Gamma", "Theta", "Vega"]) {
      expect(screen.getByText(header)).toBeInTheDocument()
    }
  })

  it("renders leg data correctly", () => {
    render(<StrategyLegTable legs={[mockLeg]} />)
    expect(screen.getByText("buy")).toBeInTheDocument()
    expect(screen.getByText("call")).toBeInTheDocument()
    expect(screen.getByText("$150.00")).toBeInTheDocument()
    expect(screen.getByText("$5.00")).toBeInTheDocument()
    expect(screen.getByText("0.520")).toBeInTheDocument()  // delta
  })

  it("styles buy legs green and sell legs red", () => {
    render(<StrategyLegTable legs={[mockLeg, mockSellLeg]} />)
    const buyText = screen.getByText("buy")
    const sellText = screen.getByText("sell")
    expect(buyText.className).toContain("green")
    expect(sellText.className).toContain("red")
  })

  it("renders multiple legs", () => {
    render(<StrategyLegTable legs={[mockLeg, mockSellLeg]} />)
    expect(screen.getByText("$150.00")).toBeInTheDocument()
    expect(screen.getByText("$155.00")).toBeInTheDocument()
  })
})
