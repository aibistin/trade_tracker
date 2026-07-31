<template>
  <div class="dashboard">
    <h3 class="dash-title">Dashboard</h3>

    <!-- Summary Cards -->
    <div v-if="summaryLoading" class="text-center py-4">
      <div class="spinner-border" role="status"></div>
      <p class="mt-2 text-muted">Loading summary...</p>
    </div>
    <div v-else-if="summaryError" class="alert alert-danger">{{ summaryError }}</div>
    <div v-else-if="summary" class="dash-cards">
      <div class="dash-card">
        <div class="dash-card-label">Realized P&amp;L</div>
        <div class="dash-card-value" :class="summary.overall.total_realized_pnl >= 0 ? 'text-profit' : 'text-loss'">
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
          <span class="text-profit">{{ summary.overall.total_winning_trades }}W</span>
          <span class="text-dim"> / </span>
          <span class="text-loss">{{ summary.overall.total_losing_trades }}L</span>
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
          <button class="btn btn-xs btn-outline-secondary" @click="showPnlChart = !showPnlChart">
            {{ showPnlChart ? '▲ Hide' : '▼ Show' }}
          </button>
          <div class="btn-group btn-group-sm">
            <button class="btn" :class="chartView === 'monthly' ? 'btn-primary' : 'btn-outline-primary'"
              @click="chartView = 'monthly'">Monthly</button>
            <button class="btn" :class="chartView === 'quarterly' ? 'btn-primary' : 'btn-outline-primary'"
              @click="chartView = 'quarterly'">Quarterly</button>
          </div>
          <div class="btn-group btn-group-sm ml-2">
            <button v-for="t in assetTypeOptions" :key="t.value" class="btn"
              :class="assetTypeFilter === t.value ? 'btn-success' : 'btn-outline-success'"
              @click="setAssetType(t.value)">{{ t.label }}</button>
          </div>
        </div>
      </div>

      <template v-if="showPnlChart">
        <div v-if="pnlLoading" class="text-center py-4">
          <div class="spinner-border" role="status"></div>
        </div>
        <div v-else-if="pnlError" class="alert alert-danger">{{ pnlError }}</div>
        <div v-else-if="chartData" class="dash-chart-wrap">
          <Bar :data="chartData" :options="chartOptions" />
        </div>
      </template>
    </div>

    <!-- Cumulative P&L Line Chart -->
    <div v-if="activeBuckets.length > 1 && !pnlLoading" class="dash-section">
      <div class="dash-section-header">
        <h5 class="dash-section-title">Cumulative P&amp;L</h5>
        <button class="btn btn-xs btn-outline-secondary" @click="showCumChart = !showCumChart">
          {{ showCumChart ? '▲ Hide' : '▼ Show' }}
        </button>
      </div>
      <CumulativePnlChart v-if="showCumChart" :buckets="activeBuckets" />
    </div>

    <!-- Win Rate Trend Chart -->
    <div v-if="winRateData && !pnlLoading" class="dash-section">
      <div class="dash-section-header">
        <h5 class="dash-section-title">Win Rate Trend</h5>
        <button class="btn btn-xs btn-outline-secondary" @click="showWinChart = !showWinChart">
          {{ showWinChart ? '▲ Hide' : '▼ Show' }}
        </button>
      </div>
      <div v-if="showWinChart" class="dash-chart-wrap">
        <Line :data="winRateData" :options="winRateOptions" />
      </div>
    </div>

    <!-- Portfolio Heatmap -->
    <div v-if="!holdingsLoading && heatmapPositions.length > 0" class="dash-section">
      <div class="dash-section-header">
        <h5 class="dash-section-title">Portfolio Heatmap</h5>
      </div>
      <PortfolioHeatmap :holdings="heatmapPositions" :livePrices="heatmapPrices" />
    </div>

    <!-- Stock Holdings Panel -->
    <div class="dash-section">
      <div class="dash-section-header">
        <h5 class="dash-section-title">Stock Holdings</h5>
      </div>
      <div v-if="holdingsLoading" class="text-center py-4">
        <div class="spinner-border" role="status"></div>
      </div>
      <div v-else-if="holdingsError" class="alert alert-danger">{{ holdingsError }}</div>
      <div v-else-if="stockPositions.length > 0" class="table-responsive">
        <table class="table holdings-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Chart</th>
              <th>Name</th>
              <th>Type</th>
              <th class="text-end">Shares</th>
              <th class="text-end">Avg Cost</th>
              <th class="text-end">Cost Basis</th>
              <th class="text-end">Current Price</th>
              <th class="text-end">Mkt Value</th>
              <th class="text-end">Unreal. P&amp;L</th>
              <th class="text-end">P&amp;L %</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in stockPositions" :key="p.symbol + p.trade_type">
              <td>
                <router-link :to="`/trades/open/${p.symbol}`" class="dash-symbol-link">{{ p.symbol }}</router-link>
              </td>
              <td class="sparkline-cell">
                <SparklineChart
                  :priceData="priceHistory[p.symbol]?.prices ?? []"
                  :annotations="priceHistory[p.symbol]?.annotations ?? []"
                  :width="120" :height="32"
                />
              </td>
              <td class="text-muted text-sm">{{ p.name }}</td>
              <td><span class="type-badge" :class="typeBadgeClass(p.trade_type)">{{ tradeTypeLabel(p.trade_type) }}</span></td>
              <td class="text-end">{{ Number(p.quantity).toFixed(2) }}</td>
              <td class="text-end">{{ formatCurrency(p.avg_cost) }}</td>
              <td class="text-end">{{ formatCurrency(p.cost_basis) }}</td>
              <td class="text-end">
                <span v-if="p.current_price != null"
                  :class="p.current_price >= p.avg_cost ? 'text-profit' : 'text-loss'">
                  {{ formatCurrency(p.current_price) }}
                </span>
                <span v-else class="text-muted">--</span>
              </td>
              <td class="text-end">
                <span v-if="p.market_value != null" :class="(p.unrealized_pnl ?? 0) >= 0 ? 'text-profit' : 'text-loss'">
                  {{ formatCurrency(p.market_value) }}
                </span>
                <span v-else class="text-muted">--</span>
              </td>
              <td class="text-end">
                <span v-if="p.unrealized_pnl != null" :class="p.unrealized_pnl >= 0 ? 'text-profit' : 'text-loss'">
                  {{ formatCurrency(p.unrealized_pnl) }}
                </span>
                <span v-else class="text-muted">--</span>
              </td>
              <td class="text-end">
                <span v-if="p.pnl_pct != null" :class="p.pnl_pct >= 0 ? 'text-profit' : 'text-loss'">
                  {{ p.pnl_pct.toFixed(2) }}%
                </span>
                <span v-else class="text-muted">--</span>
              </td>
            </tr>
          </tbody>
          <tfoot v-if="holdingsData?.stock?.total_cost_basis != null">
            <tr class="totals-row">
              <td colspan="6" class="text-end">Totals</td>
              <td class="text-end">{{ formatCurrency(holdingsData.stock.total_cost_basis) }}</td>
              <td></td>
              <td class="text-end" :class="(holdingsData.stock.total_unrealized_pnl ?? 0) >= 0 ? 'text-profit' : 'text-loss'">
                {{ holdingsData.stock.total_market_value != null ? formatCurrency(holdingsData.stock.total_market_value) : '--' }}
              </td>
              <td class="text-end" :class="(holdingsData.stock.total_unrealized_pnl ?? 0) >= 0 ? 'text-profit' : 'text-loss'">
                {{ holdingsData.stock.total_unrealized_pnl != null ? formatCurrency(holdingsData.stock.total_unrealized_pnl) : '--' }}
              </td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>
      <div v-else-if="!holdingsLoading && !holdingsError" class="text-muted py-3">No open stock holdings.</div>
    </div>

    <!-- Option Holdings Panel -->
    <div class="dash-section">
      <div class="dash-section-header">
        <h5 class="dash-section-title">Option Holdings</h5>
      </div>
      <div v-if="holdingsLoading" class="text-center py-4">
        <div class="spinner-border" role="status"></div>
      </div>
      <div v-else-if="holdingsError" class="alert alert-danger">{{ holdingsError }}</div>
      <div v-else-if="optionPositions.length > 0" class="table-responsive">
        <table class="table holdings-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Chart</th>
              <th>Name</th>
              <th>Type</th>
              <th class="text-end">Contracts</th>
              <th class="text-end">Avg Cost</th>
              <th class="text-end">Cost Basis</th>
              <th class="text-end">Current Price</th>
              <th class="text-end">Mkt Value</th>
              <th class="text-end">Unreal. P&amp;L</th>
              <th class="text-end">P&amp;L %</th>
            </tr>
          </thead>
          <tbody>
            <!-- One parent row per underlying symbol, expandable to show individual contracts -->
            <!-- Columns: Symbol | Chart | Name | Type | Contracts | Avg Cost | Cost Basis | Current Price | Mkt Value | Unreal P&L | P&L% -->
            <template v-for="group in groupedOptions" :key="group.symbol">
              <tr @click="toggleOptionDetail(group.symbol)" class="option-row">
                <td>
                  <span class="expand-icon">{{ expandedOptions.has(group.symbol) ? '▼' : '▶' }}</span>
                  <router-link :to="`/trades/open/${group.symbol}`" class="dash-symbol-link" @click.stop>{{ group.symbol }}</router-link>
                </td>
                <td class="sparkline-cell">
                  <SparklineChart
                    :priceData="priceHistory[group.symbol]?.prices ?? []"
                    :annotations="priceHistory[group.symbol]?.annotations ?? []"
                    :width="120" :height="32"
                  />
                </td>
                <td class="text-muted text-sm">{{ group.name }}</td>
                <!-- Type col: show contract count for the aggregated row -->
                <td class="text-dim text-sm">{{ group.contracts.length }} ct{{ group.contracts.length !== 1 ? 's' : '' }}</td>
                <!-- Contracts (qty) col: total across all contracts -->
                <td class="text-end">{{ group.contracts.reduce((s, c) => s + c.quantity, 0).toFixed(0) }}</td>
                <!-- Avg Cost col: N/A at group level -->
                <td class="text-end text-dim">--</td>
                <!-- Cost Basis col: total -->
                <td class="text-end">{{ formatCurrency(group.total_cost_basis) }}</td>
                <!-- Current Price col: N/A at group level -->
                <td class="text-end text-dim">--</td>
                <!-- Mkt Value col: total -->
                <td class="text-end">
                  <span v-if="group.total_unrealized_pnl != null" :class="profitLossClass(group.total_unrealized_pnl)">
                    {{ formatCurrency(group.total_market_value) }}
                  </span>
                  <span v-else class="text-muted">--</span>
                </td>
                <!-- Unreal P&L col: total -->
                <td class="text-end">
                  <span v-if="group.total_unrealized_pnl != null" :class="profitLossClass(group.total_unrealized_pnl)">
                    {{ formatCurrency(group.total_unrealized_pnl) }}
                  </span>
                  <span v-else class="text-muted">--</span>
                </td>
                <!-- P&L% col: overall % -->
                <td class="text-end">
                  <span v-if="group.pnl_pct != null" :class="profitLossClass(group.pnl_pct)">
                    {{ group.pnl_pct.toFixed(2) }}%
                  </span>
                  <span v-else class="text-muted">--</span>
                </td>
              </tr>
              <!-- Expanded: one sub-row per option contract -->
              <template v-if="expandedOptions.has(group.symbol)">
                <tr v-for="pos in group.contracts" :key="pos.label" class="option-detail-row">
                  <td></td>
                  <td></td>
                  <td class="text-muted">{{ pos.label }}</td>
                  <td><span class="type-badge" :class="typeBadgeClass(pos.trade_type)">{{ tradeTypeLabel(pos.trade_type) }}</span></td>
                  <td class="text-end">{{ Number(pos.quantity).toFixed(0) }}</td>
                  <td class="text-end">{{ formatCurrency(pos.avg_cost) }}</td>
                  <td class="text-end">{{ formatCurrency(pos.cost_basis) }}</td>
                  <td class="text-end">
                    <span v-if="pos.current_price != null" :class="profitLossClass(pos.unrealized_pnl)">
                      {{ formatCurrency(pos.current_price) }}
                    </span>
                    <span v-else class="text-muted">--</span>
                  </td>
                  <td class="text-end">
                    <span v-if="pos.market_value != null" :class="profitLossClass(pos.unrealized_pnl)">
                      {{ formatCurrency(pos.market_value) }}
                    </span>
                    <span v-else class="text-muted">--</span>
                  </td>
                  <td class="text-end">
                    <span v-if="pos.unrealized_pnl != null" :class="profitLossClass(pos.unrealized_pnl)">
                      {{ formatCurrency(pos.unrealized_pnl) }}
                    </span>
                    <span v-else class="text-muted">--</span>
                  </td>
                  <td class="text-end">
                    <span v-if="pos.pnl_pct != null" :class="profitLossClass(pos.pnl_pct)">
                      {{ pos.pnl_pct.toFixed(2) }}%
                    </span>
                    <span v-else class="text-muted">--</span>
                  </td>
                </tr>
              </template>
            </template>
          </tbody>
          <tfoot v-if="holdingsData?.option?.total_cost_basis != null">
            <tr class="totals-row">
              <td colspan="6" class="text-end">Totals</td>
              <td class="text-end">{{ formatCurrency(holdingsData.option.total_cost_basis) }}</td>
              <td></td>
              <td class="text-end" :class="(holdingsData.option.total_unrealized_pnl ?? 0) >= 0 ? 'text-profit' : 'text-loss'">
                {{ holdingsData.option.total_market_value != null ? formatCurrency(holdingsData.option.total_market_value) : '--' }}
              </td>
              <td class="text-end" :class="(holdingsData.option.total_unrealized_pnl ?? 0) >= 0 ? 'text-profit' : 'text-loss'">
                {{ holdingsData.option.total_unrealized_pnl != null ? formatCurrency(holdingsData.option.total_unrealized_pnl) : '--' }}
              </td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>
      <div v-else-if="!holdingsLoading && !holdingsError" class="text-muted py-3">No open option holdings.</div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, reactive } from 'vue'
