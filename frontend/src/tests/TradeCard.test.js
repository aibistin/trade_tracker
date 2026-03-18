import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { ref } from 'vue';
import TradeCard from '@/components/TradeCard.vue';

vi.mock('axios');

// Shared refs — same objects returned by every useStockPrice() call
const mockPrice = ref(null);
const mockLoading = ref(false);
const mockFetchPrice = vi.fn();

vi.mock('@/composables/useStockPrice.js', () => ({
  useStockPrice: () => ({
    price: mockPrice,
    loading: mockLoading,
    error: ref(null),
    fetchPrice: mockFetchPrice,
  }),
}));

const makeTrade = (overrides = {}) => ({
  trade_id: 1,
  account: 'C',
  trade_type: 'L',
  action: 'B',
  trade_label: null,
  is_option: false,
  trade_date: '2024-01-15',
  price: 100.00,
  is_buy_trade: true,
  quantity: 10,
  amount: 1000.00,
  is_done: false,
  closed_date: null,
  current_sold_qty: 0,
  current_sold_amt: 0,
  current_profit_loss: 0,
  current_percent_profit_loss: 0,
  sells: [],
  reason: null,
  initial_stop_price: null,
  projected_sell_price: null,
  symbol: 'AAPL',
  ...overrides,
});

