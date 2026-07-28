<template>
  <div class="tc-card" :class="accentClass">

    <!-- Header Bar -->
    <div class="tc-header" @click="toggle">
      <div class="tc-header-left">
        <span class="tc-chevron" :class="{ 'is-open': expanded }">&#x203A;</span>
        <span class="tc-id">{{ trade.trade_id }}-{{ trade.account }}</span>
        <span class="tc-type-pill" :class="typePillClass">{{ formatTradeType(trade) }}</span>
        <span class="tc-date-range">
          {{ formatDate(trade.trade_date) }} &rarr; {{ trade.is_done && trade.closed_date ? formatDate(trade.closed_date) : 'Open' }}
        </span>
      </div>
      <span class="tc-status-pill" :class="statusPillClass">{{ statusText }}</span>
    </div>

    <!-- Option Label -->
    <div v-if="isOption && trade.trade_label" class="tc-option-label">
      <span class="tc-label-icon">&#x25C6;</span>
      <span class="tc-label-text">{{ trade.trade_label }}</span>
    </div>

    <div class="tc-body">
      <!-- Position -->
      <div class="tc-chip-row tc-divider-bottom">
        <div class="tc-chip">
          <span class="tc-chip-label">Qty</span>
          <span class="tc-chip-value">{{ trade.quantity }}</span>
        </div>
        <div class="tc-chip">
          <span class="tc-chip-label">Price</span>
          <span class="tc-chip-value">{{ formatCurrency(trade.price) }}</span>
        </div>
        <div class="tc-chip">
          <span class="tc-chip-label">Cost</span>
          <span class="tc-chip-value">{{ formatCurrency(trade.amount) }}</span>
        </div>
      </div>

      <!-- Result -->
      <div class="tc-chip-row">
        <div class="tc-chip">
          <span class="tc-chip-label">Qty Sold</span>
          <span class="tc-chip-value">{{ formatValue(trade.current_sold_qty) }}</span>
        </div>
        <div class="tc-chip">
          <span class="tc-chip-label">Proceeds</span>
          <span class="tc-chip-value">{{ formatCurrency(trade.current_sold_amt) }}</span>
        </div>
        <div class="tc-chip">
          <span class="tc-chip-label">P/L</span>
          <span class="tc-chip-value" :class="profitLossClass(trade.current_profit_loss)">
            {{ formatCurrency(trade.current_profit_loss) }}
          </span>
        </div>
        <div class="tc-chip">
          <span class="tc-chip-label">P/L %</span>
          <span class="tc-chip-value" :class="profitLossClass(trade.current_percent_profit_loss)">
            {{ trade.current_percent_profit_loss ? formatValue(trade.current_percent_profit_loss) + '%' : '' }}
          </span>
        </div>
      </div>

      <!-- Expanded Sections -->
      <template v-if="expanded">

        <!-- Matched Sell Trades -->
        <div v-if="hasSells" class="tc-subsection">
          <div class="tc-subsection-title">Matched Sells ({{ trade.sells.length }})</div>
          <div v-for="(sell, i) in trade.sells" :key="sell.trade_id"
            class="tc-chip-row" :class="{ 'tc-divider-bottom': i < trade.sells.length - 1 }">
            <div class="tc-chip">
              <span class="tc-chip-label">{{ sell.trade_id }}-{{ sell.account }}</span>
              <span class="tc-chip-value">{{ formatDate(sell.trade_date) }}</span>
            </div>
            <div class="tc-chip">
              <span class="tc-chip-label">Qty</span>
              <span class="tc-chip-value">{{ sell.quantity }}</span>
            </div>
            <div class="tc-chip">
              <span class="tc-chip-label">Price</span>
              <span class="tc-chip-value">{{ formatCurrency(sell.price) }}</span>
            </div>
            <div class="tc-chip">
              <span class="tc-chip-label">Basis</span>
              <span class="tc-chip-value">{{ formatCurrency(sell.basis_amt) }}</span>
            </div>
            <div class="tc-chip">
              <span class="tc-chip-label">Revenue</span>
              <span class="tc-chip-value">{{ formatCurrency(sell.amount) }}</span>
            </div>
            <div class="tc-chip">
              <span class="tc-chip-label">P/L</span>
              <span class="tc-chip-value" :class="profitLossClass(sell.profit_loss)">
                {{ formatCurrency(sell.profit_loss) }}
                {{ sell.percent_profit_loss ? '· ' + formatValue(sell.percent_profit_loss) + '%' : '' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Live Pricing: open trades only -->
        <div v-if="!trade.is_done" class="tc-subsection">
          <div class="tc-subsection-title">Live Pricing</div>
          <div class="tc-chip-row">
            <div class="tc-chip">
              <span class="tc-chip-label">{{ isOption ? 'Option Price' : 'Live Price' }}</span>
              <span v-if="priceLoading" class="tc-chip-value text-muted">...</span>
              <span v-else-if="livePrice != null" class="tc-chip-value">{{ formatCurrency(livePrice) }}</span>
              <span v-else class="tc-chip-value text-muted">--</span>
            </div>
            <div class="tc-chip">
              <span class="tc-chip-label">Cost{{ isOption ? ' (×100)' : '' }}</span>
              <span class="tc-chip-value">{{ formatCurrency(openCost) }}</span>
            </div>
            <div v-if="marketValue != null" class="tc-chip">
              <span class="tc-chip-label">Mkt Value</span>
              <span class="tc-chip-value" :class="profitLossClass(priceDiff)">{{ formatCurrency(marketValue) }}</span>
            </div>
            <div v-if="priceDiff != null" class="tc-chip">
              <span class="tc-chip-label">Diff</span>
              <span class="tc-chip-value" :class="profitLossClass(priceDiff)">{{ formatCurrency(priceDiff) }}</span>
            </div>
            <div v-if="priceDiffPct != null" class="tc-chip">
              <span class="tc-chip-label">Diff %</span>
              <span class="tc-chip-value" :class="profitLossClass(priceDiffPct)">{{ formatValue(priceDiffPct) }}%</span>
            </div>
          </div>
        </div>

        <!-- Notes: stop / target / reason, shown when set -->
        <div v-if="trade.initial_stop_price || trade.projected_sell_price || trade.reason" class="tc-subsection">
          <div class="tc-subsection-title">Notes</div>
          <div class="tc-chip-row">
            <div v-if="trade.initial_stop_price" class="tc-chip">
              <span class="tc-chip-label">Stop</span>
              <span class="tc-chip-value text-loss">{{ formatCurrency(trade.initial_stop_price) }}</span>
            </div>
            <div v-if="trade.projected_sell_price" class="tc-chip">
              <span class="tc-chip-label">Target</span>
              <span class="tc-chip-value text-profit">{{ formatCurrency(trade.projected_sell_price) }}</span>
            </div>
            <div v-if="trade.reason" class="tc-chip tc-chip-reason">
              <span class="tc-chip-label">Reason</span>
              <span class="tc-chip-value">{{ trade.reason }}</span>
            </div>
          </div>
        </div>

        <!-- Edit -->
        <div class="tc-subsection">
          <div class="tc-subsection-title">Edit</div>
          <div class="tc-chip-row">
            <div class="tc-chip">
              <span class="tc-chip-label">Reason</span>
              <input type="text" v-model="editReason" placeholder="Enter reason..." maxlength="500" @click.stop />
            </div>
            <div class="tc-chip">
              <span class="tc-chip-label">Stop Price</span>
              <input type="number" step="0.01" v-model="editStopPrice" placeholder="0.00" @click.stop />
            </div>
            <div class="tc-chip">
              <span class="tc-chip-label">Target Sell</span>
              <input type="number" step="0.01" v-model="editTargetSell" placeholder="0.00" @click.stop />
            </div>
          </div>
          <div class="tc-edit-actions">
            <button class="btn btn-sm btn-primary tc-save-btn" @click.stop="save" :disabled="saving">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
            <span v-if="saveStatus" class="tc-save-status" :class="saveStatusClass">{{ saveStatus }}</span>
          </div>
        </div>

      </template>
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
  border: 1px solid var(--color-terminal-border);
  border-left-width: 3px;
  border-radius: 10px;
  overflow: hidden;
}

.tc-accent-long { border-left-color: var(--color-long); }
.tc-accent-short { border-left-color: var(--color-short); }
.tc-accent-call { border-left-color: var(--color-call); }
.tc-accent-put { border-left-color: var(--color-put); }
.tc-accent-other { border-left-color: var(--color-terminal-text-dim); }

/* ── Header Bar ─────────────────────────────────────────────── */
.tc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  border-bottom: 1px solid var(--color-terminal-border);
  transition: background 0.15s;
}

