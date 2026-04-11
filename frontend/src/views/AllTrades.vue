<template>
  <div class="all-trades">
    <!-- Loading State -->
    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border" role="status"></div>
      <p class="mt-2 text-muted">Loading {{ titleCase(scope) }} trades...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="alert alert-danger">
      Error loading data: {{ error }}
    </div>

    <div v-if="data">
      <div class="trades-header">
        <h4 class="trades-title">
          {{ titleCase(scope) }} Trades —
          <span class="trades-symbol">{{ data.stock_symbol }}</span>
        </h4>

        <!-- Cost vs Market Value summary -->
        <div v-if="holdingSummary" class="holding-summary">
          <div class="hs-item">
            <span class="hs-label">Avg Cost</span>
            <span class="hs-value">{{ formatCurrency(holdingSummary.avg_cost) }}</span>
          </div>
          <div class="hs-item">
            <span class="hs-label">Current Price</span>
            <span class="hs-value" :class="holdingSummary.current_price >= holdingSummary.avg_cost ? 'text-profit' : 'text-loss'">
              {{ formatCurrency(holdingSummary.current_price) }}
            </span>
          </div>
          <div class="hs-item">
            <span class="hs-label">Cost Basis</span>
            <span class="hs-value">{{ formatCurrency(holdingSummary.cost_basis) }}</span>
          </div>
          <div class="hs-item">
            <span class="hs-label">Market Value</span>
            <span class="hs-value" :class="holdingSummary.unrealized_pnl >= 0 ? 'text-profit' : 'text-loss'">
              {{ formatCurrency(holdingSummary.market_value) }}
            </span>
          </div>
          <div class="hs-item">
            <span class="hs-label">Unrealized P&amp;L</span>
            <span class="hs-value" :class="holdingSummary.unrealized_pnl >= 0 ? 'text-profit' : 'text-loss'">
              {{ formatCurrency(holdingSummary.unrealized_pnl) }}
              ({{ holdingSummary.pnl_pct?.toFixed(2) }}%)
            </span>
          </div>
        </div>
      </div>

      <div class="date-filter">
        <label for="afterDateFilter" class="filter-label">Show trades after:</label>
        <input id="afterDateFilter" type="date"
          :value="afterDate" @change="applyDateFilter($event.target.value)" />
        <button v-if="afterDate" class="btn btn-sm btn-outline-secondary" @click="clearDateFilter">Clear</button>
      </div>

      <!-- Stock Trades -->
      <div v-if="data.transaction_stats.stock?.has_trades === true">
        <TransactionSummary :tradeSummary="data.transaction_stats.stock.summary" :stockSymbol="data.stock_symbol"
          stockType="Stock" :allTradeCount="data.transaction_stats.stock.all_trades?.length" />
        <WinLossBar
          :wins="data.transaction_stats.stock.summary?.winning_trades_count ?? 0"
          :losses="data.transaction_stats.stock.summary?.losing_trades_count ?? 0"
          :avgWin="avgClosedPnl(data.transaction_stats.stock.all_trades, true)"
          :avgLoss="avgClosedPnl(data.transaction_stats.stock.all_trades, false)" />
        <div class="tc-section">
          <TradeCard v-for="trade in allBuyTrades.stock" :key="trade.trade_id"
            :trade="trade" stockType="Stock" @trade-updated="updateTrade" />
        </div>
      </div>

      <!-- Option Trades -->
      <div v-if="data.transaction_stats.option?.has_trades === true">
        <TransactionSummary :tradeSummary="data.transaction_stats.option.summary" :stockSymbol="data.stock_symbol"
          stockType="Option" :allTradeCount="data.transaction_stats.option.all_trades?.length" />
        <WinLossBar
          :wins="data.transaction_stats.option.summary?.winning_trades_count ?? 0"
          :losses="data.transaction_stats.option.summary?.losing_trades_count ?? 0"
          :avgWin="avgClosedPnl(data.transaction_stats.option.all_trades, true)"
          :avgLoss="avgClosedPnl(data.transaction_stats.option.all_trades, false)" />
        <div class="tc-section">
          <TradeCard v-for="trade in allBuyTrades.option" :key="trade.trade_id"
            :trade="trade" stockType="Option" @trade-updated="updateTrade" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { API_BASE_URL } from '@/config.js';
import { useFetchTrades } from '@/composables/useFetchTrades.js';
import { formatCurrency } from '@/utils/tradeUtils.js';
import TransactionSummary from '@/components/TransactionSummary.vue';
import TradeCard from '@/components/TradeCard.vue';
import WinLossBar from '@/components/WinLossBar.vue';

const props = defineProps({
  stockSymbol: {
    type: String,
    required: true,
    validator: (v) => v === v.toUpperCase(),
  },
  scope: {
    type: String,
    required: true,
    validator: (v) => ['all', 'open', 'closed'].includes(v),
  },
});

const route = useRoute();
const router = useRouter();
const afterDate = ref(route.query.after_date || '');
const { data, loading, error, fetchData } = useFetchTrades();

