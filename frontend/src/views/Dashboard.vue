<template>
  <div class="dashboard">
    <h3 class="dash-title">Dashboard</h3>

    <!-- Summary Cards -->
    <div v-if="summaryLoading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="mt-2">Loading summary…</p>
    </div>
    <div v-else-if="summaryError" class="alert alert-danger">{{ summaryError }}</div>
    <div v-else-if="summary" class="dash-cards">
      <div class="dash-card">
        <div class="dash-card-label">Realized P&amp;L</div>
        <div class="dash-card-value" :class="summary.overall.total_realized_pnl >= 0 ? 'text-success' : 'text-danger'">
          {{ formatCurrency(summary.overall.total_realized_pnl) }}
        </div>
      </div>
      <div class="dash-card">
        <div class="dash-card-label">Win Rate</div>
        <div class="dash-card-value">{{ (summary.overall.batting_average * 100).toFixed(1) }}%</div>
      </div>
      <div class="dash-card">
        <div class="dash-card-label">Wins / Losses</div>
        <div class="dash-card-value">
          <span class="text-success">{{ summary.overall.total_winning_trades }}W</span>
          <span class="text-muted"> / </span>
          <span class="text-danger">{{ summary.overall.total_losing_trades }}L</span>
        </div>
      </div>
      <div class="dash-card">
        <div class="dash-card-label">Symbols Traded</div>
        <div class="dash-card-value">{{ summary.overall.symbols_traded }}</div>
      </div>
    </div>

    <!-- P&L Over Time Chart -->
    <div class="dash-section">
      <div class="dash-section-header">
        <h5 class="dash-section-title">P&amp;L Over Time</h5>
        <div class="dash-toggles">
          <div class="btn-group btn-group-sm">
            <button class="btn" :class="chartView === 'monthly' ? 'btn-primary' : 'btn-outline-primary'"
              @click="chartView = 'monthly'">Monthly</button>
            <button class="btn" :class="chartView === 'quarterly' ? 'btn-primary' : 'btn-outline-primary'"
              @click="chartView = 'quarterly'">Quarterly</button>
          </div>
          <div class="btn-group btn-group-sm ms-2">
            <button v-for="t in assetTypeOptions" :key="t.value" class="btn"
              :class="assetTypeFilter === t.value ? 'btn-success' : 'btn-outline-success'"
              @click="setAssetType(t.value)">{{ t.label }}</button>
          </div>
        </div>
      </div>

      <div v-if="pnlLoading" class="text-center py-4">
        <div class="spinner-border text-success" role="status"></div>
      </div>
      <div v-else-if="pnlError" class="alert alert-danger">{{ pnlError }}</div>
      <div v-else-if="chartData" class="dash-chart-wrap">
        <Bar :data="chartData" :options="chartOptions" />
      </div>
    </div>

    <!-- Win Rate Trend Chart -->
    <div v-if="winRateData && !pnlLoading" class="dash-section">
      <div class="dash-section-header">
        <h5 class="dash-section-title">Win Rate Trend</h5>
      </div>
      <div class="dash-chart-wrap">
        <Line :data="winRateData" :options="winRateOptions" />
      </div>
    </div>

    <!-- Current Holdings -->
    <div class="dash-section">
      <h5 class="dash-section-title">Current Holdings</h5>
      <div v-if="holdingsLoading" class="text-center py-4">
        <div class="spinner-border text-warning" role="status"></div>
      </div>
      <div v-else-if="holdingsError" class="alert alert-danger">{{ holdingsError }}</div>
      <div v-else-if="holdings && holdings.length > 0" class="table-responsive">
        <table class="table table-sm table-hover dash-holdings-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Name</th>
              <th>Type</th>
              <th class="text-end">Shares</th>
              <th class="text-end">Avg Price</th>
              <th class="text-end">Cost Basis P/L</th>
              <th class="text-end">Live Price</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="h in holdings" :key="h.symbol + h.trade_type">
              <td>
                <router-link :to="`/trades/open/${h.symbol}`" class="dash-symbol-link">{{ h.symbol }}</router-link>
              </td>
              <td class="text-muted small">{{ h.name }}</td>
              <td><span class="dash-type-badge" :class="typeBadgeClass(h.trade_type)">{{ tradeTypeLabel(h.trade_type) }}</span></td>
              <td class="text-end">{{ h.shares }}</td>
              <td class="text-end">{{ formatCurrency(h.average_price) }}</td>
              <td class="text-end" :class="h.profit_loss >= 0 ? 'text-success' : 'text-danger'">
                {{ formatCurrency(h.profit_loss) }}
              </td>
              <td class="text-end">
                <span v-if="livePrices[h.symbol]?.loading" class="text-muted small">…</span>
                <span v-else-if="livePrices[h.symbol]?.price != null">
                  {{ formatCurrency(livePrices[h.symbol].price) }}
                </span>
                <button v-else class="btn btn-xs btn-outline-secondary" @click="loadLivePrice(h.symbol)">
                  Get Price
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="text-muted py-3">No open holdings found.</div>
    </div>

    <!-- By Symbol Breakdown -->
    <div v-if="summary && summary.by_symbol.length > 0" class="dash-section">
      <h5 class="dash-section-title">By Symbol</h5>
      <div class="table-responsive">
        <table class="table table-sm table-hover dash-symbol-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Name</th>
              <th class="text-end">Wins</th>
              <th class="text-end">Losses</th>
              <th class="text-end">Win Rate</th>
              <th class="text-end">Realized P/L</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in sortedBySymbol" :key="s.symbol">
              <td>
                <router-link :to="`/trades/closed/${s.symbol}`" class="dash-symbol-link">{{ s.symbol }}</router-link>
              </td>
              <td class="text-muted small">{{ s.name }}</td>
              <td class="text-end text-success">{{ s.combined.winning_trades_count }}</td>
              <td class="text-end text-danger">{{ s.combined.losing_trades_count }}</td>
              <td class="text-end">{{ (s.combined.batting_average * 100).toFixed(1) }}%</td>
              <td class="text-end" :class="s.combined.profit_loss >= 0 ? 'text-success' : 'text-danger'">
                {{ formatCurrency(s.combined.profit_loss) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement,
  PointElement, LineElement,
  Title, Tooltip, Legend
} from 'chart.js'
import { Bar, Line } from 'vue-chartjs'
import { formatCurrency } from '@/utils/tradeUtils.js'
import { API_BASE_URL } from '@/config.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend)

// ── State ────────────────────────────────────────────────────────────

const summary = ref(null)
const summaryLoading = ref(false)
const summaryError = ref(null)

const pnlData = ref(null)
const pnlLoading = ref(false)
const pnlError = ref(null)

const holdings = ref(null)
const holdingsLoading = ref(false)
const holdingsError = ref(null)

const chartView = ref('monthly')   // 'monthly' | 'quarterly'
const assetTypeFilter = ref('all') // 'all' | 'stock' | 'option'

// Per-holding live price cache: { [symbol]: { price, loading } }
const livePrices = ref({})

const assetTypeOptions = [
  { value: 'all', label: 'All' },
  { value: 'stock', label: 'Stock' },
  { value: 'option', label: 'Option' },
]

// ── Data Fetching ────────────────────────────────────────────────────

async function fetchSummary() {
  summaryLoading.value = true
  summaryError.value = null
  try {
    const { data } = await axios.get(`${API_BASE_URL}/dashboard/summary`)
    summary.value = data
  } catch (e) {
    summaryError.value = e.message || 'Failed to load summary'
  } finally {
    summaryLoading.value = false
  }
}

async function fetchPnlOverTime() {
  pnlLoading.value = true
  pnlError.value = null
  try {
    const { data } = await axios.get(`${API_BASE_URL}/dashboard/pnl_over_time?asset_type=${assetTypeFilter.value}`)
    pnlData.value = data
  } catch (e) {
    pnlError.value = e.message || 'Failed to load P&L data'
  } finally {
    pnlLoading.value = false
  }
}

async function fetchHoldings() {
  holdingsLoading.value = true
  holdingsError.value = null
  try {
    const { data } = await axios.get(`${API_BASE_URL}/trade/current_holdings_json`)
    holdings.value = data
  } catch (e) {
    holdingsError.value = e.message || 'Failed to load holdings'
  } finally {
    holdingsLoading.value = false
  }
}

async function loadLivePrice(symbol) {
  if (livePrices.value[symbol]?.price != null) return
  livePrices.value[symbol] = { price: null, loading: true }
  try {
    const { data } = await axios.get(`${API_BASE_URL}/get_stock_data/${symbol}`)
    const price = data?.currentPrice ?? data?.regularMarketPrice ?? null
    livePrices.value[symbol] = { price, loading: false }
  } catch {
    livePrices.value[symbol] = { price: null, loading: false }
  }
}

function setAssetType(val) {
  assetTypeFilter.value = val
  fetchPnlOverTime()
}

onMounted(() => {
  fetchSummary()
  fetchPnlOverTime()
  fetchHoldings()
})

// ── Chart Data ────────────────────────────────────────────────────────

const activeBuckets = computed(() => {
  if (!pnlData.value) return []
  return chartView.value === 'monthly' ? pnlData.value.monthly : pnlData.value.quarterly
})

const chartData = computed(() => {
  const buckets = activeBuckets.value
  if (!buckets.length) return null
  const labels = buckets.map(b => b.label)
  const pnlValues = buckets.map(b => b.pnl_dollars)
  return {
    labels,
    datasets: [
      {
        label: 'Realized P&L ($)',
        data: pnlValues,
        backgroundColor: pnlValues.map(v => v >= 0 ? 'rgba(25,135,84,0.75)' : 'rgba(220,53,69,0.75)'),
        borderColor: pnlValues.map(v => v >= 0 ? '#198754' : '#dc3545'),
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const val = ctx.parsed.y
          return ` ${val >= 0 ? '+' : ''}$${val.toFixed(2)}`
        },
      },
    },
  },
  scales: {
    y: {
      ticks: {
        callback: (v) => `$${v.toFixed(0)}`,
      },
    },
  },
}

const winRateData = computed(() => {
  const buckets = activeBuckets.value
  if (buckets.length < 2) return null
  return {
    labels: buckets.map(b => b.label),
    datasets: [
      {
        label: 'Win Rate (%)',
        data: buckets.map(b => +(b.batting_average * 100).toFixed(1)),
        borderColor: '#0d6efd',
        backgroundColor: 'rgba(13,110,253,0.1)',
        tension: 0.3,
        fill: true,
        pointRadius: 4,
      },
    ],
  }
})

const winRateOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: { label: (ctx) => ` ${ctx.parsed.y}%` },
    },
  },
  scales: {
    y: {
      min: 0,
      max: 100,
      ticks: { callback: (v) => `${v}%` },
    },
  },
}

