import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { ToolStatusIndicator } from "../ToolStatusIndicator"

describe("ToolStatusIndicator", () => {
  it("shows running state with tool label", () => {
    render(<ToolStatusIndicator tool="get_stock_quote" status="running" />)
    expect(screen.getByText(/Fetching stock quote/)).toBeInTheDocument()
  })

  it("shows done state with summary", () => {
    render(
      <ToolStatusIndicator
        tool="get_stock_quote"
        status="done"
        summary="AAPL: $185.50"
      />
    )
    expect(screen.getByText(/AAPL: \$185.50/)).toBeInTheDocument()
  })

  it("shows tool name for unknown tools", () => {
    render(<ToolStatusIndicator tool="custom_tool" status="running" />)
    expect(screen.getByText(/custom_tool/)).toBeInTheDocument()
  })
})
