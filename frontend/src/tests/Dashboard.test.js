import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import axios from 'axios';
import Dashboard from '@/views/Dashboard.vue';

vi.mock('axios');

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useRoute: () => ({ query: {}, params: {} }),
}));

// Stub chart components — jsdom has no canvas
vi.mock('vue-chartjs', () => ({
  Bar: { template: '<div class="stub-bar" />' },
  Line: { template: '<div class="stub-line" />' },
}));

vi.mock('chart.js', () => {
  function ChartMock() { this.destroy = vi.fn(); }
  ChartMock.register = vi.fn();
  return {
    Chart: ChartMock,
    CategoryScale: {},
    LinearScale: {},
    BarElement: {},
    PointElement: {},
    LineElement: {},
    Filler: {},
    Title: {},
    Tooltip: {},
    Legend: {},
  };
});

vi.mock('chartjs-chart-treemap', () => ({
  TreemapController: {},
  TreemapElement: {},
}));

// Stub canvas-based components that use new Chart() directly
vi.mock('@/components/PortfolioHeatmap.vue', () => ({
  default: { template: '<div class="stub-heatmap" />' },
}));

vi.mock('@/components/CumulativePnlChart.vue', () => ({
  default: { template: '<div class="stub-cumulative" />' },
}));

vi.mock('@/components/SparklineChart.vue', () => ({
  default: { template: '<div class="stub-sparkline" />' },
}));

const summaryResponse = {
  overall: {
    total_realized_pnl: 5000.00,
    total_winning_trades: 20,
    total_losing_trades: 10,
    batting_average: 0.667,
    symbols_traded: 5,
  },
  by_symbol: [
    {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      stock: { winning_trades_count: 3, losing_trades_count: 1, batting_average: 0.75, profit_loss: 1200 },
      option: null,
      combined: { winning_trades_count: 3, losing_trades_count: 1, batting_average: 0.75, profit_loss: 1200 },
    },
    {
      symbol: 'TSLA',
      name: 'Tesla Inc.',
      stock: { winning_trades_count: 2, losing_trades_count: 3, batting_average: 0.4, profit_loss: -500 },
      option: null,
      combined: { winning_trades_count: 2, losing_trades_count: 3, batting_average: 0.4, profit_loss: -500 },
    },
  ],
};

const pnlResponse = {
  monthly: [
    { period: '2024-01', label: 'Jan 2024', winning_trades: 3, losing_trades: 1, batting_average: 0.75, pnl_dollars: 850, pnl_pct_avg: 11.3 },
    { period: '2024-02', label: 'Feb 2024', winning_trades: 2, losing_trades: 2, batting_average: 0.5, pnl_dollars: -200, pnl_pct_avg: -4.1 },
  ],
  quarterly: [
    { period: '2024-Q1', label: 'Q1 2024', winning_trades: 5, losing_trades: 3, batting_average: 0.625, pnl_dollars: 650, pnl_pct_avg: 7.2 },
  ],
};

const holdingsResponse = {
  stock: {
    positions: [
      { symbol: 'AAPL', trade_type: 'L', quantity: 50, avg_cost: 180.00, cost_basis: 9000.00, current_price: null, market_value: null, unrealized_pnl: null, pnl_pct: null, name: 'Apple Inc.' },
      { symbol: 'TSLA', trade_type: 'L', quantity: 10, avg_cost: 220.00, cost_basis: 2200.00, current_price: null, market_value: null, unrealized_pnl: null, pnl_pct: null, name: 'Tesla Inc.' },
    ],
    total_cost_basis: 11200.00,
    total_market_value: null,
    total_unrealized_pnl: null,
  },
  option: {
    positions: [],
    total_cost_basis: null,
    total_market_value: null,
    total_unrealized_pnl: null,
  },
};

function mockAllRequests() {
  axios.get.mockImplementation((url) => {
    if (url.includes('dashboard/summary'))       return Promise.resolve({ data: summaryResponse });
    if (url.includes('dashboard/pnl_over_time')) return Promise.resolve({ data: pnlResponse });
    if (url.includes('/api/holdings'))           return Promise.resolve({ data: holdingsResponse });
    return Promise.reject(new Error(`Unmocked URL: ${url}`));
  });
}

const mountDashboard = () =>
  mount(Dashboard, {
    global: { stubs: { 'router-link': { template: '<a><slot /></a>' } } },
  });

