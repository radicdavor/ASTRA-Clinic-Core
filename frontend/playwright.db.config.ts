import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e-db",
  timeout: 45_000,
  expect: { timeout: 10_000 },
  reporter: [["list"]],
  use: {
    baseURL: process.env.ASTRA_E2E_FRONTEND_URL ?? "http://127.0.0.1:5174",
    timezoneId: "America/New_York",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
