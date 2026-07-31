<template>
  <div class="ts-wrapper">
    <div class="ts-title">
      {{ stockType }} Transaction Summary —
      <span class="ts-symbol">{{ stockSymbol }}</span>
    </div>

    <div class="ts-grid">
      <div class="ts-card ts-card-bought">
        <div class="ts-card-header">Bought</div>
        <div class="ts-card-row ts-card-labels">
          <span>Qty</span>
          <span>Avg Price</span>
          <span>Cost</span>
        </div>
        <div class="ts-card-row ts-card-values">
          <span>{{ tradeSummary.bought_quantity }}</span>
          <span>{{ formatCurrency(Math.abs(tradeSummary.average_bought_price || 0)) }}</span>
          <span>{{ formatCurrency(tradeSummary.bought_amount || 0) }}</span>
        </div>
      </div>

      <div class="ts-card ts-card-sold">
        <div class="ts-card-header">Sold</div>
        <div class="ts-card-row ts-card-labels ts-cols-4">
          <span>Qty</span>
          <span>Avg Price</span>
          <span>Cost</span>
          <span>Revenue</span>
        </div>
        <div class="ts-card-row ts-card-values ts-cols-4">
          <span>{{ tradeSummary.sold_quantity }}</span>
          <span>{{ formatCurrency(tradeSummary.average_basis_sold_price || 0) }}</span>
          <span>{{ formatCurrency(tradeSummary.closed_bought_amount || 0) }}</span>
          <span>{{ formatCurrency(tradeSummary.sold_amount || 0) }}</span>
        </div>
      </div>

      <div class="ts-card ts-card-unsold">
        <div class="ts-card-header">Unsold</div>
        <div class="ts-card-row ts-card-labels">
          <span>Qty</span>
          <span>Avg Price</span>
          <span>Cost</span>
        </div>
        <div class="ts-card-row ts-card-values">
          <span>{{ tradeSummary.open_bought_quantity }}</span>
          <span>{{ formatCurrency(tradeSummary.average_basis_open_price || 0) }}</span>
          <span>{{ formatCurrency(tradeSummary.open_bought_amount || 0) }}</span>
        </div>
      </div>

      <div class="ts-card ts-card-result">
        <div class="ts-card-header">Result</div>
        <div class="ts-card-row ts-card-labels">
          <span>P/L</span>
          <span>P/L%</span>
          <span>Trade Ct</span>
        </div>
        <div class="ts-card-row ts-card-values">
          <span :class="profitLossClass(tradeSummary.profit_loss)">
            {{ formatCurrency(tradeSummary.profit_loss) }}
          </span>
          <span :class="profitLossClass(tradeSummary.percent_profit_loss)">
            {{ formatValue(tradeSummary.percent_profit_loss) }}%
          </span>
          <span>{{ allTradeCount }}</span>
        </div>
      </div>
    </div>
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
  margin-bottom: 16px;
}

.ts-title {
  background: var(--color-terminal-bg);
  color: var(--color-terminal-text);
  text-align: center;
  padding: 8px 12px;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  border: 1px solid var(--color-terminal-border);
  border-radius: 6px;
  margin-bottom: 12px;
}

.ts-symbol {
  color: var(--color-accent-cyan);
}

/* 2x2 on a standard laptop width, collapsing to 1 column as the
   viewport narrows (the page wrapper caps content at 1200px, so this
   never grows past 2 columns even on a wide monitor). */
.ts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(440px, 1fr));
  gap: 14px;
}

.ts-card {
  background: var(--color-terminal-panel);
  border: 1px solid var(--color-terminal-border);
  border-radius: 10px;
  overflow: hidden;
}

.ts-card-header {
  text-align: center;
  padding: 6px 8px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border-bottom-width: 2px;
  border-bottom-style: solid;
}

.ts-card-bought .ts-card-header {
  background: rgba(38, 139, 210, 0.08);
  color: var(--color-long);
  border-bottom-color: var(--color-long);
}

.ts-card-sold .ts-card-header {
  background: rgba(220, 50, 47, 0.08);
  color: var(--color-loss);
  border-bottom-color: var(--color-loss);
}

.ts-card-unsold .ts-card-header {
  background: rgba(133, 153, 0, 0.08);
  color: var(--color-profit);
  border-bottom-color: var(--color-profit);
}

.ts-card-result .ts-card-header {
  background: rgba(203, 75, 22, 0.08);
  color: var(--color-accent-orange);
  border-bottom-color: var(--color-accent-orange);
}

.ts-card-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  text-align: center;
}

.ts-card-row.ts-cols-4 {
  grid-template-columns: repeat(4, 1fr);
}

.ts-card-labels span {
  background: var(--color-terminal-panel);
  color: var(--color-terminal-text-muted);
  padding: 5px 8px;
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  border: 1px solid var(--color-terminal-border-subtle);
}

.ts-card-values span {
  background: var(--color-terminal-surface);
  color: var(--color-terminal-text);
  padding: 7px 8px;
  border: 1px solid var(--color-terminal-border-subtle);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.ts-card-values span:hover {
  background: var(--color-terminal-hover);
}
</style>
