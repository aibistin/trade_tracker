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
          <th class="ts-col">Qty</th>
          <th class="ts-col">Avg Price</th>
          <th class="ts-col">Cost</th>

          <th class="ts-col">Qty</th>
          <th class="ts-col">Avg Price</th>
          <th class="ts-col">Cost</th>
          <th class="ts-col">Revenue</th>

          <th class="ts-col">Qty</th>
          <th class="ts-col">Avg Price</th>
          <th class="ts-col">Cost</th>

          <th class="ts-col">P/L</th>
          <th class="ts-col">P/L%</th>
          <th class="ts-col">Trade Ct</th>
        </tr>
      </thead>
      <tbody>
        <tr class="ts-data-row">
          <td>{{ tradeSummary.bought_quantity }}</td>
          <td>{{ formatCurrency(Math.abs(tradeSummary.average_bought_price || 0)) }}</td>
          <td>{{ formatCurrency(tradeSummary.bought_amount || 0) }}</td>

          <td>{{ tradeSummary.sold_quantity }}</td>
          <td>{{ formatCurrency(tradeSummary.average_basis_sold_price || 0) }}</td>
          <td>{{ formatCurrency(tradeSummary.closed_bought_amount || 0) }}</td>
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

<script setup>
import { formatCurrency, profitLossClass, formatValue } from '@/utils/tradeUtils.js';

defineProps({
  stockSymbol: { type: String, required: true },
  stockType: { type: String, required: true },
  tradeSummary: { type: Object, required: true },
  allTradeCount: { type: Number, default: 0 },
});
</script>

<style scoped>
.ts-wrapper {
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 16px;
  border: 1px solid var(--color-terminal-border);
}

.ts-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 0;
  font-size: 0.82rem;
}

.ts-title {
  background: var(--color-terminal-bg);
  color: var(--color-terminal-text);
  text-align: center;
  padding: 8px 12px;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.ts-symbol {
  color: var(--color-accent-cyan);
}

.ts-group {
  text-align: center;
  padding: 6px 8px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border: 1px solid var(--color-terminal-border);
  border-bottom-width: 2px;
}

.ts-group-bought {
  background: rgba(59, 130, 246, 0.08);
  color: var(--color-long);
  border-bottom-color: var(--color-long);
}

.ts-group-sold {
  background: rgba(239, 68, 68, 0.08);
  color: var(--color-loss);
  border-bottom-color: var(--color-loss);
}

.ts-group-unsold {
  background: rgba(34, 197, 94, 0.08);
  color: var(--color-profit);
  border-bottom-color: var(--color-profit);
}

.ts-group-result {
  background: rgba(249, 115, 22, 0.08);
  color: var(--color-accent-orange);
  border-bottom-color: var(--color-accent-orange);
}

.ts-col {
  background: var(--color-terminal-panel);
  color: var(--color-terminal-text-muted);
  text-align: center;
  padding: 5px 8px;
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  border: 1px solid var(--color-terminal-border-subtle);
}

.ts-data-row td {
  background: var(--color-terminal-surface);
  color: var(--color-terminal-text);
  text-align: center;
  padding: 7px 8px;
  border: 1px solid var(--color-terminal-border-subtle);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.ts-data-row td:hover {
  background: var(--color-terminal-hover);
}
</style>
