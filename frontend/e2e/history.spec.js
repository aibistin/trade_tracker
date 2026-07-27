import { test, expect } from '@playwright/test';

/**
 * E2E tests for the By Symbol — Closed Trade History view (/history).
 * API responses are intercepted via Playwright route() so these tests
 * run without a live backend.
 */

const summaryData = {
  overall: {
    total_realized_pnl: 2899.50,
    total_winning_trades: 10,
    total_losing_trades: 7,
    batting_average: 0.588,
    symbols_traded: 2,
  },
  by_symbol: [
    {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      stock: { winning_trades_count: 5, losing_trades_count: 2, batting_average: 0.714, profit_loss: 3200.00 },
      option: null,
      combined: { winning_trades_count: 5, losing_trades_count: 2, batting_average: 0.714, profit_loss: 3200.00 },
    },
    {
      symbol: 'TSLA',
      name: 'Tesla Inc.',
      stock: { winning_trades_count: 3, losing_trades_count: 4, batting_average: 0.429, profit_loss: -800.50 },
      option: { winning_trades_count: 2, losing_trades_count: 1, batting_average: 0.667, profit_loss: 500.00 },
      combined: { winning_trades_count: 5, losing_trades_count: 5, batting_average: 0.5, profit_loss: -300.50 },
    },
  ],
};

test.describe('Symbol History page', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/trade/symbols_json', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([['AAPL', 'Apple Inc.'], ['TSLA', 'Tesla Inc.']]) })
    );
    await page.route('**/api/dashboard/summary', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(summaryData) })
    );
  });

  test('loads via the History nav link', async ({ page }) => {
    await page.goto('/dashboard');
    await page.locator('.nav-link', { hasText: 'History' }).click();
    await expect(page).toHaveURL(/\/history/);
    await expect(page.locator('text=By Symbol — Closed Trade History')).toBeVisible({ timeout: 10000 });
  });

  test('renders all symbols sorted by P&L descending', async ({ page }) => {
    await page.goto('/history');
    await expect(page.locator('text=Realized Performance')).toBeVisible({ timeout: 10000 });

    await expect(page.locator('text=Apple Inc.')).toBeVisible();
    await expect(page.locator('text=Tesla Inc.')).toBeVisible();
    await expect(page.locator('text=71.4%')).toBeVisible();

    // AAPL (3200.00) should come before TSLA (-300.50) when sorted by P&L desc
    const firstSymbol = await page.locator('tbody tr').first().locator('td').first().textContent();
    expect(firstSymbol.trim()).toBe('AAPL');
  });

  test('clicking a column header re-sorts the table', async ({ page }) => {
    await page.goto('/history');
    await expect(page.locator('text=Realized Performance')).toBeVisible({ timeout: 10000 });

    // Losses descending: TSLA (5) before AAPL (2)
    await page.locator('th', { hasText: 'Losses' }).click();
    const firstSymbol = await page.locator('tbody tr').first().locator('td').first().textContent();
    expect(firstSymbol.trim()).toBe('TSLA');
  });

  test('shows a totals row with summed stats', async ({ page }) => {
    await page.goto('/history');
    await expect(page.locator('text=Realized Performance')).toBeVisible({ timeout: 10000 });

    const totalsRow = page.locator('tfoot .totals-row');
    await expect(totalsRow).toBeVisible();
    // Wins 10, losses 7, win rate 58.8%, total P&L 3200 - 300.50 = 2899.50
    await expect(totalsRow.locator('text=10')).toBeVisible();
    await expect(totalsRow.locator('text=7')).toBeVisible();
    await expect(totalsRow.locator('text=58.8%')).toBeVisible();
    await expect(totalsRow.locator('text=$2,899.50')).toBeVisible();
  });

  test('handles API error gracefully', async ({ page }) => {
    await page.route('**/api/dashboard/summary', route =>
      route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: 'Internal error' }) })
    );
    await page.goto('/history');
    await expect(page.locator('.alert-danger')).toBeVisible({ timeout: 10000 });
  });
});
