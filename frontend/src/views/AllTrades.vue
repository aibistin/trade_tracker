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
          <div class="tc-header-row">
            <div class="tc-hcell"></div>
            <div class="tc-hcell">ID-Acct</div>
            <div class="tc-hcell">Type</div>
            <div class="tc-hcell">Action</div>
            <div class="tc-hcell">Date</div>
            <div class="tc-hcell">Qty</div>
            <div class="tc-hcell">Price</div>
            <div class="tc-hcell">Cost</div>
            <div class="tc-hcell">Sold Qty</div>
            <div class="tc-hcell">Sold Amt</div>
            <div class="tc-hcell">P/L</div>
            <div class="tc-hcell">P/L%</div>
            <div class="tc-hcell">Status</div>
          </div>
          <TradeCard v-for="trade in buyTrades(data.transaction_stats.stock.all_trades)" :key="trade.trade_id"
            :trade="transformTrade(trade)" stockType="Stock" />
        </div>
      </div>

      <!-- Option Trades -->
      <div v-if="data.transaction_stats.option?.has_trades === true">
        <TransactionSummary :tradeSummary="data.transaction_stats.option.summary" :stockSymbol="data.stock_symbol"
          stockType="Option" :allTradeCount="data.transaction_stats.option.all_trades?.length" />
        <div class="tc-section">
          <div class="tc-header-row">
            <div class="tc-hcell"></div>
            <div class="tc-hcell">ID-Acct</div>
            <div class="tc-hcell">Type</div>
            <div class="tc-hcell">Action</div>
            <div class="tc-hcell">Date</div>
            <div class="tc-hcell">Qty x 100</div>
            <div class="tc-hcell">Price</div>
            <div class="tc-hcell">Cost</div>
            <div class="tc-hcell">Sold Qty</div>
            <div class="tc-hcell">Sold Amt</div>
            <div class="tc-hcell">P/L</div>
            <div class="tc-hcell">P/L%</div>
            <div class="tc-hcell">Status</div>
          </div>
          <TradeCard v-for="trade in buyTrades(data.transaction_stats.option.all_trades)" :key="trade.trade_id"
            :trade="transformTrade(trade)" stockType="Option" />
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { API_BASE_URL } from "@/config.js";
import { useFetchTrades } from "../composables/useFetchTrades";
import TransactionSummary from "./TransactionSummary.vue";
import TradeCard from "../components/TradeCard.vue";

export default {
  components: {
    TransactionSummary,
    TradeCard,
  },
  props: {
    stockSymbol: {
      type: String,
      required: true,
      default: "",
      validator: (value) => value === value.toUpperCase(),
    },
    scope: {
      type: String,
      required: true,
      validator: (value) => ["all", "open", "closed"].includes(value),
    },
  },
  methods: {
    titleCase(str) {
      return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    },
    buyTrades(trades) {
      if (!trades) return [];
      return trades.filter((t) => t.is_buy_trade === true);
    },
    transformTrade(trade) {
      const wantedKeys = [
        "trade_id",
        "account",
        "trade_type",
        "action",
        "trade_label",
        "is_option",
        "trade_date",
        "price",
        "is_buy_trade",
        "target_price",
        "expiration_date",
        "quantity",
        "amount",
        "profit_loss",
        "percent_profit_loss",
        "is_done",
        /* BuyTrade specific fields */
        "current_sold_qty",
        "current_sold_amt",
        "current_profit_loss",
        "current_percent_profit_loss",
        /* Matched sells */
        "sells",
        /* User-editable fields */
        "reason",
        "initial_stop_price",
        "projected_sell_price",
      ];

      let newTrade = {};
      wantedKeys.forEach((key) => {
        if (Object.prototype.hasOwnProperty.call(trade, key)) {
          newTrade[key] = trade[key];
        }
      });
      return newTrade;
    },
  },

  setup(props) {
    const route = useRoute();
    const router = useRouter();
    const apiUrl = ref(null);
    const stockSymbol = ref(props.stockSymbol);
    const afterDate = ref(route.query.after_date || "");
    const { data, loading, error, fetchData } = useFetchTrades();

    const _createApiUrl = (scope, stockSymbolValue, query = {}) => {
      let url = `${API_BASE_URL}/trades/${scope}/json/${stockSymbolValue}`;
      const params = new URLSearchParams();
      if (query.after_date) params.set('after_date', query.after_date);
      if (query.asset_type && query.asset_type !== 'all') params.set('asset_type', query.asset_type);
      const qs = params.toString();
      if (qs) url += `?${qs}`;
      return url;
    };

    const applyDateFilter = (dateValue) => {
      afterDate.value = dateValue;
      const query = { ...route.query };
      if (dateValue) {
        query.after_date = dateValue;
      } else {
        delete query.after_date;
      }
      router.replace({ params: route.params, query });
    };

    const clearDateFilter = () => {
      afterDate.value = "";
      const query = { ...route.query };
      delete query.after_date;
      router.replace({ params: route.params, query });
    };

    apiUrl.value = _createApiUrl(props.scope, stockSymbol.value, route.query);

    onMounted(() => {
      apiUrl.value = _createApiUrl(props.scope, stockSymbol.value, route.query);
      fetchData(apiUrl);
    });

    watch(
      [() => props.scope, () => props.stockSymbol, () => route.query.after_date, () => route.query.asset_type],
      ([newScope, newSymbol, newAfterDate]) => {
        afterDate.value = newAfterDate || "";
        apiUrl.value = _createApiUrl(newScope, newSymbol, route.query);
        fetchData(apiUrl);
      }
    );

    return {
      data,
      loading,
      error,
      afterDate,
      applyDateFilter,
      clearDateFilter,
    };
  },
};
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

/* ── Column Header Row ──────────────────────────────────────── */
/* Matches Bootstrap table-dark: #212529 bg, white text          */
/* Must match TradeCard.vue's .tc-row grid-template-columns exactly */
.tc-header-row {
  display: grid;
  grid-template-columns: 28px 100px 60px 75px 90px 65px 80px 95px 75px 95px 95px 70px 70px;
  gap: 6px;
  padding: 6px 12px 6px 16px;
  background: #212529;
  border-bottom: 1px solid #4a5058;
}

.tc-hcell {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #dee2e6;
  white-space: nowrap;
}
</style>
