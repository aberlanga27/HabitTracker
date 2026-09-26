import { AxeBuilder } from '@axe-core/playwright';
import { expect, type Page } from '@playwright/test';

export async function expectNoA11yViolations(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze();
  expect(results.violations).toEqual([]);
}

export function uniqueEmail(): string {
  return `ana+${Date.now()}${Math.floor(Math.random() * 1000)}@example.com`;
}

/** Register a fresh account through the UI and wait for the dashboard. */
export async function signUp(page: Page): Promise<string> {
  const email = uniqueEmail();
  await page.goto('/register');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill('twelve-chars');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page.getByRole('heading', { name: 'Today' })).toBeVisible();
  return email;
}
