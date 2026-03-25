import { test, expect } from "@playwright/test";

test.describe("Health checks", () => {
  test("frontend loads", async ({ page }) => {
    const resp = await page.goto("/");
    expect(resp?.status()).toBeLessThan(400);
  });

  test("backend health endpoint", async ({ request }) => {
    const resp = await request.get("/api/health");
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.status).toBe("ok");
  });
});
