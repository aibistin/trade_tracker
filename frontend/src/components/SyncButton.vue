<template>
  <div class="sync-button">
    <button
      class="btn btn-outline-primary btn-sm sync-btn"
      :disabled="syncing"
      :title="symbol ? `Sync ${symbol} from Schwab` : 'Sync all trades from Schwab'"
      @click="triggerSync"
    >
      <span v-if="syncing" class="sync-spinner"></span>
      <span v-else class="sync-icon">&#x21bb;</span>
      {{ syncing ? 'Syncing…' : (symbol ? `Sync ${symbol}` : 'Sync') }}
    </button>
    <span v-if="statusText" class="sync-status" :class="{ 'sync-status-error': error }">
      {{ statusText }}
    </span>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { useSchwabSync } from '@/composables/useSchwabSync.js';

const props = defineProps({
  symbol: {
    type: String,
    default: null,
  },
});

const { syncing, lastSyncedAt, lastResult, error, triggerSync, fetchLastSynced, stopPolling } =
  useSchwabSync(() => props.symbol);

onMounted(fetchLastSynced);
// This component instance can be reused across symbol navigations (see
// useSchwabSync.js) — refetch so "Synced Xm ago" reflects the new symbol.
watch(() => props.symbol, fetchLastSynced);

// Shows the just-finished result ("Synced 3 new trades") briefly, then falls
// back to the persistent "Synced Xm ago" display.
const showResult = ref(false);
let resultTimer = null;

watch(lastResult, (result) => {
  if (!result) return;
  showResult.value = true;
  clearTimeout(resultTimer);
  resultTimer = setTimeout(() => { showResult.value = false; }, 5000);
});

// Ticks every 30s so "Synced Xm ago" stays current without user interaction.
const now = ref(Date.now());
const clockTimer = setInterval(() => { now.value = Date.now(); }, 30000);

onBeforeUnmount(() => {
  clearTimeout(resultTimer);
  clearInterval(clockTimer);
  stopPolling();
});

function formatTimeAgo(iso) {
  if (!iso) return 'Never synced';
  const diffMs = now.value - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'Synced just now';
  if (mins < 60) return `Synced ${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `Synced ${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `Synced ${days}d ago`;
}

const statusText = computed(() => {
  if (error.value) return error.value;
  if (showResult.value && lastResult.value) {
    const { inserted } = lastResult.value;
    return inserted > 0 ? `Synced ${inserted} new trade${inserted === 1 ? '' : 's'}` : 'Up to date';
  }
  return formatTimeAgo(lastSyncedAt.value);
});
</script>

<style scoped>
.sync-button {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sync-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.sync-icon {
  font-size: 0.85rem;
  line-height: 1;
}

.sync-spinner {
  display: inline-block;
  width: 10px;
  height: 10px;
  border: 2px solid var(--color-terminal-border);
  border-right-color: var(--color-accent-cyan);
  border-radius: 50%;
  animation: sync-spin 0.75s linear infinite;
}

@keyframes sync-spin {
  to { transform: rotate(360deg); }
}

.sync-status {
  font-size: 0.72rem;
  color: var(--color-terminal-text-muted);
  white-space: nowrap;
}

.sync-status-error {
  color: var(--color-loss);
}
</style>