describe('Dashboard', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders the page title', () => {
    mockAllRequests();
    const wrapper = mountDashboard();
    expect(wrapper.text()).toContain('Dashboard');
  });

  it('shows summary cards after data loads', async () => {
    mockAllRequests();
    const wrapper = mountDashboard();
    await flushPromises();
    expect(wrapper.text()).toContain('$5,000.00');   // total P&L
    expect(wrapper.text()).toContain('66.7%');        // win rate
    expect(wrapper.text()).toContain('20W');
    expect(wrapper.text()).toContain('10L');
    expect(wrapper.text()).toContain('5');            // symbols traded
  });

  it('renders one holdings row per stock position', async () => {
    mockAllRequests();
    const wrapper = mountDashboard();
    await flushPromises();
    // Stock holdings table is the first .table in the DOM
    const firstTable = wrapper.findAll('.table')[0];
    const rows = firstTable.findAll('tbody tr');
    expect(rows).toHaveLength(holdingsResponse.stock.positions.length);
  });

  it('shows cost basis for each stock position', async () => {
    mockAllRequests();
    const wrapper = mountDashboard();
    await flushPromises();
    expect(wrapper.text()).toContain('$9,000.00');
    expect(wrapper.text()).toContain('$2,200.00');
  });

  it('shows dash for current price when server provides null', async () => {
    mockAllRequests();
    const wrapper = mountDashboard();
    await flushPromises();
    // current_price is null in holdingsResponse — the price cell shows '--'
    const stockTable = wrapper.findAll('.table')[0];
    expect(stockTable.text()).toContain('--');
  });

  it('shows current price and unrealized P&L when provided by server', async () => {
    const holdingsWithPrice = {
      stock: {
        positions: [
          { symbol: 'AAPL', trade_type: 'L', quantity: 50, avg_cost: 180.00, cost_basis: 9000.00, current_price: 195.00, market_value: 9750.00, unrealized_pnl: 750.00, pnl_pct: 8.33, name: 'Apple Inc.' },
        ],
        total_cost_basis: 9000.00, total_market_value: 9750.00, total_unrealized_pnl: 750.00,
      },
      option: { positions: [], total_cost_basis: null, total_market_value: null, total_unrealized_pnl: null },
    };
    axios.get.mockImplementation((url) => {
      if (url.includes('dashboard/summary'))       return Promise.resolve({ data: summaryResponse });
      if (url.includes('dashboard/pnl_over_time')) return Promise.resolve({ data: pnlResponse });
      if (url.includes('/api/holdings'))           return Promise.resolve({ data: holdingsWithPrice });
      return Promise.reject(new Error(`Unmocked URL: ${url}`));
    });
    const wrapper = mountDashboard();
    await flushPromises();
    expect(wrapper.text()).toContain('$195.00');  // current_price
    expect(wrapper.text()).toContain('$750.00');  // unrealized_pnl
  });

  it('shows an error message when summary fetch fails', async () => {
    axios.get.mockImplementation((url) => {
      if (url.includes('dashboard/summary'))       return Promise.reject(new Error('Server error'));
      if (url.includes('dashboard/pnl_over_time')) return Promise.resolve({ data: pnlResponse });
      if (url.includes('current_holdings_json'))   return Promise.resolve({ data: holdingsResponse });
      return Promise.reject(new Error(`Unmocked URL: ${url}`));
    });
    const wrapper = mountDashboard();
    await flushPromises();
    expect(wrapper.text()).toContain('Server error');
  });

  it('shows an empty holdings message when there are no open positions', async () => {
    const emptyHoldings = {
      stock: { positions: [], total_cost_basis: null, total_market_value: null, total_unrealized_pnl: null },
      option: { positions: [], total_cost_basis: null, total_market_value: null, total_unrealized_pnl: null },
    };
    axios.get.mockImplementation((url) => {
      if (url.includes('dashboard/summary'))       return Promise.resolve({ data: summaryResponse });
      if (url.includes('dashboard/pnl_over_time')) return Promise.resolve({ data: pnlResponse });
      if (url.includes('/api/holdings'))           return Promise.resolve({ data: emptyHoldings });
      return Promise.reject(new Error(`Unmocked URL: ${url}`));
    });
    const wrapper = mountDashboard();
    await flushPromises();
    expect(wrapper.text()).toContain('No open stock holdings.');
  });
});
