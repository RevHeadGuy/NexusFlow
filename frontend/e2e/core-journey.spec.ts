import { test, expect, type Page } from "@playwright/test";

/**
 * Core journey end-to-end tests.
 *
 * Exercise the real frontend against a live backend (mock LLM provider, throwaway
 * SQLite DB) through the browser. Each run registers a unique account so tests
 * are independent of prior state.
 */

function uniqueEmail() {
  return `e2e-${Date.now()}-${Math.floor(Math.random() * 1e6)}@nexusflow.test`;
}

/** Register a fresh account and land on the authenticated app shell. */
async function registerAccount(page: Page) {
  const email = uniqueEmail();
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible({ timeout: 20_000 });
  await page.getByRole("button", { name: "Create an account" }).click();
  await expect(page.getByRole("heading", { name: "Create your account" })).toBeVisible();
  await page.getByLabel("Your name").fill("E2E Tester");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.locator('input[type="password"]').fill("e2e-password-123");
  await page.getByRole("button", { name: "Create account" }).click();
  // The register flow does a full-page navigation and re-bootstraps auth via
  // /auth/me. Wait for the authenticated dashboard to render so auth is fully
  // settled before navigating further; otherwise the app-shell guard can bounce
  // a fresh navigation back to /login while /auth/me is still in flight.
  await expect(page).not.toHaveURL(/\/login/, { timeout: 20_000 });
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 20_000 });
  return email;
}

/** Create a project from the new-project form and return its id (from the URL).
 *
 * Navigates via the dashboard's in-app link rather than a full `goto` so the
 * already-bootstrapped auth session is kept alive (a fresh page load re-runs
 * the auth guard and can race a redirect back to login). */
async function createProject(page: Page, name: string): Promise<string> {
  await page.getByRole("link", { name: "New Project" }).click();
  await expect(page.getByLabel("Project Name")).toBeVisible({ timeout: 20_000 });
  await page.getByLabel("Project Name").fill(name);
  await page.getByLabel("Description").fill("End-to-end test project");
  await page
    .getByLabel("Your Idea")
    .fill("Build a predictive maintenance platform for manufacturing lines with explainable alerts.");
  await page.getByRole("button", { name: "Create Project" }).click();
  // Wait for the real project-detail URL. Exclude the form route (/projects/new)
  // so we capture the generated project id, not the literal "new".
  await expect(page).toHaveURL(/\/projects\/(?!new$)[^/]+$/, { timeout: 20_000 });
  const match = page.url().match(/\/projects\/([^/]+)$/);
  return match![1];
}

test("register, create a project, generate a brief, and reach the workflow", async ({ page }) => {
  await registerAccount(page);
  const projectId = await createProject(page, "E2E Maintenance Platform");

  await expect(page.getByText("E2E Maintenance Platform").first()).toBeVisible();

  // --- Generate the idea brief ---
  await page.getByRole("button", { name: /Generate Brief|Analyze with AI/ }).first().click();

  // The generated brief renders its sections (mock provider returns a brief).
  await expect(page.getByText("Idea Brief").first()).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("Problem Statement").first()).toBeVisible();

  // --- Reach the workflow ---
  await page.getByRole("link", { name: /Configure workflow|Open workflow/ }).first().click();
  await expect(page).toHaveURL(new RegExp(`/projects/${projectId}/workflow$`), { timeout: 20_000 });
});

test("full journey: brief -> single-stage workflow -> approval -> completion -> export", async ({ page }) => {
  await registerAccount(page);
  const projectId = await createProject(page, "E2E Full Journey");

  // --- Generate the idea brief (idea_discovery uses the saved brief). ---
  await page.getByRole("button", { name: /Generate Brief|Analyze with AI/ }).first().click();
  await expect(page.getByText("Idea Brief").first()).toBeVisible({ timeout: 30_000 });

  // --- Start a single-stage workflow (idea discovery) for a deterministic path. ---
  // Use the in-app link to keep the auth session alive.
  await page.getByRole("link", { name: /Configure workflow|Open workflow/ }).first().click();
  await expect(page).toHaveURL(new RegExp(`/projects/${projectId}/workflow$`), { timeout: 20_000 });
  await expect(page.getByRole("heading", { name: "Start the review workflow" })).toBeVisible({ timeout: 20_000 });

  // Deselect every stage except Idea discovery so the workflow completes in one approval.
  const stageCheckboxes = page.locator('fieldset input[type="checkbox"]');
  const count = await stageCheckboxes.count();
  for (let i = 0; i < count; i++) {
    const box = stageCheckboxes.nth(i);
    const label = box.locator("xpath=..");
    const text = (await label.innerText()).toLowerCase();
    const isIdeaDiscovery = text.includes("idea");
    if ((await box.isChecked()) !== isIdeaDiscovery) {
      await box.click();
    }
  }

  await page.getByRole("button", { name: "Start workflow" }).click();

  // --- Prepare the stage deliverable. ---
  await expect(page.getByRole("button", { name: /Prepare stage deliverable/ })).toBeVisible({ timeout: 20_000 });
  await page.getByRole("button", { name: /Prepare stage deliverable/ }).click();

  // Once prepared and checks pass, the approve button becomes enabled.
  const approve = page.getByRole("button", { name: /Approve and continue/ });
  await expect(approve).toBeEnabled({ timeout: 30_000 });
  await approve.click();

  // --- The single-stage workflow is now complete. ---
  await expect(page.getByText(/All workflow stages are approved|Workflow complete/).first()).toBeVisible({
    timeout: 30_000,
  });

  // --- Export the project package and confirm a ZIP is returned. ---
  // Navigate to artifacts via the in-app link shown on completion.
  await page.getByRole("link", { name: /Open artifacts|View artifacts/ }).first().click();
  await expect(page).toHaveURL(new RegExp(`/projects/${projectId}/artifacts$`), { timeout: 20_000 });
  const exportLink = page.getByRole("link", { name: /Export package/ });
  await expect(exportLink).toBeVisible({ timeout: 20_000 });

  const href = await exportLink.getAttribute("href");
  expect(href).toContain(`/projects/${projectId}/package/export`);

  // Fetch the export through the authenticated browser context and assert it is a ZIP.
  const token = await page.evaluate(() => window.localStorage.getItem("nexusflow.access_token"));
  const response = await page.request.get(href!, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  expect(response.ok()).toBeTruthy();
  const contentType = response.headers()["content-type"] ?? "";
  expect(contentType).toContain("zip");
});