// Current holding summary for this symbol (from /api/holdings)
const holdingSummary = ref(null);

async function fetchHoldingSummary(symbol) {
  try {
    const { data: h } = await axios.get(`${API_BASE_URL}/holdings`);
    const allPositions = [
      ...(h.stock?.positions ?? []),
      ...(h.option?.positions ?? []),
    ];
    const match = allPositions.find(p => p.symbol === symbol);
    holdingSummary.value = match ?? null;
  } catch {
    holdingSummary.value = null;
  }
}

const WANTED_KEYS = [
  'trade_id', 'account', 'trade_type', 'action', 'trade_label', 'is_option',
  'trade_date', 'price', 'is_buy_trade', 'target_price', 'expiration_date',
  'quantity', 'amount', 'profit_loss', 'percent_profit_loss', 'is_done',
  'closed_date', 'current_sold_qty', 'current_sold_amt', 'current_profit_loss',
  'current_percent_profit_loss', 'sells', 'reason', 'initial_stop_price',
  'projected_sell_price', 'symbol',
];

function transformTrade(trade) {
  const result = {};
  for (const key of WANTED_KEYS) {
    if (Object.prototype.hasOwnProperty.call(trade, key)) {
      result[key] = trade[key];
    }
  }
  return result;
}

const allBuyTrades = computed(() => {
  if (!data.value) return { stock: [], option: [] };
  return {
    stock: (data.value.transaction_stats.stock?.all_trades ?? [])
      .filter((t) => t.is_buy_trade === true)
      .map(transformTrade),
    option: (data.value.transaction_stats.option?.all_trades ?? [])
      .filter((t) => t.is_buy_trade === true)
      .map(transformTrade),
  };
});

function avgClosedPnl(trades, isWin) {
  const closed = (trades ?? []).filter(t => t.is_buy_trade && t.is_done);
  const filtered = isWin
    ? closed.filter(t => t.current_profit_loss > 0)
    : closed.filter(t => t.current_profit_loss < 0);
  if (!filtered.length) return null;
  return filtered.reduce((sum, t) => sum + t.current_profit_loss, 0) / filtered.length;
}

function titleCase(str) {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

function createApiUrl(scope, symbol, query = {}) {
  let url = `${API_BASE_URL}/trades/${scope}/json/${symbol}`;
  const params = new URLSearchParams();
  if (query.after_date) params.set('after_date', query.after_date);
  if (query.asset_type && query.asset_type !== 'all') params.set('asset_type', query.asset_type);
  const qs = params.toString();
  if (qs) url += `?${qs}`;
  return url;
}

function applyDateFilter(dateValue) {
  afterDate.value = dateValue;
  const query = { ...route.query };
  if (dateValue) {
    query.after_date = dateValue;
  } else {
    delete query.after_date;
  }
  router.replace({ params: route.params, query });
}

function clearDateFilter() {
  afterDate.value = '';
  const query = { ...route.query };
  delete query.after_date;
  router.replace({ params: route.params, query });
}

function updateTrade(tradeId, fields) {
  for (const section of ['stock', 'option']) {
    const trades = data.value?.transaction_stats?.[section]?.all_trades;
    if (!trades) continue;
    const idx = trades.findIndex((t) => t.trade_id === tradeId);
    if (idx !== -1) {
      Object.assign(trades[idx], fields);
      return;
    }
  }
}

onMounted(() => {
  fetchData(createApiUrl(props.scope, props.stockSymbol, route.query));
  fetchHoldingSummary(props.stockSymbol);
});

watch(
  [() => props.scope, () => props.stockSymbol, () => route.query.after_date, () => route.query.asset_type],
  ([newScope, newSymbol, newAfterDate]) => {
    afterDate.value = newAfterDate || '';
    fetchData(createApiUrl(newScope, newSymbol, route.query));
  }
);
</script>

<style scoped>
.all-trades {
  max-width: 1200px;
  margin: 0 auto;
}

.trades-header {
  margin-bottom: 16px;
}

.trades-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-terminal-text);
  margin-bottom: 10px;
}

/* Cost vs Market Value summary bar */
.holding-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  background: var(--color-terminal-surface);
  border: 1px solid var(--color-terminal-border);
  border-radius: 6px;
  overflow: hidden;
}

.hs-item {
  display: flex;
  flex-direction: column;
  padding: 10px 18px;
  border-right: 1px solid var(--color-terminal-border);
  min-width: 120px;
}
.hs-item:last-child { border-right: none; }

.hs-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-terminal-text-muted);
  margin-bottom: 2px;
}

.hs-value {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-terminal-text);
  font-variant-numeric: tabular-nums;
}

.trades-symbol {
  color: var(--color-accent-cyan);
}

.date-filter {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.filter-label {
  font-size: 0.75rem;
  color: var(--color-terminal-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

/* ── Trade Card Section ─────────────────────────────────────── */
.tc-section {
  margin-bottom: 24px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--color-terminal-border-subtle);
}

.text-center { text-align: center; }
.py-4 { padding: 1rem 0; }
.mt-2 { margin-top: 0.5rem; }
</style>
