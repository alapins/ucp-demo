import { defineConfig, devices } from "@playwright/test";

/**
 * The merchant window driven against the real demo — real Invoice API, real Event Bus,
 * real browser. Nothing here is stubbed, because the criteria these tests cover are
 * about what a Merchant operator sees happen, and a stubbed stream cannot show that.
 *
 * One worker: the tests share one system of record, and the Invoice list is global.
 */
export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  use: { baseURL: "http://localhost:5173", trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: devices["Desktop Chrome"] }],
  webServer: {
    // Brings the whole demo up if it isn't already, and waits on the same healthchecks
    // that order startup for an operator running `docker compose up`.
    command: "docker compose --file ../compose.yaml up --build --wait",
    url: "http://localhost:5173",
    reuseExistingServer: true,
    timeout: 600_000,
    stdout: "pipe",
    stderr: "pipe",
  },
});