import axios from 'axios'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement,
  PointElement, LineElement,
  Title, Tooltip, Legend
} from 'chart.js'
import { Bar, Line } from 'vue-chartjs'
import { formatCurrency, profitLossClass } from '@/utils/tradeUtils.js'
import { API_BASE_URL } from '@/config.js'
import PortfolioHeatmap from '@/components/PortfolioHeatmap.vue'
import SparklineChart from '@/components/SparklineChart.vue'
import CumulativePnlChart from '@/components/CumulativePnlChart.vue'
import { usePriceHistory } from '@/composables/usePriceHistory.js'
import { onSyncComplete } from '@/composables/syncEvents.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend)

// ── State ────────────────────────────────────────────────────────────

const summary = ref(null)
const summaryLoading = ref(false)
const summaryError = ref(null)

const pnlData = ref(null)
const pnlLoading = ref(false)
const pnlError = ref(null)

const holdingsData = ref(null)
const holdingsLoading = ref(false)
const holdingsError = ref(null)

const chartView = ref('monthly')
const assetTypeFilter = ref('all')

// Chart visibility toggles (default closed)
const showPnlChart = ref(false)
const showCumChart = ref(false)
const showWinChart = ref(false)

// Option holdings expanded rows
const expandedOptions = reactive(new Set())
function toggleOptionDetail(key) {
  if (expandedOptions.has(key)) expandedOptions.delete(key)
  else expandedOptions.add(key)
}

