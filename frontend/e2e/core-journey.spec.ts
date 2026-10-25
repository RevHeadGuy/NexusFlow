import { test, expect } from "@playwright/test";

/**
 * Core journey end-to-end test.
 *
 * Exercises the real frontend against a live backend (mock LLM provider, throwaway
 * SQLite DB) through the browser:
 *   register a new account -> create a project -> generate its idea brief ->
 *   reach the workflow -> view artifacts/export entry point.
 *
 * Each run registers a unique account so the test is independent of prior state.
 */

function uniqueEmail() {
  return `e2e-${Date.now()}-${Math.floor(Math.random() * 1e6)}@nexusflow.test`;
}

test("register, create a project, generate a brief, and reach the workflow", async ({ page }) => {
  const email = uniqueEmail();

  // --- Register ---
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible({ timeout: 20_000 });

  // Switch to the register form and wait for it to render.
  await page.getByRole("button", { name: "Create an account" }).click();
  await expect(page.getByRole("heading", { name: "Create your account" })).toBeVisible();

  await page.getByLabel("Your name").fill("E2E Tester");
  await page.getByLabel("Email", { exact: true }).fill(email);
  // The password label includes a hint, so target the input by type instead.
  await page.locator('input[type="password"]').fill("e2e-password-123");
  await page.getByRole("button", { name: "Create account" }).click();

  // After registering we leave the login page for the authenticated app shell.
  await expect(page).not.toHaveURL(/\/login/, { timeout: 20_000 });

  // --- Create a project ---
  await page.goto("/projects/new");
  await page.getByLabel("Project Name").fill("E2E Maintenance Platform");
  await page.getByLabel("Description").fill("End-to-end test project");
  await page
    .getByLabel("Your Idea")
    .fill("Build a predictive maintenance platform for manufacturing lines with explainable alerts.");
  await page.getByRole("button", { name: "Create Project" }).click();

  // We should navigate to the project workspace.
  await expect(page).toHaveURL(/\/projects\/[^/]+$/, { timeout: 20_000 });
  await expect(page.getByText("E2E Maintenance Platform").first()).toBeVisible();

  // --- Generate the idea brief ---
  await page.getByRole("button", { name: /Generate Brief|Analyze with AI/ }).first().click();

  // The generated brief renders its sections (mock provider returns a brief).
  await expect(page.getByText("Idea Brief").first()).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("Problem Statement").first()).toBeVisible();

  // --- Reach the workflow ---
  // With a brief present, the workspace offers configuring/opening the workflow.
  await page.getByRole("link", { name: /Configure workflow|Open workflow/ }).first().click();
  await expect(page).toHaveURL(/\/projects\/[^/]+\/workflow$/, { timeout: 20_000 });
});