.tc-header:hover {
  background: var(--color-terminal-hover);
}

.tc-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex-wrap: wrap;
  row-gap: 2px;
}

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

.tc-id {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-terminal-text);
  white-space: nowrap;
}

.tc-date-range {
  font-size: 0.72rem;
  color: var(--color-terminal-text-muted);
  white-space: nowrap;
}

/* ── Type / Status Pills ────────────────────────────────────── */
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
  padding: 6px 12px 0;
  font-size: 0.74rem;
  color: var(--color-accent-cyan);
  letter-spacing: 0.03em;
}

.tc-label-icon {
  font-size: 0.55rem;
  margin-right: 5px;
  opacity: 0.5;
}

/* ── Body / Chip Rows ───────────────────────────────────────── */
.tc-body {
  padding: 2px 12px 8px;
}

.tc-chip-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 20px;
  padding: 8px 0;
}

.tc-chip-row.tc-divider-bottom {
  border-bottom: 1px dashed var(--color-terminal-border-subtle);
}

.tc-chip {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.tc-chip-label {
  font-size: 0.62rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-terminal-text-dim);
  white-space: nowrap;
}

.tc-chip-value {
  font-size: 0.82rem;
  color: var(--color-terminal-text);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.tc-chip-reason {
  flex: 1 1 200px;
}

.tc-chip-reason .tc-chip-value {
  white-space: normal;
  font-style: italic;
  color: var(--color-terminal-text-muted);
}

/* ── Sections: Matched Sells / Live Pricing / Notes / Edit ──── */
.tc-subsection {
  margin-top: 4px;
  padding-top: 8px;
  border-top: 1px solid var(--color-terminal-border);
}

.tc-subsection-title {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-terminal-text-muted);
}

/* ── Edit Inputs ────────────────────────────────────────────── */
.tc-chip input {
  width: 100%;
  box-sizing: border-box;
  min-width: 140px;
}

.tc-edit-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-top: 8px;
}

.tc-save-btn {
  min-width: 64px;
}

.tc-save-status {
  font-size: 0.78rem;
}
</style>
