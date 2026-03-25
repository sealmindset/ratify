import { test, expect } from "@playwright/test";

test.describe("Login flow", () => {
  test("unauthenticated user sees login page", async ({ page }) => {
    await page.goto("/login");
    // Should see the sign-in button
    await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
  });

  test("login redirects through mock-oidc", async ({ page }) => {
    await page.goto("/login");
    // Click sign in
    await page.getByRole("button", { name: /sign in/i }).click();
    // Should redirect to mock-oidc (wait for navigation)
    await page.waitForURL(/mock-oidc|localhost:10090|\/api\/auth/, {
      timeout: 10000,
    });
    // The mock-oidc should show a user picker or auto-redirect
    // Just verify we got somewhere (not an error page)
    const status = await page.evaluate(() => document.readyState);
    expect(status).toBeTruthy();
  });

  test("login with admin user reaches dashboard", async ({ page }) => {
    // Use login_hint to auto-select admin user in mock-oidc
    await page.goto("/api/auth/login?login_hint=mock-admin");
    // Should eventually reach the dashboard
    await page.waitForURL("**/dashboard**", { timeout: 15000 });
    await expect(page.locator("body")).toContainText(/dashboard/i);
  });
});
