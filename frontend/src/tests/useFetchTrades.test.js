import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useFetchTrades } from '@/composables/useFetchTrades.js';
import axios from 'axios';

vi.mock('axios');

describe('useFetchTrades', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('returns initial state: data null, loading false, error null', () => {
    const { data, loading, error } = useFetchTrades();
    expect(data.value).toBeNull();
    expect(loading.value).toBe(false);
    expect(error.value).toBeNull();
  });

  it('sets loading true during fetch and false when done', async () => {
    axios.get.mockResolvedValueOnce({ data: [] });
    const { loading, fetchData } = useFetchTrades();

    const promise = fetchData('http://test/api');
    expect(loading.value).toBe(true);
    await promise;
    expect(loading.value).toBe(false);
  });

  it('populates data on success', async () => {
    const mockPayload = [['AAPL', 'Apple Inc.']];
    axios.get.mockResolvedValueOnce({ data: mockPayload });
    const { data, fetchData } = useFetchTrades();

    await fetchData('http://test/api/symbols');
    expect(data.value).toEqual(mockPayload);
  });

  it('sets error and clears data on failure', async () => {
    axios.get.mockRejectedValueOnce(new Error('Network Error'));
    const { data, error, fetchData } = useFetchTrades();

    await fetchData('http://test/api/fail');
    expect(error.value).toBe('Network Error');
    expect(data.value).toBeNull();
  });

  it('clears previous error at the start of a new fetch', async () => {
    axios.get.mockRejectedValueOnce(new Error('First error'));
    const { error, fetchData } = useFetchTrades();
    await fetchData('http://test/1');
    expect(error.value).toBe('First error');

    axios.get.mockResolvedValueOnce({ data: 'ok' });
    await fetchData('http://test/2');
    expect(error.value).toBeNull();
  });

  it('each useFetchTrades call returns independent state', async () => {
    axios.get.mockResolvedValueOnce({ data: 'first' });
    const { data: data1, fetchData: fetch1 } = useFetchTrades();
    const { data: data2 } = useFetchTrades();

    await fetch1('http://test/1');
    expect(data1.value).toBe('first');
    expect(data2.value).toBeNull();
  });
});
