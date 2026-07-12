import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import axios from 'axios';
import SymbolHistory from '@/views/SymbolHistory.vue';

vi.mock('axios');

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useRoute: () => ({ query: {}, params: {} }),
}));

const summaryResponse = {
  overall: {
    total_realized_pnl: 700.00,
    total_winning_trades: 6,
    total_losing_trades: 5,
    batting_average: 0.545,
    symbols_traded: 3,
  },
  by_symbol: [
    {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      combined: { winning_trades_count: 3, losing_trades_count: 1, batting_average: 0.75, profit_loss: 1200 },
    },
    {
      symbol: 'TSLA',
      name: 'Tesla Inc.',
      combined: { winning_trades_count: 2, losing_trades_count: 3, batting_average: 0.4, profit_loss: -500 },
    },
    {
      symbol: 'MSFT',
      name: 'Microsoft Corp.',
      combined: { winning_trades_count: 1, losing_trades_count: 1, batting_average: 0.5, profit_loss: 0 },
    },
  ],
};

const mountHistory = () =>
  mount(SymbolHistory, {
    global: { stubs: { 'router-link': { template: '<a><slot /></a>' } } },
  });

function firstColumnValues(wrapper) {
  return wrapper.findAll('tbody tr').map((row) => row.find('td').text());
}

describe('SymbolHistory', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    axios.get.mockResolvedValue({ data: summaryResponse });
  });

  it('renders the page title', async () => {
    const wrapper = mountHistory();
    await flushPromises();
    expect(wrapper.text()).toContain('By Symbol — Closed Trade History');
  });

  it('renders one row per symbol, sorted by P&L descending by default', async () => {
    const wrapper = mountHistory();
    await flushPromises();
    expect(firstColumnValues(wrapper)).toEqual(['AAPL', 'MSFT', 'TSLA']);
    expect(wrapper.text()).toContain('Apple Inc.');
    expect(wrapper.text()).toContain('75.0%');
  });

  it('sorts by symbol ascending when the Symbol header is clicked', async () => {
    const wrapper = mountHistory();
    await flushPromises();
    await wrapper.findAll('th')[0].trigger('click');
    expect(firstColumnValues(wrapper)).toEqual(['AAPL', 'MSFT', 'TSLA']);
    // Second click flips to descending
    await wrapper.findAll('th')[0].trigger('click');
    expect(firstColumnValues(wrapper)).toEqual(['TSLA', 'MSFT', 'AAPL']);
  });

  it('sorts numeric columns descending on first click', async () => {
    const wrapper = mountHistory();
    await flushPromises();
    // Column index 3 = Losses: TSLA(3), AAPL(1), MSFT(1)
    await wrapper.findAll('th')[3].trigger('click');
    expect(firstColumnValues(wrapper)[0]).toBe('TSLA');
  });

  it('shows a totals row summing wins, losses, and P&L', async () => {
    const wrapper = mountHistory();
    await flushPromises();
    const totalsRow = wrapper.find('tfoot .totals-row');
    expect(totalsRow.exists()).toBe(true);
    const cells = totalsRow.findAll('td').map((td) => td.text());
    expect(cells).toContain('6');        // total wins
    expect(cells).toContain('5');        // total losses
    expect(cells).toContain('54.5%');    // overall win rate (6 / 11)
    expect(cells).toContain('$700.00');  // total realized P&L
  });

  it('shows an error message when the fetch fails', async () => {
    axios.get.mockRejectedValueOnce(new Error('Server error'));
    const wrapper = mountHistory();
    await flushPromises();
    expect(wrapper.text()).toContain('Server error');
  });

  it('shows an empty message when there are no closed trades', async () => {
    axios.get.mockResolvedValueOnce({ data: { overall: {}, by_symbol: [] } });
    const wrapper = mountHistory();
    await flushPromises();
    expect(wrapper.text()).toContain('No closed trades yet.');
  });
});