// ── Computed Helpers ──────────────────────────────────────────────────

const sortedBySymbol = computed(() => {
  if (!summary.value) return []
  return [...summary.value.by_symbol].sort(
    (a, b) => b.combined.profit_loss - a.combined.profit_loss
  )
})

function tradeTypeLabel(code) {
  const map = { L: 'Long', S: 'Short', C: 'Call', P: 'Put', O: 'Other' }
  return map[code] ?? code
}

function typeBadgeClass(code) {
  const map = { L: 'badge-long', S: 'badge-short', C: 'badge-call', P: 'badge-put' }
  return map[code] ?? ''
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 20px;
}

.dash-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 20px;
  color: #212529;
}

/* ── Summary Cards ───────────────────────────────────────────── */
.dash-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}

.dash-card {
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 10px;
  padding: 18px 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}

.dash-card-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #6c757d;
  margin-bottom: 6px;
}

.dash-card-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #212529;
  font-variant-numeric: tabular-nums;
}

/* ── Sections ────────────────────────────────────────────────── */
.dash-section {
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}

.dash-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}

.dash-section-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  color: #212529;
}

.dash-toggles {
  display: flex;
  align-items: center;
}

.dash-chart-wrap {
  position: relative;
  height: 260px;
}

/* ── Holdings Table ──────────────────────────────────────────── */
.dash-holdings-table th,
.dash-symbol-table th {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6c757d;
  border-bottom-width: 1px;
}

.dash-symbol-link {
  font-weight: 600;
  color: #0d6efd;
  text-decoration: none;
}

.dash-symbol-link:hover {
  text-decoration: underline;
}

.dash-type-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 99px;
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: #e9ecef;
  color: #495057;
}

.badge-long { background: rgba(13,110,253,.15); color: #0a58ca; }
.badge-short { background: rgba(220,53,69,.15); color: #b02a37; }
.badge-call { background: rgba(25,135,84,.15); color: #146c43; }
.badge-put { background: rgba(253,126,20,.15); color: #ca6510; }

.btn-xs {
  padding: 1px 8px;
  font-size: 0.72rem;
}
</style>
