import { expect, test } from "@playwright/test";

test("the app boots and renders the design tokens end to end", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "Understand a stock before you decide anything about it.",
  );
  // The CTA is a real navigation link ("Get started free" -> /signup),
  // not a <button>, so its accessible role is "link".
  await expect(page.getByRole("link", { name: "Get started free" }).first()).toBeVisible();
});