const { history: priceHistory, fetchMultiple: fetchPriceHistories } = usePriceHistory()

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
    const { data } = await axios.get(`${API_BASE_URL}/holdings`)
    holdingsData.value = data
    // Fetch sparkline price histories for all positions
    const allPositions = [...(data.stock?.positions ?? []), ...(data.option?.positions ?? [])]
    const symbols = [...new Set(allPositions.map(p => p.symbol))]
    if (symbols.length) fetchPriceHistories(symbols)
  } catch (e) {
    holdingsError.value = e.message || 'Failed to load holdings'
  } finally {
    holdingsLoading.value = false
  }
}

function setAssetType(val) {
  assetTypeFilter.value = val
  fetchPnlOverTime()
}

// Any completed sync (global or per-symbol) can change the aggregate
// dashboard, so it always refetches all three sources.
let unsubscribeSync = null

onMounted(() => {
  fetchSummary()
  fetchPnlOverTime()
  fetchHoldings()

  unsubscribeSync = onSyncComplete(() => {
    fetchSummary()
    fetchPnlOverTime()
    fetchHoldings()
  })
})

onBeforeUnmount(() => {
  unsubscribeSync?.()
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
        backgroundColor: pnlValues.map(v => v >= 0 ? 'rgba(133,153,0,0.55)' : 'rgba(220,50,47,0.55)'),
        borderColor: pnlValues.map(v => v >= 0 ? '#859900' : '#dc322f'),
        borderWidth: 1,
        borderRadius: 3,
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
      backgroundColor: '#073642',
      titleColor: '#eee8d5',
      bodyColor: '#eee8d5',
      borderColor: '#586e75',
      borderWidth: 1,
      titleFont: { family: 'Inter, sans-serif', size: 11 },
      bodyFont: { family: 'Inter, sans-serif', size: 11 },
      callbacks: {
        label: (ctx) => {
          const val = ctx.parsed.y
          return ` ${val >= 0 ? '+' : ''}$${val.toFixed(2)}`
        },
      },
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(88,110,117,0.15)' },
      ticks: { color: '#93a1a1', font: { family: 'Inter, sans-serif', size: 10 } },
    },
    y: {
      grid: { color: 'rgba(88,110,117,0.15)' },
      ticks: {
        color: '#93a1a1',
        font: { family: 'Inter, sans-serif', size: 10 },
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
        borderColor: '#2aa198',
        backgroundColor: 'rgba(42,161,152,0.08)',
        tension: 0.3,
        fill: true,
        pointRadius: 4,
        pointBackgroundColor: '#2aa198',
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
      backgroundColor: '#073642',
      titleColor: '#eee8d5',
      bodyColor: '#eee8d5',
      borderColor: '#586e75',
      borderWidth: 1,
      titleFont: { family: 'Inter, sans-serif', size: 11 },
      bodyFont: { family: 'Inter, sans-serif', size: 11 },
      callbacks: { label: (ctx) => ` ${ctx.parsed.y}%` },
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(88,110,117,0.15)' },
      ticks: { color: '#93a1a1', font: { family: 'Inter, sans-serif', size: 10 } },
    },
    y: {
      min: 0,
      max: 100,
      grid: { color: 'rgba(88,110,117,0.15)' },
      ticks: {
        color: '#93a1a1',
        font: { family: 'Inter, sans-serif', size: 10 },
        callback: (v) => `${v}%`,
      },
    },
  },
}

