import { expect, test } from '@playwright/test';

import { expectNoA11yViolations, signUp } from './helpers';

test.describe('spec 006 - Today dashboard @p1', () => {
  test('empty state, progress, keyboard check-ins, all done', async ({ page }) => {
    await signUp(page);
    await expect(page.getByRole('link', { name: 'Create your first habit' })).toBeVisible();
    await expectNoA11yViolations(page);

    await page.getByRole('link', { name: 'Create your first habit' }).click();
    for (const name of ['Read', 'Walk']) {
      await page.getByLabel('Name', { exact: true }).fill(name);
      await page.getByRole('button', { name: 'Add habit' }).click();
      await expect(page.getByRole('heading', { name })).toBeVisible();
    }
    await page.getByRole('link', { name: 'Today', exact: true }).click();

    await expect(page.getByText('0 of 2 habits done')).toBeVisible();
    await expect(page.getByRole('progressbar', { name: 'Daily progress' })).toHaveAttribute(
      'aria-valuenow',
      '0',
    );

    const read = page.getByRole('button', { name: 'Read', exact: true });
    for (let i = 0; i < 12 && !(await read.evaluate((el) => el === document.activeElement)); i++) {
      await page.keyboard.press('Tab');
    }
    await expect(read).toBeFocused();
    await page.keyboard.press('Space');
    await expect(page.getByText('1 of 2 habits done')).toBeVisible();
    await expect(
      page.getByRole('list', { name: 'Done' }).getByRole('button', { name: 'Read', exact: true }),
    ).toBeVisible();

    await page.getByRole('button', { name: 'Walk', exact: true }).focus();
    await page.keyboard.press('Enter');
    await expect(page.getByText('All done for today!')).toBeVisible();
    await expect(page.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');
    await expectNoA11yViolations(page);
  });
});
