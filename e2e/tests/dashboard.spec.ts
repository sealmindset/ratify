import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/api/auth/login?login_hint=mock-admin");
    await page.waitForURL("**/dashboard**", { timeout: 15000 });
  });

  test("dashboard shows content", async ({ page }) => {
    await page.waitForLoadState("networkidle");
    // Dashboard should have meaningful content (not empty)
    const body = await page.locator("body").textContent();
    expect(body?.length).toBeGreaterThan(50);
  });

  test("sidebar navigation works", async ({ page }) => {
    // Check sidebar has navigation links
    const sidebar = page.locator("nav, [data-sidebar]").first();
    await expect(sidebar).toBeVisible();

    // Should have links to main sections
    const links = page.getByRole("link");
    const count = await links.count();
    expect(count).toBeGreaterThan(2);
  });
});
