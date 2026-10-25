import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end test configuration.
 *
 * Two web servers are started for the run:
 *  - the FastAPI backend on :8000 using the mock LLM provider and a throwaway
 *    SQLite database, so no cloud credentials or live models are needed;
 *  - the Next.js frontend on :3000 pointed at that backend.
 *
 * Both are reused if already running locally (`reuseExistingServer`), so you can
 * also start them by hand and just run the tests.
 */
const BACKEND_PORT = 8000;
const FRONTEND_PORT = 3000;
// Use localhost (not 127.0.0.1) so it matches the backend CORS allowlist
// (http://localhost:3000) and Next.js dev's same-origin HMR expectations.
const FRONTEND_HOST = "localhost";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://${FRONTEND_HOST}:${FRONTEND_PORT}`,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: [
    {
      // Fresh throwaway DB per run; mock provider keeps it credential-free.
      // PYTHON can point at the backend interpreter (e.g. the venv) if the
      // default `python` on PATH lacks the backend dependencies.
      command:
        "cd ../backend && rm -f e2e-nexusflow.db && " +
        "LLM_PROVIDER=mock DATABASE_URL=sqlite:///./e2e-nexusflow.db " +
        "AUTH_SECRET_KEY=e2e-secret-key-at-least-32-characters-long DEBUG=false " +
        "${PYTHON:-python} -m uvicorn app.main:app --host 127.0.0.1 --port " + BACKEND_PORT,
      url: `http://127.0.0.1:${BACKEND_PORT}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: "npm run dev",
      url: `http://${FRONTEND_HOST}:${FRONTEND_PORT}`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: { NEXT_PUBLIC_API_URL: `http://localhost:${BACKEND_PORT}` },
    },
  ],
});
