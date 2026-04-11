import { test, expect } from '@playwright/test';

/**
 * E2E tests for the TradeHome (Holdings) view at /home.
 * API responses are intercepted via Playwright route() so these tests
 * run without a live backend.
 */

// --- Mock data ---

const symbolsData = [
  ['AAPL', 'Apple Inc.'],
  ['MSFT', 'Microsoft Corp.'],
  ['TSLA', 'Tesla Inc.'],
  ['SPY', 'SPDR S&P 500'],
];

const holdingsData = [
  { symbol: 'AAPL', trade_type: 'L', shares: 100, average_price: 175.00, profit_loss: 1500.00, name: 'Apple Inc.' },
  { symbol: 'MSFT', trade_type: 'L', shares: 25, average_price: 400.00, profit_loss: -350.00, name: 'Microsoft Corp.' },
  { symbol: 'SPY', trade_type: 'C', shares: 10, average_price: 8.00, profit_loss: 200.00, name: 'SPDR S&P 500' },
  { symbol: 'TSLA', trade_type: 'P', shares: 3, average_price: 15.50, profit_loss: -120.00, name: 'Tesla Inc.' },
];

async function mockHomeAPIs(page) {
  await page.route('**/api/trade/symbols_json', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(symbolsData) })
  );
  await page.route('**/api/trade/current_holdings_json', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(holdingsData) })
  );
}

// --- Tests ---

