/**
 * usePriceHistory.js
 * Fetches price history for a symbol from the sparkline API.
 * Caches results in a module-level Map for the session.
 * Returns { history, annotations } for the SparklineChart component.
 */
import { ref } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '@/config.js'

const cache = new Map()

export function usePriceHistory() {
  const history = ref({})
  const loading = ref(false)

  async function fetchHistory(symbol, period = '3mo') {
    if (!symbol) return
    const cacheKey = `${symbol}:${period}`
    if (cache.has(cacheKey)) {
      history.value[symbol] = cache.get(cacheKey)
      return
    }

    loading.value = true
    try {
      const { data } = await axios.get(
        `${API_BASE_URL}/ticker/history/${symbol}?period=${period}`
      )
      const result = {
        prices: data.prices ?? [],
        // Backend returns 'trades' (buy/sell annotations); map to what SparklineChart expects
        annotations: data.trades ?? [],
      }
      cache.set(cacheKey, result)
      history.value[symbol] = result
    } catch {
      // Endpoint may not exist yet; silently skip
      history.value[symbol] = { prices: [], annotations: [] }
    } finally {
      loading.value = false
    }
  }

  async function fetchMultiple(symbols, period = '3mo') {
    const toFetch = symbols.filter(s => !history.value[s])
    for (let i = 0; i < toFetch.length; i += 3) {
      const batch = toFetch.slice(i, i + 3)
      await Promise.all(batch.map(s => fetchHistory(s, period)))
    }
  }

  return { history, loading, fetchHistory, fetchMultiple }
}