// ── Computed Helpers ──────────────────────────────────────────────────

const stockPositions = computed(() => holdingsData.value?.stock?.positions ?? [])
const optionPositions = computed(() => holdingsData.value?.option?.positions ?? [])

// Group option positions by underlying symbol for the dashboard table.
// Each group has a parent row (totals) and contract sub-rows (per unique option label).
const groupedOptions = computed(() => {
  const groups = {}
  for (const pos of optionPositions.value) {
    const sym = pos.symbol
    if (!groups[sym]) {
      groups[sym] = { symbol: sym, name: pos.name, contracts: [], total_cost_basis: 0, total_market_value: 0, priced_cost_basis: 0 }
    }
    groups[sym].contracts.push(pos)
    groups[sym].total_cost_basis += pos.cost_basis
    if (pos.market_value != null) {
      groups[sym].total_market_value += pos.market_value
      // Only include cost for contracts that have a live price so P&L denominator matches numerator
      groups[sym].priced_cost_basis += pos.cost_basis
    }
  }
  return Object.values(groups).map(g => {
    const hasPrices = g.priced_cost_basis > 0
    const total_unrealized_pnl = hasPrices ? g.total_market_value - g.priced_cost_basis : null
    const pnl_pct = hasPrices && g.priced_cost_basis !== 0
      ? (total_unrealized_pnl / g.priced_cost_basis) * 100
      : null
    return { ...g, total_unrealized_pnl, pnl_pct }
  })
})

