<template>
  <div class="tc-card" :class="accentClass">

    <!-- Main Summary Row -->
    <div class="tc-row" @click="toggle">
      <span class="tc-chevron" :class="{ 'is-open': expanded }">&#x203A;</span>

      <!-- Identity: ID + type pill -->
      <div class="tc-group tc-group-id">
        <span class="tc-id">{{ trade.trade_id }}-{{ trade.account }}</span>
        <span class="tc-type-pill" :class="typePillClass">{{ formatTradeType(trade) }}</span>
      </div>

      <!-- Dates: Opened (+ Closed when done) -->
      <div class="tc-group tc-group-dates">
        <div class="tc-labeled-val">
          <span class="tc-micro-label">Opened</span>
          <span class="tc-date">{{ formatDate(trade.trade_date) }}</span>
        </div>
        <div v-if="trade.is_done && trade.closed_date" class="tc-labeled-val">
          <span class="tc-micro-label">Closed</span>
          <span class="tc-closed-date">{{ formatDate(trade.closed_date) }}</span>
        </div>
      </div>

      <!-- Flexible data area -->
      <div class="tc-trade-data">
        <div class="tc-group tc-group-position">
          <div class="tc-labeled-val">
            <span class="tc-micro-label">Qty</span>
            <span class="tc-qty">{{ trade.quantity }}</span>
          </div>
          <span class="tc-sep">@</span>
          <div class="tc-labeled-val">
            <span class="tc-micro-label">Price</span>
            <span class="tc-price">{{ formatCurrency(trade.price) }}</span>
          </div>
          <span class="tc-sep">=</span>
          <div class="tc-labeled-val">
            <span class="tc-micro-label">Cost</span>
            <span class="tc-basis">{{ formatCurrency(trade.amount) }}</span>
          </div>
        </div>

        <span class="tc-divider" aria-hidden="true"></span>

        <div class="tc-group tc-group-sold">
          <div class="tc-labeled-val">
            <span class="tc-micro-label">Qty Sold</span>
            <span class="tc-sold-qty">{{ formatValue(trade.current_sold_qty) }}</span>
          </div>
          <span class="tc-sep">/</span>
          <div class="tc-labeled-val">
            <span class="tc-micro-label">Proceeds</span>
            <span class="tc-sold-amt">{{ formatCurrency(trade.current_sold_amt) }}</span>
          </div>
        </div>

        <div class="tc-group tc-group-pl">
          <div class="tc-labeled-val">
            <span class="tc-micro-label">P/L</span>
            <span :class="profitLossClass(trade.current_profit_loss)">
              {{ formatCurrency(trade.current_profit_loss) }}
            </span>
          </div>
          <div class="tc-labeled-val">
            <span class="tc-micro-label">P/L %</span>
            <span class="tc-plp" :class="profitLossClass(trade.current_percent_profit_loss)">
              {{ trade.current_percent_profit_loss ? formatValue(trade.current_percent_profit_loss) + '%' : '' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Status pill -->
      <span class="tc-status-pill" :class="statusPillClass">{{ statusText }}</span>
    </div>

    <!-- Option Label -->
    <div v-if="isOption && trade.trade_label" class="tc-option-label">
      <span class="tc-label-icon">&#x25C6;</span>
      <span class="tc-label-text">{{ trade.trade_label }}</span>
    </div>

    <!-- Expanded Detail Panel -->
    <div v-if="expanded" class="tc-detail">

      <!-- Matched Sell Trades -->
      <div v-if="hasSells" class="tc-sells">
        <div class="tc-sells-title">Matched Sells ({{ trade.sells.length }})</div>
        <div class="tc-sell-row tc-sell-head">
          <span>ID-Acct</span>
          <span>Date</span>
          <span>Qty</span>
          <span>Price</span>
          <span>Basis</span>
          <span>Revenue</span>
          <span>P/L</span>
          <span>P/L %</span>
        </div>
        <div v-for="sell in trade.sells" :key="sell.trade_id" class="tc-sell-row tc-sell-data">
          <span>{{ sell.trade_id }}-{{ sell.account }}</span>
          <span>{{ formatDate(sell.trade_date) }}</span>
          <span>{{ sell.quantity }}</span>
          <span>{{ formatCurrency(sell.price) }}</span>
          <span>{{ formatCurrency(sell.basis_amt) }}</span>
          <span>{{ formatCurrency(sell.amount) }}</span>
          <span :class="profitLossClass(sell.profit_loss)">{{ formatCurrency(sell.profit_loss) }}</span>
          <span :class="profitLossClass(sell.percent_profit_loss)">
            {{ sell.percent_profit_loss ? formatValue(sell.percent_profit_loss) + '%' : '' }}
          </span>
        </div>
      </div>

      <!-- Metrics Bar: live pricing for open trades -->
      <div v-if="!trade.is_done" class="tc-metrics-bar">
        <div class="tc-metric">
          <span class="tc-metric-label">{{ isOption ? 'Option Price' : 'Live Price' }}</span>
          <span v-if="priceLoading" class="tc-metric-value text-muted">...</span>
          <span v-else-if="livePrice != null" class="tc-metric-value">{{ formatCurrency(livePrice) }}</span>
          <span v-else class="tc-metric-value text-muted">--</span>
        </div>
        <div class="tc-metric">
          <span class="tc-metric-label">Cost{{ isOption ? ' (×100)' : '' }}</span>
          <span class="tc-metric-value">{{ formatCurrency(openCost) }}</span>
        </div>
        <div v-if="marketValue != null" class="tc-metric">
          <span class="tc-metric-label">Mkt Value</span>
          <span class="tc-metric-value" :class="profitLossClass(priceDiff)">{{ formatCurrency(marketValue) }}</span>
        </div>
        <div v-if="priceDiff != null" class="tc-metric">
          <span class="tc-metric-label">Diff</span>
          <span class="tc-metric-value" :class="profitLossClass(priceDiff)">{{ formatCurrency(priceDiff) }}</span>
        </div>
        <div v-if="priceDiffPct != null" class="tc-metric">
          <span class="tc-metric-label">Diff %</span>
          <span class="tc-metric-value" :class="profitLossClass(priceDiffPct)">{{ formatValue(priceDiffPct) }}%</span>
        </div>
      </div>

      <!-- Metrics Bar: stop / target / reason (always shown when set) -->
      <div v-if="trade.initial_stop_price || trade.projected_sell_price || trade.reason" class="tc-metrics-bar">
        <div v-if="trade.initial_stop_price" class="tc-metric">
          <span class="tc-metric-label">Stop</span>
          <span class="tc-metric-value text-loss">{{ formatCurrency(trade.initial_stop_price) }}</span>
        </div>
        <div v-if="trade.projected_sell_price" class="tc-metric">
          <span class="tc-metric-label">Target</span>
          <span class="tc-metric-value text-profit">{{ formatCurrency(trade.projected_sell_price) }}</span>
        </div>
        <div v-if="trade.reason" class="tc-metric tc-metric-reason">
          <span class="tc-metric-label">Reason</span>
          <span class="tc-metric-value">{{ trade.reason }}</span>
        </div>
      </div>

      <!-- Edit Form -->
      <div class="tc-edit-form">
        <div class="tc-edit-field">
          <label class="tc-edit-label">Reason</label>
          <input type="text" v-model="editReason" placeholder="Enter reason..." maxlength="500"
            @click.stop />
        </div>
        <div class="tc-edit-field">
          <label class="tc-edit-label">Stop Price</label>
          <input type="number" step="0.01" v-model="editStopPrice" placeholder="0.00"
            @click.stop />
        </div>
        <div class="tc-edit-field">
          <label class="tc-edit-label">Target Sell</label>
          <input type="number" step="0.01" v-model="editTargetSell" placeholder="0.00"
            @click.stop />
        </div>
        <div class="tc-edit-field tc-edit-actions">
          <label class="tc-edit-label">&nbsp;</label>
          <div class="tc-edit-btn-row">
            <button class="btn btn-sm btn-primary tc-save-btn" @click.stop="save" :disabled="saving">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
            <span v-if="saveStatus" class="tc-save-status" :class="saveStatusClass">{{ saveStatus }}</span>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue';
import axios from 'axios';
import { formatCurrency, formatTradeType, profitLossClass, formatValue, formatDate } from '@/utils/tradeUtils.js';
import { API_BASE_URL } from '@/config.js';
import { useStockPrice } from '@/composables/useStockPrice.js';
import { useOptionPrice } from '@/composables/useOptionPrice.js';

const props = defineProps({
  trade: { type: Object, required: true },
  stockType: { type: String, default: 'Stock' },
});

const emit = defineEmits(['trade-updated']);

const expanded = ref(false);
const { price: stockPrice, loading: stockPriceLoading, fetchPrice: fetchStockPrice } = useStockPrice();
const { price: optionPrice, loading: optionPriceLoading, fetchPrice: fetchOptionPrice } = useOptionPrice();

const editReason = ref(props.trade.reason || '');
const editStopPrice = ref(props.trade.initial_stop_price != null ? String(props.trade.initial_stop_price) : '');
const editTargetSell = ref(props.trade.projected_sell_price != null ? String(props.trade.projected_sell_price) : '');
const saving = ref(false);
const saveStatus = ref('');
let saveTimer = null;

const isOption = computed(() => ['C', 'P', 'O'].includes(props.trade.trade_type));
const hasSells = computed(() => Array.isArray(props.trade.sells) && props.trade.sells.length > 0);

// Unified live price: option trades use option price, stock trades use stock price
const livePrice = computed(() => isOption.value ? optionPrice.value : stockPrice.value);
const priceLoading = computed(() => isOption.value ? optionPriceLoading.value : stockPriceLoading.value);

// Open-position metrics (meaningful only for open trades with a live price)
const multiplier = computed(() => isOption.value ? 100 : 1);
const remainingQty = computed(() =>
  Math.max(0, (props.trade.quantity || 0) - (props.trade.current_sold_qty || 0))
);
const openCost = computed(() => props.trade.price * remainingQty.value * multiplier.value);
const marketValue = computed(() => {
  if (livePrice.value == null || props.trade.is_done) return null;
  return livePrice.value * remainingQty.value * multiplier.value;
});
const priceDiff = computed(() => {
  if (marketValue.value == null) return null;
  return marketValue.value - openCost.value;
});
const priceDiffPct = computed(() => {
  if (priceDiff.value == null || openCost.value === 0) return null;
  return (priceDiff.value / openCost.value) * 100;
});

const statusText = computed(() => {
  if (!props.trade.is_done) return 'O';
  const pl = props.trade.current_profit_loss;
  return pl > 0 ? 'W' : pl < 0 ? 'L' : '-';
});

const statusPillClass = computed(() => {
  if (!props.trade.is_done) return 'tc-open';
  const pl = props.trade.current_profit_loss;
  return pl > 0 ? 'tc-win' : pl < 0 ? 'tc-loss' : 'tc-neutral';
});

const accentClass = computed(() => {
  const t = props.trade.trade_type;
  if (t === 'C') return 'tc-accent-call';
  if (t === 'P') return 'tc-accent-put';
  if (t === 'L') return 'tc-accent-long';
  if (t === 'S') return 'tc-accent-short';
  return 'tc-accent-other';
});

const typePillClass = computed(() => {
  const t = props.trade.trade_type;
  if (t === 'C') return 'pill-call';
  if (t === 'P') return 'pill-put';
  if (t === 'L') return 'pill-long';
  if (t === 'S') return 'pill-short';
  return '';
});

const saveStatusClass = computed(() => saveStatus.value === 'Saved!' ? 'text-profit' : 'text-loss');

function toggle() {
  expanded.value = !expanded.value;
  if (expanded.value && !props.trade.is_done && livePrice.value === null) {
    if (isOption.value && props.trade.trade_label) {
      fetchOptionPrice(props.trade.trade_label);
    } else if (!isOption.value && props.trade.symbol) {
      fetchStockPrice(props.trade.symbol);
    }
  }
}

async function save() {
  saving.value = true;
  saveStatus.value = '';
  if (saveTimer) clearTimeout(saveTimer);
  try {
    const fields = {
      reason: editReason.value || null,
      initial_stop_price: editStopPrice.value !== '' ? parseFloat(editStopPrice.value) : null,
      projected_sell_price: editTargetSell.value !== '' ? parseFloat(editTargetSell.value) : null,
    };
    await axios.patch(`${API_BASE_URL}/trade/update/${props.trade.trade_id}`, fields);
    emit('trade-updated', props.trade.trade_id, fields);
    saveStatus.value = 'Saved!';
  } catch (e) {
    saveStatus.value = e.response?.data?.error || e.message || 'Error saving';
  } finally {
    saving.value = false;
    saveTimer = setTimeout(() => { saveStatus.value = ''; }, 3000);
  }
}

onBeforeUnmount(() => {
  if (saveTimer) clearTimeout(saveTimer);
});
</script>

<style scoped>
/* ── Card Container ─────────────────────────────────────────── */
.tc-card {
  background: var(--color-terminal-surface);
  border: 1px solid var(--color-terminal-border-subtle);
  border-left-width: 3px;
  border-radius: 0;
  margin-bottom: 1px;
  overflow: hidden;
}

.tc-accent-long { border-left-color: var(--color-long); }
.tc-accent-short { border-left-color: var(--color-short); }
.tc-accent-call { border-left-color: var(--color-call); }
.tc-accent-put { border-left-color: var(--color-put); }
.tc-accent-other { border-left-color: var(--color-terminal-text-dim); }

/* ── Main Row ───────────────────────────────────────────────── */
.tc-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 14px 8px 12px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}

.tc-row:hover {
  background: var(--color-terminal-hover);
}

/* ── Chevron ────────────────────────────────────────────────── */
.tc-chevron {
  display: inline-block;
  font-size: 1rem;
  color: var(--color-terminal-text-dim);
  flex-shrink: 0;
  transition: transform 0.2s;
  line-height: 1;
}

.tc-chevron.is-open {
  transform: rotate(90deg);
  color: var(--color-accent-cyan);
}

/* ── Labeled Value ────────────────────────────────────────────── */
.tc-labeled-val {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.tc-micro-label {
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-terminal-text-dim);
  white-space: nowrap;
}

/* ── Groups ─────────────────────────────────────────────────── */
.tc-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.tc-group-id { gap: 7px; flex-shrink: 0; }
.tc-group-dates { gap: 12px; flex-shrink: 0; }

.tc-trade-data {
  display: flex;
  align-items: center;
  flex: 1;
  justify-content: space-evenly;
  gap: 8px;
}

.tc-group-position { gap: 6px; }
.tc-group-sold { gap: 6px; }
.tc-group-pl { gap: 14px; }

.tc-sep {
  font-size: 0.75rem;
  color: var(--color-terminal-text-dim);
  align-self: flex-end;
  margin-bottom: 1px;
}

/* ── Text Values ────────────────────────────────────────────── */
.tc-id {
  font-size: 0.8rem;
  color: var(--color-terminal-text-muted);
}

.tc-date {
  font-size: 0.82rem;
  color: var(--color-terminal-text);
  white-space: nowrap;
}

.tc-closed-date {
  font-size: 0.82rem;
  color: var(--color-terminal-text-muted);
  white-space: nowrap;
}

.tc-qty, .tc-price, .tc-basis, .tc-sold-qty, .tc-sold-amt {
  font-size: 0.82rem;
  color: var(--color-terminal-text);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.tc-plp {
  font-size: 0.82rem;
  font-variant-numeric: tabular-nums;
}

/* ── Vertical Divider ───────────────────────────────────────── */
.tc-divider {
  width: 1px;
  height: 28px;
  background: var(--color-terminal-border);
  flex-shrink: 0;
}

/* ── Type Pills ─────────────────────────────────────────────── */
.tc-type-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 99px;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  background: var(--color-terminal-panel);
  color: var(--color-terminal-text-muted);
}

.pill-long { background: rgba(59,130,246,0.15); color: var(--color-long); }
.pill-short { background: rgba(239,68,68,0.15); color: var(--color-short); }
.pill-call { background: rgba(34,197,94,0.15); color: var(--color-call); }
.pill-put { background: rgba(249,115,22,0.15); color: var(--color-put); }

/* ── Status Pills ───────────────────────────────────────────── */
.tc-status-pill {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 99px;
  font-size: 0.7rem;
  font-weight: 700;
  flex-shrink: 0;
}

.tc-open {
  background: var(--color-terminal-panel);
  color: var(--color-terminal-text-muted);
  border: 1px solid var(--color-terminal-border);
}

.tc-win {
  background: rgba(34,197,94,0.2);
  color: var(--color-profit);
}

.tc-loss {
  background: rgba(239,68,68,0.2);
  color: var(--color-loss);
}

.tc-neutral {
  background: var(--color-terminal-panel);
  color: var(--color-terminal-text-dim);
}

/* ── Option Label Sub-row ───────────────────────────────────── */
.tc-option-label {
  padding: 2px 14px 5px 42px;
  font-size: 0.74rem;
  color: var(--color-accent-cyan);
  letter-spacing: 0.03em;
}

.tc-label-icon {
  font-size: 0.55rem;
  margin-right: 5px;
  opacity: 0.5;
}

/* ── Detail Panel ───────────────────────────────────────────── */
.tc-detail {
  border-top: 1px solid var(--color-terminal-border);
  background: var(--color-terminal-panel);
  padding: 12px 16px;
}

/* ── Metrics Bar ────────────────────────────────────────────── */
.tc-metrics-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-top: 12px;
  margin-bottom: 12px;
}

