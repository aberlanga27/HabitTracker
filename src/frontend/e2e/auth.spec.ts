import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

async function expectNoA11yViolations(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze();
  expect(results.violations).toEqual([]);
}

function uniqueEmail(): string {
  return `ana+${Date.now()}${Math.floor(Math.random() * 1000)}@example.com`;
}

test.describe('spec 001 - User accounts @p1', () => {
  test('US1+US2+US3: register lands on dashboard, survives reload, sign out protects pages', async ({
    page,
  }) => {
    const email = uniqueEmail();
    await page.goto('/');
    await expect(page).toHaveURL(/\/sign-in\?next=%2F$/);
    await expectNoA11yViolations(page);

    await page.getByRole('link', { name: 'Create an account' }).click();
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Password').fill('twelve-chars');
    await page.getByRole('button', { name: 'Create account' }).click();

    await expect(page.getByRole('heading', { name: 'Today' })).toBeVisible();
    await expect(page.getByText(email)).toBeVisible();
    await expectNoA11yViolations(page);

    await page.reload();
    await expect(page.getByText(email)).toBeVisible();

    await page.getByRole('button', { name: 'Sign out' }).click();
    await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
    await page.goto('/');
    await expect(page).toHaveURL(/\/sign-in/);
  });

  test('US2-S2: wrong password shows a generic error', async ({ page }) => {
    await page.goto('/sign-in');
    await page.getByLabel('Email').fill('nobody@example.com');
    await page.getByLabel('Password').fill('wrong-password');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('alert')).toHaveText('Invalid email or password');
  });

  test('keyboard only: register and sign out without a pointer', async ({ page }) => {
    await page.goto('/register');
    await page.keyboard.press('Tab');
    await expect(page.getByLabel('Email')).toBeFocused();
    await page.keyboard.type(uniqueEmail());
    await page.keyboard.press('Tab');
    await page.keyboard.type('twelve-chars');
    await page.keyboard.press('Enter');
    await expect(page.getByRole('heading', { name: 'Today' })).toBeVisible();

    const signOut = page.getByRole('button', { name: 'Sign out' });
    for (
      let i = 0;
      i < 5 && !(await signOut.evaluate((el) => el === document.activeElement));
      i++
    ) {
      await page.keyboard.press('Tab');
    }
    await expect(signOut).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
  });
});
