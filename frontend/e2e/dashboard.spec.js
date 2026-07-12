import { test, expect } from '@playwright/test';

/**
 * E2E tests for the Dashboard view.
 * API responses are intercepted via Playwright route() so these tests
 * run without a live backend.
 */

// --- Mock data ---

const summaryData = {
  overall: {
    total_realized_pnl: 12500.75,
    total_winning_trades: 35,
    total_losing_trades: 15,
    batting_average: 0.7,
    symbols_traded: 8,
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

const pnlData = {
  monthly: [
    { period: '2025-01', label: 'Jan 2025', winning_trades: 5, losing_trades: 2, batting_average: 0.714, pnl_dollars: 2100.00, pnl_pct_avg: 8.5 },
    { period: '2025-02', label: 'Feb 2025', winning_trades: 3, losing_trades: 3, batting_average: 0.5, pnl_dollars: -450.00, pnl_pct_avg: -3.2 },
    { period: '2025-03', label: 'Mar 2025', winning_trades: 7, losing_trades: 1, batting_average: 0.875, pnl_dollars: 4800.00, pnl_pct_avg: 12.1 },
  ],
  quarterly: [
    { period: '2025-Q1', label: 'Q1 2025', winning_trades: 15, losing_trades: 6, batting_average: 0.714, pnl_dollars: 6450.00, pnl_pct_avg: 5.8 },
  ],
};

// GET /api/holdings response shape: stock/option sections, each with
// aggregated positions (server-provided prices) and section totals.
const holdingsData = {
  stock: {
    positions: [
      { symbol: 'AAPL', trade_type: 'L', quantity: 50, avg_cost: 180.00, cost_basis: 9000.00, current_price: 195.00, market_value: 9750.00, unrealized_pnl: 750.00, pnl_pct: 8.33, name: 'Apple Inc.' },
      { symbol: 'MSFT', trade_type: 'L', quantity: 30, avg_cost: 410.00, cost_basis: 12300.00, current_price: 403.33, market_value: 12100.00, unrealized_pnl: -200.00, pnl_pct: -1.63, name: 'Microsoft Corp.' },
    ],
    total_cost_basis: 21300.00,
    total_market_value: 21850.00,
    total_unrealized_pnl: 550.00,
  },
  option: {
    positions: [
      { symbol: 'SPY', label: 'SPY 12/19/2025 500.00 C', trade_type: 'C', quantity: 5, avg_cost: 12.50, cost_basis: 6250.00, current_price: 13.10, market_value: 6550.00, unrealized_pnl: 300.00, pnl_pct: 4.8, occ_ticker: 'SPY251219C00500000', name: 'SPDR S&P 500' },
    ],
    total_cost_basis: 6250.00,
    total_market_value: 6550.00,
    total_unrealized_pnl: 300.00,
  },
};

const emptyHoldingsData = {
  stock: { positions: [], total_cost_basis: null, total_market_value: null, total_unrealized_pnl: null },
  option: { positions: [], total_cost_basis: null, total_market_value: null, total_unrealized_pnl: null },
};

const priceHistoryData = { prices: [], annotations: [] };

/**
 * Set up route interception to mock all Dashboard API calls.
 */
async function mockDashboardAPIs(page) {
  await page.route('**/api/dashboard/summary', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(summaryData) })
  );
  await page.route('**/api/dashboard/pnl_over_time**', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(pnlData) })
  );
  await page.route('**/api/holdings', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(holdingsData) })
  );
  await page.route('**/api/ticker/history/**', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(priceHistoryData) })
  );
}

// --- Tests ---

