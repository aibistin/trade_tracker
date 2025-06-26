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

      <div v-if="data.transaction_stats.stock.has_trades === true">
        <TransactionSummary :tradeSummary="data.transaction_stats.stock.summary" :stockSymbol="data.stock_symbol"
          stockType="Stock" :allTradeCount="data.transaction_stats.stock.all_trades?.length" />
        <buy-trade-summary :stockSymbol="data.stock_symbol" stockType="Stock">
          <tr v-for="trade in data.transaction_stats.stock.all_trades" :key="trade.trade_id"
            :class="tradeRowClass(trade)">
            <TradeTableRow :trade="transformTrade(trade)" />
          </tr>
        </buy-trade-summary>
      </div>

      <!-- Option trades here -->
      <div v-if="data.transaction_stats.option.has_trades === true">
        <TransactionSummary :tradeSummary="data.transaction_stats.option.summary" :stockSymbol="data.stock_symbol"
          stockType="Option" :allTradeCount="data.transaction_stats.option.all_trades?.length" />
        <buy-trade-summary :stockSymbol="data.stock_symbol" stockType="Option">
          <tr v-for="trade in data.transaction_stats.option.all_trades" :key="trade.trade_id"
            :class="tradeRowClass(trade)">
            <TradeTableRow :trade="transformTrade(trade)" stockType="Option" />
          </tr>
        </buy-trade-summary>
      </div>


    </div>
  </div>
</template>

<script>
import { onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { logRoute, profitLossClass } from "@/utils/tradeUtils.js";
import { useFetchTrades } from "../composables/useFetchTrades";
import TransactionSummary from "./TransactionSummary.vue";
import TradeTableRow from "../components/TradeTableRow.vue";
import BuyTradeSummary from "../components/BuyTradeSummary.vue";

export default {
  components: {
    TransactionSummary,
    TradeTableRow,
    BuyTradeSummary,
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
    profitLossClass,
    titleCase(str) {
      return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    },
    tradeRowClass(trade) {
      return {
        "table-info": trade.is_buy_trade ? true : false,
        "border-subtle": trade.is_buy_trade ? true : false,
        /* Sell Trades */
        "table-light": trade.is_buy_trade ? false : true,
        "border-light": trade.is_buy_trade ? false : true,
        "table-borderless": trade.is_buy_trade ? false : true,
      };
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
        /*BuyTrade specific fields */
        "current_sold_qty",
        "current_sold_amt",
        "current_profit_loss",
        "current_percent_profit_loss",
        /*SellTrade specific fields */
        "basis_price",
        "basis_amt",
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
    const apiUrl = ref(null);
    const expandedTrades = ref(new Set());
    const stockSymbol = ref(props.stockSymbol);
    const { data, loading, error, fetchData } = useFetchTrades();
    const route = useRoute();
    logRoute(route);
    // Get all_trades, open_trades or closed_trades
    const _createApiUrl = (scope, stockSymbolValue) => {
      return `http://localhost:5000/api/trades/${scope}/json/${stockSymbolValue}`;
    };

    const toggleTrade = (tradeId) => {
      const newSet = new Set(expandedTrades.value);
      newSet.has(tradeId) ? newSet.delete(tradeId) : newSet.add(tradeId);
      expandedTrades.value = newSet;
    };

    apiUrl.value = _createApiUrl(props.scope, stockSymbol.value);
    console.log(`[AllTrades] API URL: ${apiUrl.value}`);

    onMounted(() => {
      apiUrl.value = _createApiUrl(props.scope, stockSymbol.value);
      console.log(
        `[AllTrades.vue->Mounted]: Fetching data URL: ${apiUrl.value}`
      );
      fetchData(apiUrl); // Done reactively in the getFetchTrades composable
    });

    watch(
      [() => props.scope, () => props.stockSymbol],
      ([newScope, newSymbol]) => {
        console.log(
          `[AllTrades.vue->Watch props]: New Scope: ${newScope.value}`
        );
        console.log(
          `[AllTrades.vue->Watch props]: New Symbol: ${newSymbol.value}`
        );
        apiUrl.value = _createApiUrl(newScope, newSymbol);
        console.log(`[AllTrades.vue->Watch Props]: New URL: ${apiUrl.value}`);
        fetchData(apiUrl);
      }
    );

    return {
      data,
      loading,
      error,
      expandedTrades,
      logRoute,
      toggleTrade,
    };
  },
};
</script>

<style scoped>
.all-trades {
  margin: 20px;
}
</style>