// Adapt holdings data for PortfolioHeatmap (which expects {symbol, shares, average_price, trade_type})
const heatmapPositions = computed(() => {
  const all = [...stockPositions.value, ...optionPositions.value]
  return all.map(p => ({
    symbol: p.symbol,
    shares: p.quantity,
    average_price: p.avg_cost,
    trade_type: p.trade_type,
    name: p.name,
  }))
})

// Build a livePrices-compatible object from server-provided current_price
const heatmapPrices = computed(() => {
  const prices = {}
  for (const p of [...stockPositions.value, ...optionPositions.value]) {
    if (p.current_price != null) {
      prices[p.symbol] = { price: p.current_price, loading: false }
    }
  }
  return prices
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
}

.dash-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 20px;
  color: var(--color-terminal-text);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* ── Summary Cards ───────────────────────────────────────────── */
.dash-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.dash-card {
  background: var(--color-terminal-panel);
  border: 1px solid var(--color-terminal-border-subtle);
  border-radius: 6px;
  padding: 16px 18px;
}

.dash-card-label {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-terminal-text-muted);
  margin-bottom: 6px;
}

.dash-card-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--color-terminal-text);
  font-variant-numeric: tabular-nums;
}

/* ── Sections ────────────────────────────────────────────────── */
.dash-section {
  background: var(--color-terminal-surface);
  border: 1px solid var(--color-terminal-border-subtle);
  border-radius: 6px;
  padding: 18px;
  margin-bottom: 20px;
}