.tc-metric {
  display: flex;
  flex-direction: column;
}

.tc-metric-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-terminal-text-dim);
}

.tc-metric-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-terminal-text);
}

.tc-metric-reason .tc-metric-value {
  font-weight: 400;
  font-style: italic;
}

/* ── Edit Form ──────────────────────────────────────────────── */
.tc-edit-form {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
  margin-bottom: 14px;
  padding: 10px 14px;
  background: var(--color-terminal-bg);
  border-radius: 6px;
  border: 1px solid var(--color-terminal-border-subtle);
}

.tc-edit-field {
  display: flex;
  flex-direction: column;
  min-width: 160px;
}

.tc-edit-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-terminal-text-dim);
  margin-bottom: 3px;
}

.tc-edit-btn-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tc-save-btn {
  min-width: 64px;
}

.tc-save-status {
  font-size: 0.78rem;
}

/* ── Matched Sells ──────────────────────────────────────────── */
.tc-sells {
  border-radius: 6px;
  overflow: hidden;
}

.tc-sells-title {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-terminal-text-dim);
  margin-bottom: 5px;
}

.tc-sell-row {
  display: grid;
  grid-template-columns: 72px 84px 46px 68px 84px 84px 76px 62px;
  gap: 8px;
  padding: 5px 10px;
  align-items: center;
  font-size: 0.78rem;
  font-variant-numeric: tabular-nums;
}

.tc-sell-head {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-terminal-text-dim);
  background: var(--color-terminal-bg);
  border-radius: 4px 4px 0 0;
  padding: 4px 10px;
}

.tc-sell-data {
  background: var(--color-terminal-surface);
  color: var(--color-terminal-text);
  border-top: 1px solid var(--color-terminal-border-subtle);
}

.tc-sell-data:last-child {
  border-radius: 0 0 4px 4px;
}
</style>
