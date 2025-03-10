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

      <h4 class="mt-4 mb-3">{{ titleCase(scope)}} Trades for <span
          class="text-primary-emphasis">{{ data.stock_symbol }}</span>
      </h4>

      <TransactionSummary :tradeSummary="data.transaction_stats.stock.summary" :stockSymbol="data.stock_symbol"
        :allTradeCount="data.transaction_stats.stock.all_trades?.length" />
      <div v-if="data.transaction_stats.stock.all_trades?.length">
        <buy-trade-summary :stockSymbol="data.stock_symbol">
          <tr v-for="trade in flattenTrades(data.transaction_stats.stock.all_trades)" :key="trade.trade_id"
            :class="tradeRowClass(trade)">
            <TradeTableRow :buyTrade="transformTrade(trade)" />
          </tr>
        </buy-trade-summary>
      </div>
      <!-- Put option trades here -->

    </div>
  </div>
</template>

<script>
import { onMounted, ref, watch } from "vue";
import { useRoute } from 'vue-router';
import { logRoute, profitLossClass } from "@/utils/tradeUtils.js";
import { useFetchTrades } from '../composables/useFetchTrades';
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
      default: '',
      validator: (value) => value === value.toUpperCase(),
    },
    scope: {
      type: String,
      required: true,
      validator: (value) => ['all', 'open', 'closed'].includes(value),
    },
  },
  methods: {
    profitLossClass,
    titleCase(str) {
      return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    },
    tradeRowClass(trade) {
      return {
        "table-info": trade.isBuy ? true : false,
        "border-subtle": trade.isBuy ? true : false,
        /* Sell Trades */
        "table-light": trade.isBuy ? false : true,
        "border-light": trade.isBuy ? false : true,
        "table-borderless": trade.isBuy ? false : true,
      };
    },
    transformTrade(trade) {
      const sameKeys = ["trade_id", "account", "trade_date_iso", "price", "isBuy", "profit_loss", "percent_profit_loss"];
      let newTrade = {
        bought_quantity: trade.quantity,
        bought_amount: trade.amount,
        sold_quantity: trade.quantity,
        sold_amount: trade.amount,
        isClosed: ""
      };
      sameKeys.forEach((key) => {
        if (Object.prototype.hasOwnProperty.call(trade, key)) {
          newTrade[key] = trade[key];
        }
      });

      if (trade.isBuy) {
        newTrade.sold_quantity = trade.current_sold_qty
        newTrade.isClosed = trade?.is_done ? "Closed" : "Open";
        newTrade.sold_amount = trade.sells?.reduce((sum, sell) => sum + sell.amount, 0);
        newTrade.profit_loss = trade.sells?.reduce((sum, sell) => sum + sell.profit_loss, 0);
        newTrade.percent_profit_loss = trade.sells?.length
          ? trade.sells.reduce(
            (sum, sell) => sum + sell.percent_profit_loss,
            0
          ) / trade.sells.length
          : 0;
      }
      return newTrade;
    },
    /* Include sells in the trades array for easier table creation */
    flattenTrades(trades) {
      let flatTrades = trades.reduce((acc, trade) => {
        trade.isBuy = true;
        acc.push(trade);

        if (trade?.sells.length > 0) {
          let flatArr = trade.sells
            .map((sell) => {
              sell.isBuy = false;
              return sell;
            })
            .forEach((sell) => acc.push(sell));
          console.log(`Flat Sells: ${flatArr}`);
        }
        return acc;
      }, []);
      return flatTrades;
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
      return `http://localhost:5000/trades/${scope}/json/${stockSymbolValue}`;

    }

    const toggleTrade = (tradeId) => {
      const newSet = new Set(expandedTrades.value);
      newSet.has(tradeId) ? newSet.delete(tradeId) : newSet.add(tradeId);
      expandedTrades.value = newSet;
    };

    apiUrl.value = _createApiUrl(props.scope, stockSymbol.value);
    console.log(`[AllTrades] API URL: ${apiUrl.value}`);

    onMounted(() => {
      apiUrl.value = _createApiUrl(props.scope, stockSymbol.value);
      console.log(`[AllTrades.vue->Mounted]: Fetching data URL: ${apiUrl.value}`);
      fetchData(apiUrl); // Done reactively in the getFetchTrades composable
    });


    watch(
      [() => props.scope, () => props.stockSymbol],
      ([newScope, newSymbol]) => {
        console.log(`[AllTrades.vue->Watch props]: New Scope: ${newScope.value}`);
        console.log(`[AllTrades.vue->Watch props]: New Symbol: ${newSymbol.value}`);
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
