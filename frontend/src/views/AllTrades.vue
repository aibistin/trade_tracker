<template>
  <div class="all-trades">
    <!-- Loading State -->
    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Loading {{ titleCase(scope) }} trades...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="alert alert-danger">
      Error loading data: {{ error }}
    </div>

    <div v-if="data">
      <h4 class="mt-4 mb-3">
        {{ titleCase(scope) }} Trades for
        <span class="text-primary-emphasis">{{ data.stock_symbol }}</span>
      </h4>

      <div class="d-flex align-items-center gap-2 mb-3">
        <label for="afterDateFilter" class="form-label mb-0 text-nowrap">Show trades after:</label>
        <input id="afterDateFilter" type="date" class="form-control form-control-sm" style="max-width: 200px;"
          :value="afterDate" @change="applyDateFilter($event.target.value)" />
        <button v-if="afterDate" class="btn btn-sm btn-outline-secondary" @click="clearDateFilter">Clear</button>
      </div>

      <!-- Stock Trades -->
      <div v-if="data.transaction_stats.stock?.has_trades === true">
        <TransactionSummary :tradeSummary="data.transaction_stats.stock.summary" :stockSymbol="data.stock_symbol"
          stockType="Stock" :allTradeCount="data.transaction_stats.stock.all_trades?.length" />
        <div class="tc-section">
          <TradeCard v-for="trade in allBuyTrades.stock" :key="trade.trade_id"
            :trade="trade" stockType="Stock" @trade-updated="updateTrade" />
        </div>
      </div>

      <!-- Option Trades -->
      <div v-if="data.transaction_stats.option?.has_trades === true">
        <TransactionSummary :tradeSummary="data.transaction_stats.option.summary" :stockSymbol="data.stock_symbol"
          stockType="Option" :allTradeCount="data.transaction_stats.option.all_trades?.length" />
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
import { API_BASE_URL } from '@/config.js';
import { useFetchTrades } from '@/composables/useFetchTrades.js';
import TransactionSummary from '@/components/TransactionSummary.vue';
import TradeCard from '@/components/TradeCard.vue';

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

const WANTED_KEYS = [
  'trade_id', 'account', 'trade_type', 'action', 'trade_label', 'is_option',
  'trade_date', 'price', 'is_buy_trade', 'target_price', 'expiration_date',
  'quantity', 'amount', 'profit_loss', 'percent_profit_loss', 'is_done',
  'closed_date', 'current_sold_qty', 'current_sold_amt', 'current_profit_loss',
  'current_percent_profit_loss', 'sells', 'reason', 'initial_stop_price',
  'projected_sell_price',
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

// Update source data when TradeCard saves changes (data-down/events-up)
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
  margin: 20px;
}

/* ── Trade Card Section ─────────────────────────────────────── */
/* Rounded container clips header + cards to give soft corners   */
.tc-section {
  margin-bottom: 24px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #373b3e;
}
</style>
