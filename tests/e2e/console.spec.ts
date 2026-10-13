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

test("Focus Agent control selects the Manager inspector", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "⌖ Focus Agent" }).click();
  await expect(page.locator(".inspector h2")).toHaveText("Manager");
  await expect(page.locator(".inspector")).toContainText("Universe Operations Captain");
});

test("Manager chat accepts a status query and responds", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const input = page.getByRole("textbox", { name: "Message Manager" });
  await expect(input).toBeVisible();
  await input.fill("status");
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(page.locator(".chat-messages")).toContainText("Actual Runtime:");
  await expect(page.locator(".chat-messages")).toContainText("Working agents:");
});