test.describe('TradeHome Holdings page', () => {
  test.beforeEach(async ({ page }) => {
    await mockHomeAPIs(page);
  });

  test('loads the home page with title', async ({ page }) => {
    await page.goto('/home');
    await expect(page.locator('h1')).toContainText('Trade Tracker');
  });

  test('shows search input', async ({ page }) => {
    await page.goto('/home');
    await expect(page.locator('input[placeholder="Type to search..."]')).toBeVisible();
  });

  test('displays stock holdings table', async ({ page }) => {
    await page.goto('/home');

    // Wait for Stock Holdings section
    await expect(page.locator('text=Stock Holdings')).toBeVisible({ timeout: 10000 });

    // AAPL and MSFT are Long (trade_type L) — should appear under stocks
    await expect(page.locator('text=Apple Inc.')).toBeVisible();
    await expect(page.locator('text=Microsoft Corp.')).toBeVisible();
  });

  test('displays option holdings table', async ({ page }) => {
    await page.goto('/home');

    // Wait for Option Holdings section
    await expect(page.locator('text=Option Holdings')).toBeVisible({ timeout: 10000 });

    // SPY (Call) and TSLA (Put) should appear under options
    await expect(page.locator('td:has-text("SPY")')).toBeVisible();
    await expect(page.locator('td:has-text("TSLA")')).toBeVisible();
  });

  test('stock holdings shows correct share counts', async ({ page }) => {
    await page.goto('/home');
    await expect(page.locator('text=Stock Holdings')).toBeVisible({ timeout: 10000 });

    // AAPL should show 100 shares
    const aaplRow = page.locator('tr').filter({ hasText: 'Apple Inc.' });
    await expect(aaplRow.locator('td.text-end').first()).toContainText('100');
  });

  test('profit has profit coloring, loss has loss coloring', async ({ page }) => {
    await page.goto('/home');
    await expect(page.locator('text=Stock Holdings')).toBeVisible({ timeout: 10000 });

    // AAPL has positive P&L (1500) — should have text-profit class
    const aaplRow = page.locator('tr').filter({ hasText: 'Apple Inc.' });
    const aaplPnl = aaplRow.locator('.text-profit');
    await expect(aaplPnl).toBeVisible();

    // MSFT has negative P&L (-350) — should have text-loss class
    const msftRow = page.locator('tr').filter({ hasText: 'Microsoft Corp.' });
    const msftPnl = msftRow.locator('.text-loss');
    await expect(msftPnl).toBeVisible();
  });

  test('holdings filter toggle works', async ({ page }) => {
    await page.goto('/home');
    await expect(page.locator('text=Stock Holdings')).toBeVisible({ timeout: 10000 });

    // Click "Stocks" filter
    const stocksBtn = page.locator('button').filter({ hasText: 'Stocks' });
    await stocksBtn.click();

    // Stock Holdings should still be visible
    await expect(page.locator('text=Stock Holdings')).toBeVisible();
    // Option Holdings should be hidden
    await expect(page.locator('text=Option Holdings')).not.toBeVisible();

    // Click "Options" filter
    const optionsBtn = page.locator('button').filter({ hasText: 'Options' });
    await optionsBtn.click();

    // Option Holdings should now be visible
    await expect(page.locator('text=Option Holdings')).toBeVisible();
    // Stock Holdings should be hidden
    await expect(page.locator('text=Stock Holdings')).not.toBeVisible();

    // Click "All" to restore both
    const allBtn = page.locator('button').filter({ hasText: 'All' });
    await allBtn.click();
    await expect(page.locator('text=Stock Holdings')).toBeVisible();
    await expect(page.locator('text=Option Holdings')).toBeVisible();
  });

  test('symbol link navigates to trades view', async ({ page }) => {
    await page.goto('/home');
    await expect(page.locator('text=Stock Holdings')).toBeVisible({ timeout: 10000 });

    // Mock the trades endpoint for navigation
    await page.route('**/api/trades/**', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          stock_symbol: 'AAPL',
          transaction_stats: {
            stock: { has_trades: false, all_trades: [], summary: {} },
            option: { has_trades: false, all_trades: [], summary: {} },
          },
          requested: 'all_trades',
        }),
      })
    );

    // Click the AAPL link
    const aaplLink = page.locator('.symbol-link').filter({ hasText: 'AAPL' }).first();
    await aaplLink.click();

    // Should navigate to the AllTrades view
    await expect(page).toHaveURL(/\/trades\/all\/AAPL/);
  });

  test('shows loading state initially', async ({ page }) => {
    // Delay the API response to catch the loading state
    await page.route('**/api/trade/current_holdings_json', async route => {
      await new Promise(r => setTimeout(r, 500));
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(holdingsData) });
    });

    await page.goto('/home');

    // Loading spinner should appear briefly
    await expect(page.locator('text=Loading holdings...')).toBeVisible();

    // Then data should load
    await expect(page.locator('text=Stock Holdings')).toBeVisible({ timeout: 10000 });
  });

  test('shows error when API fails', async ({ page }) => {
    await page.route('**/api/trade/current_holdings_json', route =>
      route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: 'Server error' }) })
    );

    await page.goto('/home');

    // Should show error alert
    await expect(page.locator('.alert-danger')).toBeVisible({ timeout: 10000 });
  });

  test('handles empty holdings gracefully', async ({ page }) => {
    await page.route('**/api/trade/current_holdings_json', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    );

    await page.goto('/home');

    // Give it a moment to settle — no holdings tables should appear
    await page.waitForTimeout(1000);
    await expect(page.locator('text=Stock Holdings')).not.toBeVisible();
    await expect(page.locator('text=Option Holdings')).not.toBeVisible();
  });

  test('closed position should NOT appear in holdings list', async ({ page }) => {
    // Mock API returning only open positions (closed are excluded by backend)
    const openOnly = [
      { symbol: 'AAPL', trade_type: 'L', shares: 100, average_price: 175.00, profit_loss: 1500.00, name: 'Apple Inc.' },
    ];

    await page.route('**/api/trade/current_holdings_json', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(openOnly) })
    );

    await page.goto('/home');
    await expect(page.locator('text=Stock Holdings')).toBeVisible({ timeout: 10000 });

    // Only AAPL should appear
    await expect(page.locator('td:has-text("AAPL")')).toBeVisible();
    // Others should not appear
    await expect(page.locator('td:has-text("MSFT")')).not.toBeVisible();
    await expect(page.locator('td:has-text("TSLA")')).not.toBeVisible();
    await expect(page.locator('td:has-text("SPY")')).not.toBeVisible();
  });
});
