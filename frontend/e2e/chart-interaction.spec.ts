import { test, expect } from "@playwright/test"

// Test that lightweight-charts instances are configured as non-interactive.
// Verifies the fix for accidental chart zoom when scrolling on mobile.
//
// These tests navigate to a portfolio dashboard and check the IndexComparisonChart,
// which always renders (it shows index data even without portfolio performance data).
// If no chart canvas is found, the test is skipped.

const PORTFOLIO_DASHBOARD_REGEX = /\/portfolio\/[\w-]+$/

test.describe("Chart interaction disabled", () => {
  test.beforeEach(async ({ page }) => {
    // Go to home, wait for portfolios to load, click the first one
    await page.goto("/")
    // Wait for portfolio cards (they have the portfolio name as h3)
    const card = page.locator("h3").first()
    await card.waitFor({ timeout: 15000 })
    await card.click()
    await page.waitForURL(PORTFOLIO_DASHBOARD_REGEX, { timeout: 10000 })
    // Give charts time to render (index data fetched async)
    await page.waitForTimeout(5000)
  })

  test("chart canvas does not zoom on mouse wheel @desktop", async ({ page }) => {
    const charts = page.locator("canvas")
    const count = await charts.count()
    test.skip(count === 0, "No charts rendered — no performance/index data available")

    const chart = charts.first()
    const box = await chart.boundingBox()
    expect(box).not.toBeNull()

    const before = await chart.screenshot()

    await page.mouse.move(box!.x + box!.width / 2, box!.y + box!.height / 2)
    await page.mouse.wheel(0, -200)
    await page.waitForTimeout(500)

    const after = await chart.screenshot()
    expect(before.equals(after)).toBe(true)
  })

  test("chart canvas does not pan on horizontal drag @desktop", async ({ page }) => {
    const charts = page.locator("canvas")
    const count = await charts.count()
    test.skip(count === 0, "No charts rendered — no performance/index data available")

    const chart = charts.first()
    const box = await chart.boundingBox()
    expect(box).not.toBeNull()

    const before = await chart.screenshot()

    const startX = box!.x + box!.width * 0.2
    const endX = box!.x + box!.width * 0.8
    const y = box!.y + box!.height / 2

    await page.mouse.move(startX, y)
    await page.mouse.down()
    await page.mouse.move(endX, y, { steps: 10 })
    await page.mouse.up()
    await page.waitForTimeout(500)

    const after = await chart.screenshot()
    expect(before.equals(after)).toBe(true)
  })

  test("double tap on chart does not change it @mobile", async ({ page }) => {
    test.skip(!test.info().project.name.includes("mobile"), "Mobile only")

    const charts = page.locator("canvas")
    const count = await charts.count()
    test.skip(count === 0, "No charts rendered — no performance/index data available")

    const chart = charts.first()
    const box = await chart.boundingBox()
    expect(box).not.toBeNull()

    const before = await chart.screenshot()

    const cx = box!.x + box!.width / 2
    const cy = box!.y + box!.height / 2

    await page.touchscreen.tap(cx, cy)
    await page.waitForTimeout(100)
    await page.touchscreen.tap(cx, cy)
    await page.waitForTimeout(500)

    const after = await chart.screenshot()
    expect(before.equals(after)).toBe(true)
  })
})
