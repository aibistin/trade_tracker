/**
 * useOptionPrice.js
 * Fetches live option price from the backend by passing the raw Schwab label.
 * The backend handles OCC ticker conversion. Caches by label for 5 minutes.
 */
import { ref } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '@/config.js'

const CACHE_TTL_MS = 5 * 60 * 1000
const cache = new Map() // { label -> { price, bid, ask, occ_ticker, timestamp } }

export function useOptionPrice() {
  const price = ref(null)
  const bid = ref(null)
  const ask = ref(null)
  const occTicker = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchPrice(label) {
    if (!label) return

    const cached = cache.get(label)
    if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
      price.value = cached.price
      bid.value = cached.bid
      ask.value = cached.ask
      occTicker.value = cached.occ_ticker
      return
    }

    loading.value = true
    error.value = null
    try {
      const { data } = await axios.get(`${API_BASE_URL}/option/price`, {
        params: { label },
      })
      price.value = data.price ?? null
      bid.value = data.bid ?? null
      ask.value = data.ask ?? null
      occTicker.value = data.occ_ticker ?? null
      cache.set(label, {
        price: price.value,
        bid: bid.value,
        ask: ask.value,
        occ_ticker: occTicker.value,
        timestamp: Date.now(),
      })
    } catch (e) {
      error.value = e.message || 'Failed to fetch option price'
    } finally {
      loading.value = false
    }
  }

  return { price, bid, ask, occTicker, loading, error, fetchPrice }
}