describe('TradeCard', () => {
  beforeEach(() => {
    mockFetchPrice.mockReset();
    mockPrice.value = null;
    mockLoading.value = false;
  });

  it('renders trade ID and account in collapsed state', () => {
    const wrapper = mount(TradeCard, { props: { trade: makeTrade() } });
    expect(wrapper.text()).toContain('1-C');
  });

  it('does not show detail panel before expand', () => {
    const wrapper = mount(TradeCard, { props: { trade: makeTrade() } });
    expect(wrapper.find('.tc-detail').exists()).toBe(false);
  });

  it('shows detail panel after clicking the row', async () => {
    const wrapper = mount(TradeCard, { props: { trade: makeTrade() } });
    await wrapper.find('.tc-row').trigger('click');
    expect(wrapper.find('.tc-detail').exists()).toBe(true);
  });

  it('collapses detail panel on second click', async () => {
    const wrapper = mount(TradeCard, { props: { trade: makeTrade() } });
    await wrapper.find('.tc-row').trigger('click');
    await wrapper.find('.tc-row').trigger('click');
    expect(wrapper.find('.tc-detail').exists()).toBe(false);
  });

  it('calls fetchPrice with symbol when expanding an open trade', async () => {
    const wrapper = mount(TradeCard, { props: { trade: makeTrade() } });
    await wrapper.find('.tc-row').trigger('click');
    expect(mockFetchPrice).toHaveBeenCalledOnce();
    expect(mockFetchPrice).toHaveBeenCalledWith('AAPL');
  });

  it('shows — when price is null and not loading', async () => {
    const wrapper = mount(TradeCard, { props: { trade: makeTrade() } });
    await wrapper.find('.tc-row').trigger('click');
    const metricsText = wrapper.find('.tc-metrics-bar').text();
    expect(metricsText).toContain('—');
  });

  it('shows loading indicator while fetching price', async () => {
    mockLoading.value = true;
    const wrapper = mount(TradeCard, { props: { trade: makeTrade() } });
    await wrapper.find('.tc-row').trigger('click');
    expect(wrapper.find('.tc-metrics-bar').text()).toContain('…');
  });

  it('shows live price once fetched', async () => {
    mockPrice.value = 125.50;
    const wrapper = mount(TradeCard, { props: { trade: makeTrade() } });
    await wrapper.find('.tc-row').trigger('click');
    expect(wrapper.find('.tc-metrics-bar').text()).toContain('$125.50');
  });

  it('does not call fetchPrice again if price is already loaded', async () => {
    const wrapper = mount(TradeCard, { props: { trade: makeTrade() } });
    await wrapper.find('.tc-row').trigger('click'); // expand — price null, fetchPrice called
    mockPrice.value = 110.00;                       // simulate fetch completing
    await wrapper.find('.tc-row').trigger('click'); // collapse
    await wrapper.find('.tc-row').trigger('click'); // re-expand — price not null, no second call
    expect(mockFetchPrice).toHaveBeenCalledTimes(1);
  });

  it('does not show live price section for closed trades', async () => {
    const trade = makeTrade({ is_done: true, closed_date: '2024-06-01', current_profit_loss: 250 });
    const wrapper = mount(TradeCard, { props: { trade } });
    await wrapper.find('.tc-row').trigger('click');
    // Live price metric is only shown when !trade.is_done
    const liveMetric = wrapper.findAll('.tc-metric').find(m => m.text().includes('Live Price'));
    expect(liveMetric).toBeUndefined();
  });

  it('does not call fetchPrice for closed trades', async () => {
    const trade = makeTrade({ is_done: true, closed_date: '2024-06-01', current_profit_loss: 250 });
    const wrapper = mount(TradeCard, { props: { trade } });
    await wrapper.find('.tc-row').trigger('click');
    expect(mockFetchPrice).not.toHaveBeenCalled();
  });

  it('shows W status pill for a winning closed trade', () => {
    const trade = makeTrade({ is_done: true, current_profit_loss: 300 });
    const wrapper = mount(TradeCard, { props: { trade } });
    expect(wrapper.find('.tc-status-pill').text()).toBe('W');
    expect(wrapper.find('.tc-win').exists()).toBe(true);
  });

  it('shows L status pill for a losing closed trade', () => {
    const trade = makeTrade({ is_done: true, current_profit_loss: -150 });
    const wrapper = mount(TradeCard, { props: { trade } });
    expect(wrapper.find('.tc-status-pill').text()).toBe('L');
    expect(wrapper.find('.tc-loss').exists()).toBe(true);
  });

  it('shows O status pill for an open trade', () => {
    const wrapper = mount(TradeCard, { props: { trade: makeTrade() } });
    expect(wrapper.find('.tc-status-pill').text()).toBe('O');
    expect(wrapper.find('.tc-open').exists()).toBe(true);
  });

  // Unrealized P&L
  it('shows unrealized P&L for a stock once live price is loaded', async () => {
    // trade: 10 shares bought at $100; live price $115 → unreal P&L = $150
    mockPrice.value = 115.00;
    const wrapper = mount(TradeCard, { props: { trade: makeTrade({ quantity: 10, price: 100 }) } });
    await wrapper.find('.tc-row').trigger('click');
    expect(wrapper.text()).toContain('$150.00');
  });

  it('shows unrealized P&L with est. label for an option', async () => {
    // option: qty 1 contract bought at $2.50 premium; live underlying $3.00 → (3-2.5)*1*100 = $50
    mockPrice.value = 3.00;
    const trade = makeTrade({ trade_type: 'C', quantity: 1, price: 2.50 });
    const wrapper = mount(TradeCard, { props: { trade } });
    await wrapper.find('.tc-row').trigger('click');
    expect(wrapper.text()).toContain('est.');
    expect(wrapper.text()).toContain('$50.00');
  });

  it('does not show unrealized P&L before live price is fetched', async () => {
    const wrapper = mount(TradeCard, { props: { trade: makeTrade() } });
    await wrapper.find('.tc-row').trigger('click');
    expect(wrapper.text()).not.toContain('Unreal.');
  });

  it('does not show unrealized P&L for closed trades', async () => {
    mockPrice.value = 125.00;
    const trade = makeTrade({ is_done: true, current_profit_loss: 300, closed_date: '2024-06-01' });
    const wrapper = mount(TradeCard, { props: { trade } });
    await wrapper.find('.tc-row').trigger('click');
    expect(wrapper.text()).not.toContain('Unreal.');
  });
});
