import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import { useSchwabSync } from '@/composables/useSchwabSync.js';
import { onSyncComplete } from '@/composables/syncEvents.js';

vi.mock('axios');

describe('useSchwabSync', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('starts with no sync in progress and nothing synced yet', () => {
    const { syncing, lastSyncedAt, lastResult, error } = useSchwabSync();
    expect(syncing.value).toBe(false);
    expect(lastSyncedAt.value).toBeNull();
    expect(lastResult.value).toBeNull();
    expect(error.value).toBeNull();
  });

  it('fetchLastSynced populates lastSyncedAt for the global scope', async () => {
    axios.get.mockResolvedValueOnce({ data: { last_synced_at: '2026-07-20T00:00:00+00:00' } });
    const { lastSyncedAt, fetchLastSynced } = useSchwabSync();

    await fetchLastSynced();

    expect(axios.get).toHaveBeenCalledWith(expect.stringContaining('/schwab/sync/last'), { params: {} });
    expect(lastSyncedAt.value).toBe('2026-07-20T00:00:00+00:00');
  });

  it('fetchLastSynced passes the symbol as a query param when scoped', async () => {
    axios.get.mockResolvedValueOnce({ data: { last_synced_at: null } });
    const { fetchLastSynced } = useSchwabSync(() => 'AAPL');

    await fetchLastSynced();

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/schwab/sync/last'),
      { params: { symbol: 'AAPL' } }
    );
  });

  it('triggerSync starts a job, polls until success, and updates state', async () => {
    axios.post.mockResolvedValueOnce({ data: { job_id: 42 } });
    axios.get
      .mockResolvedValueOnce({ data: { status: 'running' } })
      .mockResolvedValueOnce({
        data: {
          status: 'success', inserted: 3, skipped_existing: 1,
          finished_at: '2026-07-29T00:00:00+00:00',
        },
      });

    const { syncing, lastResult, lastSyncedAt, triggerSync } = useSchwabSync();

    await triggerSync();
    expect(syncing.value).toBe(true);

    await vi.advanceTimersByTimeAsync(2000); // first poll: still running
    expect(syncing.value).toBe(true);

    await vi.advanceTimersByTimeAsync(2000); // second poll: success
    expect(syncing.value).toBe(false);
    expect(lastResult.value).toEqual({ inserted: 3, skippedExisting: 1 });
    expect(lastSyncedAt.value).toBe('2026-07-29T00:00:00+00:00');
  });

  it('surfaces an error status from a failed job', async () => {
    axios.post.mockResolvedValueOnce({ data: { job_id: 5 } });
    axios.get.mockResolvedValueOnce({ data: { status: 'error', error_message: 'Schwab login expired' } });

    const { syncing, error, triggerSync } = useSchwabSync();
    await triggerSync();
    await vi.advanceTimersByTimeAsync(2000);

    expect(syncing.value).toBe(false);
    expect(error.value).toBe('Schwab login expired');
  });

  it('surfaces a failure to even start the job', async () => {
    axios.post.mockRejectedValueOnce(new Error('Network down'));

    const { syncing, error, triggerSync } = useSchwabSync();
    await triggerSync();

    expect(syncing.value).toBe(false);
    expect(error.value).toBe('Network down');
  });

  it('is a no-op while a sync is already in progress', async () => {
    axios.post.mockResolvedValueOnce({ data: { job_id: 1 } });
    axios.get.mockResolvedValue({ data: { status: 'running' } });

    const { triggerSync, stopPolling } = useSchwabSync();
    await triggerSync();
    await triggerSync(); // second call while syncing — must not POST again

    expect(axios.post).toHaveBeenCalledTimes(1);
    stopPolling();
  });

  it('stopPolling stops further status checks', async () => {
    axios.post.mockResolvedValueOnce({ data: { job_id: 9 } });
    axios.get.mockResolvedValue({ data: { status: 'running' } });

    const { triggerSync, stopPolling } = useSchwabSync();
    await triggerSync();
    stopPolling();

    const callsBefore = axios.get.mock.calls.length;
    await vi.advanceTimersByTimeAsync(5000);
    expect(axios.get.mock.calls.length).toBe(callsBefore);
  });

  it('emits sync-complete with the correct symbol on success', async () => {
    axios.post.mockResolvedValueOnce({ data: { job_id: 3 } });
    axios.get.mockResolvedValueOnce({
      data: {
        status: 'success', inserted: 0, skipped_existing: 0,
        finished_at: '2026-07-29T00:00:00+00:00',
      },
    });

    const received = [];
    const unsubscribe = onSyncComplete((symbol) => received.push(symbol));

    const { triggerSync } = useSchwabSync(() => 'MSFT');
    await triggerSync();
    await vi.advanceTimersByTimeAsync(2000);

    unsubscribe();
    expect(received).toEqual(['MSFT']);
  });

  it('always reads the current symbol, even if it changes between calls', async () => {
    // Regression test: AllTrades.vue's route (/trades/:scope/:stockSymbol)
    // reuses the same component instance across symbol navigations, so a
    // plain captured value would go stale. getSymbol must be re-invoked.
    let currentSymbol = 'HESM';
    axios.post.mockResolvedValueOnce({ data: { job_id: 7 } });
    axios.get.mockResolvedValueOnce({
      data: {
        status: 'success', inserted: 1, skipped_existing: 0,
        finished_at: '2026-08-03T00:00:00+00:00',
      },
    });

    const { triggerSync } = useSchwabSync(() => currentSymbol);
    currentSymbol = 'ORKA'; // simulate in-app navigation to a different symbol
    await triggerSync();

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/schwab/sync'),
      { symbol: 'ORKA' }
    );
  });
});
