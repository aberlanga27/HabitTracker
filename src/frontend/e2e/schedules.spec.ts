import { expect, test } from '@playwright/test';

import { expectNoA11yViolations, signUp } from './helpers';

const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

test.describe('spec 005 - Habit schedules @p1', () => {
  test('a specific-days habit shows only on its scheduled days', async ({ page }) => {
    const yesterday = DAY_NAMES[new Date(Date.now() - 86_400_000).getDay()] ?? 'Monday';
    await signUp(page);
    await page.getByRole('link', { name: 'Habits' }).click();

    await page.getByLabel('Name', { exact: true }).fill('Daily walk');
    await page.getByRole('button', { name: 'Add habit' }).click();
    const active = page.getByRole('list', { name: 'Active habits' });
    await expect(active.getByText('Every day')).toBeVisible();

    await page.getByLabel('Name', { exact: true }).fill('Gym');
    await page.getByRole('radio', { name: 'Specific days' }).check();
    await page.getByRole('button', { name: 'Add habit' }).click();
    await expect(page.getByText('Choose at least one day.')).toBeVisible();

    await page
      .getByRole('group', { name: 'Days' })
      .getByRole('checkbox', { name: yesterday })
      .check();
    await page.getByRole('button', { name: 'Add habit' }).click();
    await expect(active.getByRole('heading', { name: 'Gym' })).toBeVisible();
    await expectNoA11yViolations(page);

    await page.getByRole('link', { name: 'Today', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Daily walk', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Gym', exact: true })).toHaveCount(0);

    await page.getByRole('button', { name: /Previous day/ }).click();
    await expect(page.getByRole('button', { name: 'Gym', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Daily walk', exact: true })).toBeVisible();
    await expectNoA11yViolations(page);
  });
});
