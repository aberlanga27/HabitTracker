import { expect, test, type Page } from '@playwright/test';

import { expectNoA11yViolations, signUp } from './helpers';

async function goToDay(page: Page, action: RegExp): Promise<void> {
  const loaded = page.waitForResponse(/\/api\/v1\/days\/\d{4}-\d{2}-\d{2}$/);
  await page.getByRole('button', { name: action }).click();
  await loaded;
}

test.describe('spec 004 - Streak tracking @p1', () => {
  test('backfilled days build a streak; undo today keeps yesterday; detail shows longest', async ({
    page,
  }) => {
    await signUp(page);
    await page.getByRole('link', { name: 'Habits' }).click();
    await page.getByLabel('Name', { exact: true }).fill('Meditate');
    await page.getByRole('button', { name: 'Add habit' }).click();
    await expect(page.getByRole('heading', { name: 'Meditate' })).toBeVisible();
    await page.getByRole('link', { name: 'Today', exact: true }).click();

    const habit = page.getByRole('button', { name: 'Meditate', exact: true });
    await goToDay(page, /Previous day/);
    await goToDay(page, /Previous day/);
    await habit.click();
    await expect(habit).toHaveAttribute('aria-pressed', 'true');
    await goToDay(page, /Next day/);
    await habit.click();
    await expect(habit).toHaveAttribute('aria-pressed', 'true');
    await page.getByRole('link', { name: 'Jump to today' }).click();
    await habit.click();

    await expect(page.getByRole('img', { name: 'Current streak: 3 days' })).toBeVisible();
    await expectNoA11yViolations(page);

    await habit.click();
    await expect(habit).toHaveAttribute('aria-pressed', 'false');
    await expect(page.getByRole('img', { name: 'Current streak: 2 days' })).toBeVisible();

    await page.getByRole('link', { name: 'Habits' }).click();
    await page.getByRole('link', { name: 'Meditate' }).click();
    await expect(page.getByRole('heading', { name: 'Meditate', level: 1 })).toBeVisible();
    // Undo removed today's check-in, so the longest run is recomputed from what remains.
    await expect(page.getByRole('group', { name: 'Longest streak' })).toContainText('2 days');
    await expectNoA11yViolations(page);
  });
});