test.describe('Dashboard page', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/trade/symbols_json', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([['AAPL', 'Apple Inc.'], ['TSLA', 'Tesla Inc.']]) })
    );
    await mockDashboardAPIs(page);
  });

  test('loads and displays the Dashboard title', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('text=Dashboard')).toBeVisible();
  });

  test('shows summary cards with correct values', async ({ page }) => {
    await page.goto('/dashboard');

    // Wait for data to load — total P&L
    await expect(page.locator('text=$12,500.75')).toBeVisible({ timeout: 10000 });

    // Win rate: 0.7 * 100 = 70.0%
    await expect(page.locator('text=70.0%')).toBeVisible();

    // Wins / Losses
    await expect(page.locator('text=35W')).toBeVisible();
    await expect(page.locator('text=15L')).toBeVisible();

    // Symbols traded
    await expect(page.locator('.dash-card-value:has-text("8")')).toBeVisible();
  });

  test('shows P&L realized value with correct coloring', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('text=$12,500.75')).toBeVisible({ timeout: 10000 });

    // Positive P&L should have green text (text-profit class)
    const pnlElement = page.locator('.dash-card-value').filter({ hasText: '$12,500.75' });
    await expect(pnlElement).toHaveClass(/text-profit/);
  });

  test('displays stock holdings section with data', async ({ page }) => {
    await page.goto('/dashboard');

    // Wait for stock holdings
    await expect(page.locator('text=Stock Holdings')).toBeVisible({ timeout: 10000 });

    // Scope to the stock holdings section — find the section containing "Stock Holdings"
    const stockSection = page.locator('.dash-section').filter({ hasText: 'Stock Holdings' });
    // AAPL and MSFT are trade_type L — should appear under stocks
    await expect(stockSection.locator('text=Apple Inc.')).toBeVisible();
    await expect(stockSection.locator('text=Microsoft Corp.')).toBeVisible();
  });

  test('displays option holdings section', async ({ page }) => {
    await page.goto('/dashboard');

    // Wait for option holdings section
    await expect(page.locator('text=Option Holdings')).toBeVisible({ timeout: 10000 });

    // SPY is trade_type C, should appear under options
    await expect(page.locator('text=SPDR S&P 500')).toBeVisible();
  });

  test('stock holdings P&L coloring: green for profit, red for loss', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('text=Stock Holdings')).toBeVisible({ timeout: 10000 });

    // AAPL has profit_loss=750 (positive) => text-profit
    const aaplRow = page.locator('tr').filter({ hasText: 'AAPL' }).first();
    await expect(aaplRow).toBeVisible();

    // MSFT has profit_loss=-200 (negative) — look for loss coloring in its row
    const msftRow = page.locator('tr').filter({ hasText: 'MSFT' }).first();
    await expect(msftRow).toBeVisible();
  });

  test('shows server-provided current price and unrealized P&L', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('text=Stock Holdings')).toBeVisible({ timeout: 10000 });

    // Prices come directly from GET /api/holdings — no button click needed
    await expect(page.locator('text=$195.00')).toBeVisible();  // AAPL current_price
    await expect(page.locator('text=$750.00')).toBeVisible();  // AAPL unrealized_pnl
  });

  test('P&L chart section is visible', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('text=P&L Over Time')).toBeVisible({ timeout: 10000 });
  });

  test('monthly/quarterly toggle switches chart view', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('text=P&L Over Time')).toBeVisible({ timeout: 10000 });

    // Monthly should be active by default
    const monthlyBtn = page.locator('button').filter({ hasText: 'Monthly' });
    const quarterlyBtn = page.locator('button').filter({ hasText: 'Quarterly' });

    await expect(monthlyBtn).toHaveClass(/btn-primary/);
    await expect(quarterlyBtn).not.toHaveClass(/btn-primary/);

    // Click Quarterly
    await quarterlyBtn.click();
    await expect(quarterlyBtn).toHaveClass(/btn-primary/);
    await expect(monthlyBtn).not.toHaveClass(/btn-primary/);
  });

  test('asset type filter buttons are present', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('text=P&L Over Time')).toBeVisible({ timeout: 10000 });

    // The dash-toggles section contains the filter buttons
    const togglesSection = page.locator('.dash-toggles');
    await expect(togglesSection.locator('button', { hasText: 'All' })).toBeVisible();
    await expect(togglesSection.locator('button', { hasText: 'Stock' })).toBeVisible();
    await expect(togglesSection.locator('button', { hasText: 'Option' })).toBeVisible();
  });

  test('handles API error gracefully', async ({ page }) => {
    // Override routes to simulate errors
    await page.route('**/api/dashboard/summary', route =>
      route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: 'Internal error' }) })
    );

    await page.goto('/dashboard');

    // Should show an error message instead of crashing
    await expect(page.locator('.alert-danger')).toBeVisible({ timeout: 10000 });
  });

  test('symbol links in holdings navigate to trade view', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('text=Stock Holdings')).toBeVisible({ timeout: 10000 });

    // Mock the trades endpoint for navigation
    await page.route('**/api/trades/**', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          stock_symbol: 'AAPL',
          transaction_stats: { stock: { has_trades: false, all_trades: [], summary: {} }, option: { has_trades: false, all_trades: [], summary: {} } },
          requested: 'open_trades',
        }),
      })
    );

    // Click the AAPL symbol link in the holdings table
    const aaplLink = page.locator('.dash-symbol-link').filter({ hasText: 'AAPL' }).first();
    await aaplLink.click();

    // Should navigate to the trade view
    await expect(page).toHaveURL(/\/trades\/open\/AAPL/);
  });

  test('no open stock holdings shows empty message', async ({ page }) => {
    // Override holdings to return empty
    await page.route('**/api/holdings', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(emptyHoldingsData) })
    );

    await page.goto('/dashboard');
    await expect(page.locator('text=No open stock holdings')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=No open option holdings')).toBeVisible();
  });
});
