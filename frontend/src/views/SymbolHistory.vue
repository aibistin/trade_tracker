<template>
  <div class="history">
    <h3 class="page-title">By Symbol — Closed Trade History</h3>

    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border" role="status"></div>
      <p class="mt-2 text-muted">Loading trade history...</p>
    </div>
    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-else-if="rows.length > 0" class="history-section">
      <div class="history-section-header">
        <div>
          <h5 class="history-section-title">Realized Performance</h5>
          <p class="history-section-subtitle">
            Realized P&amp;L and win/loss stats for all closed trades. Click a column to sort.
          </p>
        </div>
      </div>
      <div class="table-responsive">
        <table class="table">
          <thead>
            <tr>
              <th v-for="col in columns" :key="col.key"
                class="sortable" :class="col.align"
                @click="sortBy(col.key)">
                {{ col.label }}
                <span class="sort-arrow">{{ sortArrow(col.key) }}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in sortedRows" :key="s.symbol">
              <td>
                <router-link :to="`/trades/closed/${s.symbol}`" class="symbol-link">{{ s.symbol }}</router-link>
              </td>
              <td class="text-muted text-sm">{{ s.name }}</td>
              <td class="text-end text-profit">{{ s.combined.winning_trades_count }}</td>
              <td class="text-end text-loss">{{ s.combined.losing_trades_count }}</td>
              <td class="text-end">{{ (s.combined.batting_average * 100).toFixed(1) }}%</td>
              <td class="text-end" :class="s.combined.profit_loss >= 0 ? 'text-profit' : 'text-loss'">
                {{ formatCurrency(s.combined.profit_loss) }}
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="totals-row">
              <td colspan="2" class="text-end">Totals</td>
              <td class="text-end text-profit">{{ totals.wins }}</td>
              <td class="text-end text-loss">{{ totals.losses }}</td>
              <td class="text-end">{{ (totals.winRate * 100).toFixed(1) }}%</td>
              <td class="text-end" :class="totals.pnl >= 0 ? 'text-profit' : 'text-loss'">
                {{ formatCurrency(totals.pnl) }}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <div v-else class="text-muted py-3">No closed trades yet.</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { formatCurrency } from '@/utils/tradeUtils.js'
import { API_BASE_URL } from '@/config.js'

const summary = ref(null)
const loading = ref(false)
const error = ref(null)

const columns = [
  { key: 'symbol', label: 'Symbol', align: '' },
  { key: 'name', label: 'Name', align: '' },
  { key: 'wins', label: 'Wins', align: 'text-end' },
  { key: 'losses', label: 'Losses', align: 'text-end' },
  { key: 'win_rate', label: 'Win Rate', align: 'text-end' },
  { key: 'pnl', label: 'Realized P/L', align: 'text-end' },
]

const columnValue = {
  symbol: (s) => s.symbol,
  name: (s) => s.name,
  wins: (s) => s.combined.winning_trades_count,
  losses: (s) => s.combined.losing_trades_count,
  win_rate: (s) => s.combined.batting_average,
  pnl: (s) => s.combined.profit_loss,
}

const sortKey = ref('pnl')
const sortDir = ref('desc')

function sortBy(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    // Text columns read best A→Z; numeric columns biggest-first
    sortDir.value = key === 'symbol' || key === 'name' ? 'asc' : 'desc'
  }
}

function sortArrow(key) {
  if (sortKey.value !== key) return ''
  return sortDir.value === 'asc' ? '▲' : '▼'
}

const rows = computed(() => summary.value?.by_symbol ?? [])

const sortedRows = computed(() => {
  const value = columnValue[sortKey.value]
  const dir = sortDir.value === 'asc' ? 1 : -1
  return [...rows.value].sort((a, b) => {
    const av = value(a)
    const bv = value(b)
    if (typeof av === 'string') return av.localeCompare(bv) * dir
    return (av - bv) * dir
  })
})

const totals = computed(() => {
  const wins = rows.value.reduce((sum, s) => sum + s.combined.winning_trades_count, 0)
  const losses = rows.value.reduce((sum, s) => sum + s.combined.losing_trades_count, 0)
  const pnl = rows.value.reduce((sum, s) => sum + s.combined.profit_loss, 0)
  const winRate = wins + losses > 0 ? wins / (wins + losses) : 0
  return { wins, losses, winRate, pnl }
})

onMounted(async () => {
  loading.value = true
  error.value = null
  try {
    const { data } = await axios.get(`${API_BASE_URL}/dashboard/summary`)
    summary.value = data
  } catch (e) {
    error.value = e.message || 'Failed to load trade history'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.history {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 20px;
  color: var(--color-terminal-text);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.history-section {
  background: var(--color-terminal-surface);
  border: 1px solid var(--color-terminal-border-subtle);
  border-radius: 6px;
  padding: 18px;
  margin-bottom: 20px;
}

.history-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  flex-wrap: wrap;
  gap: 8px;
}

.history-section-title {
  font-size: 0.85rem;
  font-weight: 600;
  margin: 0;
  color: var(--color-terminal-text);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.history-section-subtitle {
  font-size: 0.72rem;
  color: var(--color-terminal-text-muted);
  margin-top: 2px;
}

.symbol-link {
  font-weight: 600;
  color: var(--color-accent-cyan);
  text-decoration: none;
}

.symbol-link:hover {
  color: var(--color-accent-blue);
}

th.sortable {
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

th.sortable:hover {
  color: var(--color-accent-blue);
}

.sort-arrow {
  font-size: 0.55rem;
  display: inline-block;
  width: 0.8em;
}

.totals-row td {
  font-weight: 700;
  border-top: 2px solid var(--color-terminal-border);
  background: var(--color-terminal-panel);
  font-size: 0.8rem;
}

.text-sm { font-size: 0.75rem; }
.text-center { text-align: center; }
.py-4 { padding-top: 1rem; padding-bottom: 1rem; }
.py-3 { padding-top: 0.75rem; padding-bottom: 0.75rem; }
.mt-2 { margin-top: 0.5rem; }
</style>
