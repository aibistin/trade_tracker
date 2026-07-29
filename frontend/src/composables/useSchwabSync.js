/**
 * useSchwabSync.js
 * Triggers a background Schwab sync (global, or scoped to one symbol) and
 * polls for completion. On success, notifies syncEvents so other
 * components can refetch their own data.
 */
import { ref } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '@/config.js'
import { emitSyncComplete } from './syncEvents.js'

const POLL_INTERVAL_MS = 2000

export function useSchwabSync(symbol = null) {
  const syncing = ref(false)
  const lastSyncedAt = ref(null)
  const lastResult = ref(null)
  const error = ref(null)
  let pollTimer = null

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  async function fetchLastSynced() {
    try {
      const params = symbol ? { symbol } : {}
      const { data } = await axios.get(`${API_BASE_URL}/schwab/sync/last`, { params })
      lastSyncedAt.value = data.last_synced_at
    } catch {
      lastSyncedAt.value = null
    }
  }

  function poll(jobId) {
    pollTimer = setInterval(async () => {
      try {
        const { data } = await axios.get(`${API_BASE_URL}/schwab/sync/${jobId}`)
        if (data.status === 'running') return

        stopPolling()
        syncing.value = false

        if (data.status === 'error') {
          error.value = data.error_message || 'Sync failed'
        } else {
          lastResult.value = { inserted: data.inserted, skippedExisting: data.skipped_existing }
          lastSyncedAt.value = data.finished_at
          emitSyncComplete(symbol)
        }
      } catch (e) {
        stopPolling()
        syncing.value = false
        error.value = e.message || 'Sync failed'
      }
    }, POLL_INTERVAL_MS)
  }

  async function triggerSync() {
    if (syncing.value) return
    syncing.value = true
    error.value = null
    lastResult.value = null
    try {
      const body = symbol ? { symbol } : {}
      const { data } = await axios.post(`${API_BASE_URL}/schwab/sync`, body)
      poll(data.job_id)
    } catch (e) {
      syncing.value = false
      error.value = e.message || 'Failed to start sync'
    }
  }

  return { syncing, lastSyncedAt, lastResult, error, triggerSync, fetchLastSynced, stopPolling }
}