.dash-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  flex-wrap: wrap;
  gap: 8px;
}

.dash-section-title {
  font-size: 0.85rem;
  font-weight: 600;
  margin: 0;
  color: var(--color-terminal-text);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.dash-toggles {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dash-chart-wrap {
  position: relative;
  height: 260px;
}

/* ── Holdings Table ──────────────────────────────────────────── */
.holdings-table th {
  font-size: 0.65rem;
}

.holdings-table td {
  font-size: 0.78rem;
}

.totals-row td {
  font-weight: 700;
  border-top: 2px solid var(--color-terminal-border);
  background: var(--color-terminal-panel);
  font-size: 0.8rem;
}

.dash-symbol-link {
  font-weight: 600;
  color: var(--color-accent-cyan);
  text-decoration: none;
}

.dash-symbol-link:hover {
  color: var(--color-accent-blue);
}

.type-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 99px;
  font-size: 0.62rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: var(--color-terminal-panel);
  color: var(--color-terminal-text-muted);
}

.badge-long { background: rgba(38,139,210,0.15); color: var(--color-long); }
.badge-short { background: rgba(220,50,47,0.15); color: var(--color-short); }
.badge-call { background: rgba(133,153,0,0.15); color: var(--color-call); }
.badge-put { background: rgba(203,75,22,0.15); color: var(--color-put); }

.sparkline-cell {
  padding: 4px 8px;
  vertical-align: middle;
}

.text-dim { color: var(--color-terminal-text-dim); }
.text-sm { font-size: 0.75rem; }
.text-center { text-align: center; }
.py-4 { padding-top: 1rem; padding-bottom: 1rem; }
.py-3 { padding-top: 0.75rem; padding-bottom: 0.75rem; }
.mt-2 { margin-top: 0.5rem; }
.ml-2 { margin-left: 0.5rem; }

/* Option expandable rows */
.option-row { cursor: pointer; }
.option-row:hover { background: var(--color-terminal-hover); }
.expand-icon {
  font-size: 0.6rem;
  color: var(--color-terminal-text-muted);
  margin-right: 6px;
}
.option-detail-row td {
  background: var(--color-terminal-panel);
  padding: 6px 16px;
  font-size: 0.77rem;
  border-top: none;
}
.option-label-detail {
  color: var(--color-terminal-text-muted);
  margin-right: 6px;
}
.option-label-code {
  font-family: 'Courier New', monospace;
  font-size: 0.82rem;
  color: var(--color-accent-blue);
  background: var(--color-terminal-hover);
  padding: 1px 6px;
  border-radius: 3px;
}
</style>
