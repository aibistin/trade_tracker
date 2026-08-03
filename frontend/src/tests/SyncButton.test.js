import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { ref } from 'vue';
import SyncButton from '@/components/SyncButton.vue';

// Shared refs — same objects returned by every useSchwabSync() call, so
// tests can mutate them after mount and see the component react.
const mockSyncing = ref(false);
const mockLastSyncedAt = ref(null);
const mockLastResult = ref(null);
const mockError = ref(null);
const mockTriggerSync = vi.fn();
const mockFetchLastSynced = vi.fn();
const mockStopPolling = vi.fn();

vi.mock('@/composables/useSchwabSync.js', () => ({
  useSchwabSync: () => ({
    syncing: mockSyncing,
    lastSyncedAt: mockLastSyncedAt,
    lastResult: mockLastResult,
    error: mockError,
    triggerSync: mockTriggerSync,
    fetchLastSynced: mockFetchLastSynced,
    stopPolling: mockStopPolling,
  }),
}));

describe('SyncButton', () => {
  beforeEach(() => {
    mockSyncing.value = false;
    mockLastSyncedAt.value = null;
    mockLastResult.value = null;
    mockError.value = null;
    mockTriggerSync.mockReset();
    mockFetchLastSynced.mockReset();
    mockStopPolling.mockReset();
  });

  it('shows a generic "Sync" label with no symbol prop', () => {
    const wrapper = mount(SyncButton);
    expect(wrapper.find('button').text()).toContain('Sync');
    expect(wrapper.find('button').text()).not.toContain('Sync ');
  });

  it('shows a symbol-scoped label when a symbol prop is given', () => {
    const wrapper = mount(SyncButton, { props: { symbol: 'AAPL' } });
    expect(wrapper.find('button').text()).toContain('Sync AAPL');
  });

  it('calls fetchLastSynced on mount', () => {
    mount(SyncButton, { props: { symbol: 'AAPL' } });
    expect(mockFetchLastSynced).toHaveBeenCalledOnce();
  });

  it('refetches lastSynced when the symbol prop changes', async () => {
    // Regression test: AllTrades.vue's route reuses this component instance
    // across symbol navigations, so the display must refresh per-symbol.
    const wrapper = mount(SyncButton, { props: { symbol: 'AAPL' } });
    mockFetchLastSynced.mockClear();

    await wrapper.setProps({ symbol: 'MSFT' });

    expect(mockFetchLastSynced).toHaveBeenCalledOnce();
  });

  it('calls triggerSync when clicked', async () => {
    const wrapper = mount(SyncButton);
    await wrapper.find('button').trigger('click');
    expect(mockTriggerSync).toHaveBeenCalledOnce();
  });

  it('disables the button and shows "Syncing…" while a sync is in progress', async () => {
    mockSyncing.value = true;
    const wrapper = mount(SyncButton);
    await wrapper.vm.$nextTick();

    expect(wrapper.find('button').attributes('disabled')).toBeDefined();
    expect(wrapper.find('button').text()).toContain('Syncing…');
  });

  it('shows "Never synced" when nothing has synced yet', () => {
    const wrapper = mount(SyncButton);
    expect(wrapper.text()).toContain('Never synced');
  });

  it('shows a relative "Synced Xm ago" once a last-synced time is known', async () => {
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();
    mockLastSyncedAt.value = fiveMinutesAgo;
    const wrapper = mount(SyncButton);
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Synced 5m ago');
  });

  it('shows the result message right after a sync completes', async () => {
    const wrapper = mount(SyncButton);
    mockLastResult.value = { inserted: 3, skippedExisting: 1 };
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Synced 3 new trades');
  });

  it('shows "Up to date" when a sync completes with nothing new', async () => {
    const wrapper = mount(SyncButton);
    mockLastResult.value = { inserted: 0, skippedExisting: 4 };
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Up to date');
  });

  it('shows an error message styled distinctly when the sync fails', async () => {
    const wrapper = mount(SyncButton);
    mockError.value = 'Schwab login expired';
    await wrapper.vm.$nextTick();

    const status = wrapper.find('.sync-status');
    expect(status.text()).toBe('Schwab login expired');
    expect(status.classes()).toContain('sync-status-error');
  });

  it('calls stopPolling on unmount', () => {
    const wrapper = mount(SyncButton);
    wrapper.unmount();
    expect(mockStopPolling).toHaveBeenCalledOnce();
  });
});
