/**
 * useStockPrice.js
 * Fetches live stock price from the backend yfinance endpoint.
 * Caches results in a module-level Map for 5 minutes (session lifetime).
 */
import { ref } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '@/config.js'

const CACHE_TTL_MS = 5 * 60 * 1000
const cache = new Map() // { symbol -> { price, timestamp } }

export function useStockPrice() {
  const price = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchPrice(symbol) {
    if (!symbol) return

    const cached = cache.get(symbol)
    if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
      price.value = cached.price
      return
    }

    loading.value = true
    error.value = null
    try {
      const { data } = await axios.get(`${API_BASE_URL}/get_stock_data/${symbol}`)
      const livePrice = data?.currentPrice ?? data?.regularMarketPrice ?? null
      price.value = livePrice
      cache.set(symbol, { price: livePrice, timestamp: Date.now() })
    } catch (e) {
      error.value = e.message || 'Failed to fetch price'
    } finally {
      loading.value = false
    }
  }

  return { price, loading, error, fetchPrice }
}
