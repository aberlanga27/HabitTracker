import { expect, test } from '@playwright/test';

import { expectNoA11yViolations, signUp } from './helpers';

test.describe('spec 002 - Habit management @p1', () => {
  test('create, persist, edit, archive/restore, reorder by keyboard, delete', async ({ page }) => {
    await signUp(page);
    await page.getByRole('link', { name: 'Create your first habit' }).click();
    await expect(page.getByRole('heading', { name: 'Habits', level: 1 })).toBeVisible();

    for (const name of ['Read 10 pages', 'Drink 2L of water', 'Stretch']) {
      await page.getByLabel('Name', { exact: true }).fill(name);
      await page.getByRole('button', { name: 'Add habit' }).click();
      await expect(page.getByRole('list', { name: 'Active habits' }).getByText(name)).toBeVisible();
    }
    await expectNoA11yViolations(page);

    await page.reload();
    const active = page.getByRole('list', { name: 'Active habits' });
    await expect(active.getByRole('heading')).toHaveText([
      'Read 10 pages',
      'Drink 2L of water',
      'Stretch',
    ]);

    // US2: edit
    await page.getByRole('button', { name: 'Edit Read 10 pages' }).click();
    await page.locator('#edit-name').fill('Read 20 pages');
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(active.getByRole('heading', { name: 'Read 20 pages' })).toBeVisible();

    // US5: keyboard reorder
    await page.getByRole('button', { name: 'Move Stretch up' }).focus();
    await page.keyboard.press('Enter');
    await expect(active.getByRole('heading')).toHaveText([
      'Read 20 pages',
      'Stretch',
      'Drink 2L of water',
    ]);
    await page.getByRole('button', { name: 'Move Stretch up' }).focus();
    await page.keyboard.press('Enter');
    await expect(active.getByRole('heading')).toHaveText([
      'Stretch',
      'Read 20 pages',
      'Drink 2L of water',
    ]);
    await page.reload();
    await expect(active.getByRole('heading').first()).toHaveText('Stretch');

    // US3: archive leaves Today, restore brings it back
    await page.getByRole('button', { name: 'Archive Stretch' }).click();
    const archived = page.getByRole('list', { name: 'Archived habits' });
    await expect(archived.getByText('Stretch')).toBeVisible();
    await page.getByRole('link', { name: 'Today' }).click();
    await expect(page.getByText('Read 20 pages')).toBeVisible();
    await expect(page.getByText('Stretch')).toHaveCount(0);
    await page.getByRole('link', { name: 'Habits' }).click();
    await page.getByRole('button', { name: 'Restore Stretch' }).click();
    await expect(active.getByRole('heading', { name: 'Stretch' })).toBeVisible();

    // US4: typed confirmation
    await page.getByRole('button', { name: 'Delete Drink 2L of water' }).click();
    const confirm = page.getByRole('button', { name: 'Delete permanently' });
    await expect(confirm).toBeDisabled();
    await page.getByLabel(/to confirm/).fill('Drink 2L of water');
    await confirm.click();
    await expect(active.getByRole('heading', { name: 'Drink 2L of water' })).toHaveCount(0);
    await expectNoA11yViolations(page);
  });
});
