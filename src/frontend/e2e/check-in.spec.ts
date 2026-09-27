import { expect, test } from '@playwright/test';

import { expectNoA11yViolations, signUp } from './helpers';

test.describe('spec 003 - Daily check-in @p1', () => {
  test('toggle today, persist, undo, backfill yesterday, add a note', async ({ page }) => {
    await signUp(page);
    await page.getByRole('link', { name: 'Habits' }).click();
    await page.getByLabel('Name', { exact: true }).fill('Read 10 pages');
    await page.getByRole('button', { name: 'Add habit' }).click();
    await expect(page.getByRole('heading', { name: 'Read 10 pages' })).toBeVisible();
    await page.getByRole('link', { name: 'Today', exact: true }).click();

    const habit = page.getByRole('button', { name: 'Read 10 pages', exact: true });
    await expect(habit).toHaveAttribute('aria-pressed', 'false');
    await habit.click();
    await expect(habit).toHaveAttribute('aria-pressed', 'true');
    await page.reload();
    await expect(habit).toHaveAttribute('aria-pressed', 'true');
    await expectNoA11yViolations(page);

    await page.getByRole('button', { name: 'Add note for Read 10 pages' }).click();
    await page.getByLabel('Note for Read 10 pages').fill('ran 5k in the rain');
    await page.getByRole('button', { name: 'Save note' }).click();
    await expect(page.getByText('ran 5k in the rain')).toBeVisible();

    await habit.click();
    await expect(habit).toHaveAttribute('aria-pressed', 'false');
    await page.reload();
    await expect(habit).toHaveAttribute('aria-pressed', 'false');

    const dayLoaded = page.waitForResponse(/\/api\/v1\/days\/\d{4}-\d{2}-\d{2}$/);
    await page.getByRole('button', { name: /Previous day/ }).click();
    await dayLoaded;
    await expect(page).toHaveURL(/\?date=\d{4}-\d{2}-\d{2}$/);
    await expect(habit).toBeEnabled();
    await habit.focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('alert')).toHaveCount(0);
    await expect(habit).toHaveAttribute('aria-pressed', 'true');
    await page.getByRole('link', { name: 'Jump to today' }).click();
    await expect(page.getByRole('heading', { name: 'Today', level: 1 })).toBeVisible();
    await expect(habit).toHaveAttribute('aria-pressed', 'false');
    await expect(page.getByRole('button', { name: /Next day/ })).toBeDisabled();
  });
});
