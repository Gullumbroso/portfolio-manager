import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { ChatInput } from "../ChatInput"

describe("ChatInput", () => {
  it("calls onSend with trimmed content on Enter", async () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} />)

    const textarea = screen.getByPlaceholderText(/ask about/i)
    await userEvent.type(textarea, "Hello world")
    await userEvent.keyboard("{Enter}")

    expect(onSend).toHaveBeenCalledWith("Hello world")
  })

  it("does not send on Shift+Enter (newline)", async () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} />)

    const textarea = screen.getByPlaceholderText(/ask about/i)
    await userEvent.type(textarea, "Hello")
    await userEvent.keyboard("{Shift>}{Enter}{/Shift}")

    expect(onSend).not.toHaveBeenCalled()
  })

  it("disables input and button when disabled prop is true", () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} disabled />)

    const textarea = screen.getByPlaceholderText(/ask about/i)
    expect(textarea).toBeDisabled()

    const button = screen.getByRole("button")
    expect(button).toBeDisabled()
  })

  it("does not send empty messages", async () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} />)

    await userEvent.keyboard("{Enter}")
    expect(onSend).not.toHaveBeenCalled()
  })

  it("clears input after sending", async () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} />)

    const textarea = screen.getByPlaceholderText(/ask about/i)
    await userEvent.type(textarea, "Hello")
    await userEvent.keyboard("{Enter}")

    expect(textarea).toHaveValue("")
  })
})
