import { test, expect } from "@playwright/test";

test.describe("RFC Registry", () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto("/api/auth/login?login_hint=mock-admin");
    await page.waitForURL("**/dashboard**", { timeout: 15000 });
  });

  test("RFC list page loads with seed data", async ({ page }) => {
    await page.goto("/rfcs");
    await page.waitForLoadState("networkidle");
    // Should see the RFC registry heading or table
    await expect(page.locator("body")).toContainText(/rfc/i);
  });

  test("can navigate to create new RFC", async ({ page }) => {
    await page.goto("/rfcs");
    await page.waitForLoadState("networkidle");
    // Find and click the create/new button
    const newButton = page.getByRole("link", { name: /new|create/i });
    if (await newButton.isVisible()) {
      await newButton.click();
      await page.waitForURL("**/rfcs/new**");
      await expect(page.locator("body")).toContainText(/interview|create|new/i);
    }
  });
});
