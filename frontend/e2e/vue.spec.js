import { test, expect } from '@playwright/test';

test('home page loads with title and search input', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/trading/i);
  await expect(page.locator('h1')).toContainText('Stock Trading App');
  await expect(page.locator('input[placeholder="Type to search..."]')).toBeVisible();
});

test('navigating to a trade symbol route shows the AllTrades view', async ({ page }) => {
  await page.goto('/trades/all/AAPL');
  // The loading spinner or trade data heading should appear
  await expect(page.locator('.all-trades')).toBeVisible();
});

test('404 route shows not found page', async ({ page }) => {
  await page.goto('/does-not-exist');
  await expect(page.locator('h1')).toContainText('404');
});
