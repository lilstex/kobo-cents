import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end tests, justified in docs/frontend-architecture/00.md by
 * this app's real accounts and real payments, not just component
 * behavior in isolation.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL: "http://localhost:3000",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
