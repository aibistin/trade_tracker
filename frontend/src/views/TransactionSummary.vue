<template>
  <div class="ts-wrapper">
  <table class="ts-table">
    <thead>
      <tr>
        <th colspan="13" class="ts-title">
          {{ stockType }} Transaction Summary —
          <span class="ts-symbol">{{ stockSymbol }}</span>
        </th>
      </tr>
      <tr>
        <th colspan="3" class="ts-group ts-group-bought">Bought</th>
        <th colspan="4" class="ts-group ts-group-sold">Sold</th>
        <th colspan="3" class="ts-group ts-group-unsold">Unsold</th>
        <th colspan="3" class="ts-group ts-group-result">Result</th>
      </tr>
      <tr>
        <th class="ts-col">Total Qty</th>
        <th class="ts-col">Avg Price</th>
        <th class="ts-col">Cost Basis</th>

        <th class="ts-col">Qty</th>
        <th class="ts-col">Avg Price</th>
        <th class="ts-col">Cost Basis</th>
        <th class="ts-col">Revenue</th>

        <th class="ts-col">Qty</th>
        <th class="ts-col">Avg Price</th>
        <th class="ts-col">Cost Basis</th>

        <th class="ts-col">Profit/Loss</th>
        <th class="ts-col">Profit/Loss %</th>
        <th class="ts-col">Trade Ct</th>
      </tr>
    </thead>
    <tbody>
      <tr class="ts-data-row">
        <td>{{ tradeSummary.bought_quantity }}</td>
        <td>{{ formatCurrency(Math.abs(tradeSummary.average_bought_price || 0)) }}</td>
        <td :class="profitLossClass(tradeSummary.bought_amount)">
          {{ formatCurrency(tradeSummary.bought_amount || 0) }}
        </td>

        <td>{{ tradeSummary.sold_quantity }}</td>
        <td>{{ formatCurrency(tradeSummary.average_basis_sold_price || 0) }}</td>
        <td :class="profitLossClass(tradeSummary.closed_bought_amount)">
          {{ formatCurrency(tradeSummary.closed_bought_amount || 0) }}
        </td>
        <td>{{ formatCurrency(tradeSummary.sold_amount || 0) }}</td>

        <td>{{ tradeSummary.open_bought_quantity }}</td>
        <td>{{ formatCurrency(tradeSummary.average_basis_open_price || 0) }}</td>
        <td>{{ formatCurrency(tradeSummary.open_bought_amount || 0) }}</td>

        <td :class="profitLossClass(tradeSummary.profit_loss)">
          {{ formatCurrency(tradeSummary.profit_loss) }}
        </td>
        <td :class="profitLossClass(tradeSummary.percent_profit_loss)">
          {{ formatValue(tradeSummary.percent_profit_loss) }}%
        </td>
        <td>{{ allTradeCount }}</td>
      </tr>
    </tbody>
  </table>
  </div>
</template>

<script>
import { formatCurrency, profitLossClass, formatValue } from '@/utils/tradeUtils.js';

export default {
  props: {
    stockSymbol: {
      type: String,
      required: true
    },
    stockType: {
      type: String,
      required: true
    },
    tradeSummary: {
      type: Object,
      required: true
    },
    allTradeCount: {
      type: Number,
      required: false,
      default: 0
    },
  },
  methods: {
    formatCurrency,
    profitLossClass,
    formatValue,
  }
};
</script>

<style scoped>
/* ── Rounded Outer Wrapper ──────────────────────────────────── */
/* overflow: hidden clips all child elements to the rounded edge */
.ts-wrapper {
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 16px;
  border: 1px solid #373b3e;
}

/* ── Table Shell ────────────────────────────────────────────── */
.ts-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 0;
  font-size: 0.85rem;
}

/* ── Title Row ─────────────────────────────────────────────── */
/* Matches AllTrades column header: table-dark #212529          */
.ts-title {
  background: #212529;
  color: #fff;
  text-align: center;
  padding: 8px 12px;
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.ts-symbol {
  color: #74c2e1;
}

/* ── Column Group Headers ───────────────────────────────────── */
/* Each group uses a distinct dark tint + colored bottom accent  */
.ts-group {
  text-align: center;
  padding: 6px 8px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border: 1px solid #373b3e;
  border-bottom-width: 3px;
}

.ts-group-bought {
  background: #0c1c32;
  color: #7ab3e8;
  border-bottom-color: #0d6efd;
}
.ts-group-sold {
  background: #2a0d0d;
  color: #e88a8a;
  border-bottom-color: #dc3545;
}
.ts-group-unsold {
  background: #0a2116;
  color: #7acca0;
  border-bottom-color: #198754;
}
.ts-group-result {
  background: #1f1200;
  color: #e8b47a;
  border-bottom-color: #fd7e14;
}

/* ── Column Name Headers ────────────────────────────────────── */
.ts-col {
  background: #2c3237;
  color: #adb5bd;
  text-align: center;
  padding: 5px 8px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  border: 1px solid #373b3e;
}

/* ── Data Row ───────────────────────────────────────────────── */
/* Matches TradeCard: table-info #cff4fc, dark text             */
.ts-data-row td {
  background: #cff4fc;
  color: #000;
  text-align: center;
  padding: 7px 8px;
  border: 1px solid #bacbe3;
  font-weight: 500;
}
.ts-data-row td:hover {
  background: #bfdaec;
}
</style>
