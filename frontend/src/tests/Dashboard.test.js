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

vi.mock('chart.js', () => ({
  Chart: { register: vi.fn() },
  CategoryScale: {},
  LinearScale: {},
  BarElement: {},
  PointElement: {},
  LineElement: {},
  Title: {},
  Tooltip: {},
  Legend: {},
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

const holdingsResponse = [
  { symbol: 'AAPL', trade_type: 'L', shares: 50, average_price: 180.00, profit_loss: 500.00, name: 'Apple Inc.' },
  { symbol: 'TSLA', trade_type: 'L', shares: 10, average_price: 220.00, profit_loss: -300.00, name: 'Tesla Inc.' },
];

function mockAllRequests() {
  axios.get.mockImplementation((url) => {
    if (url.includes('dashboard/summary'))       return Promise.resolve({ data: summaryResponse });
    if (url.includes('dashboard/pnl_over_time')) return Promise.resolve({ data: pnlResponse });
    if (url.includes('current_holdings_json'))   return Promise.resolve({ data: holdingsResponse });
    if (url.includes('get_stock_data'))          return Promise.resolve({ data: { currentPrice: 190.00 } });
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

  it('renders one holdings row per holding', async () => {
    mockAllRequests();
    const wrapper = mountDashboard();
    await flushPromises();
    const rows = wrapper.findAll('.dash-holdings-table tbody tr');
    expect(rows).toHaveLength(holdingsResponse.length);
  });

  it('shows a Get Price button for each holding initially', async () => {
    mockAllRequests();
    const wrapper = mountDashboard();
    await flushPromises();
    const buttons = wrapper.findAll('button').filter((b) => b.text() === 'Get Price');
    expect(buttons).toHaveLength(holdingsResponse.length);
  });

  it('calls the price API when Get Price is clicked', async () => {
    mockAllRequests();
    const wrapper = mountDashboard();
    await flushPromises();
    const btn = wrapper.findAll('button').find((b) => b.text() === 'Get Price');
    await btn.trigger('click');
    await flushPromises();
    expect(axios.get).toHaveBeenCalledWith(expect.stringContaining('get_stock_data/AAPL'));
  });

  it('replaces Get Price button with live price after fetch', async () => {
    mockAllRequests();
    const wrapper = mountDashboard();
    await flushPromises();
    const btn = wrapper.findAll('button').find((b) => b.text() === 'Get Price');
    await btn.trigger('click');
    await flushPromises();
    expect(wrapper.text()).toContain('$190.00');
    // Button for AAPL should be gone; one remaining for TSLA
    const remaining = wrapper.findAll('button').filter((b) => b.text() === 'Get Price');
    expect(remaining).toHaveLength(1);
  });

  it('renders by-symbol breakdown rows', async () => {
    mockAllRequests();
    const wrapper = mountDashboard();
    await flushPromises();
    const rows = wrapper.findAll('.dash-symbol-table tbody tr');
    expect(rows).toHaveLength(summaryResponse.by_symbol.length);
    expect(wrapper.text()).toContain('Apple Inc.');
    expect(wrapper.text()).toContain('75.0%');
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
    axios.get.mockImplementation((url) => {
      if (url.includes('dashboard/summary'))       return Promise.resolve({ data: summaryResponse });
      if (url.includes('dashboard/pnl_over_time')) return Promise.resolve({ data: pnlResponse });
      if (url.includes('current_holdings_json'))   return Promise.resolve({ data: [] });
      return Promise.reject(new Error(`Unmocked URL: ${url}`));
    });
    const wrapper = mountDashboard();
    await flushPromises();
    expect(wrapper.text()).toContain('No open holdings found');
  });
});
