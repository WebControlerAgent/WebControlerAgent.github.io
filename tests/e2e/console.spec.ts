import { test, expect } from "@playwright/test";

test("AIWCU console loads with the expected title and root", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", error => pageErrors.push(error.message));

  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page).toHaveTitle(/AIWCU/i);
  await expect(page.locator("#root")).toBeAttached();
  await expect(page.locator("body")).toContainText(/AIWCU|Universe|Operations/i);
  await page.waitForTimeout(1500);
  expect(pageErrors, "Unexpected uncaught page errors").toEqual([]);
});

test("console boot overlay exposes its branded shell", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page.locator("#boot")).toBeAttached();
  await expect(page.locator(".boot-title")).toHaveCount(1);
  await expect(page.locator(".boot-title")).toContainText("AIWCU");
});
