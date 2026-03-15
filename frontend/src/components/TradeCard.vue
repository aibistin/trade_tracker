<template>
  <div class="tc-card" :class="accentClass">

    <!-- Main Summary Row -->
    <div class="tc-row" @click="toggle">
      <span class="tc-chevron" :class="{ 'is-open': expanded }">›</span>

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

      <!-- Flexible data area: spreads proportionally to fill available space -->
      <div class="tc-trade-data">

        <!-- Position: Qty @ Price = Cost -->
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

        <!-- Sold: Qty Sold / Proceeds -->
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

        <!-- P/L amount + percentage -->
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

      </div><!-- /tc-trade-data -->

      <!-- Status pill -->
      <span class="tc-status-pill" :class="statusPillClass">{{ statusText }}</span>
    </div>

    <!-- Option Label (always visible for option trades) -->
    <div v-if="isOption && trade.trade_label" class="tc-option-label">
      <span class="tc-label-icon">◆</span>
      <span class="tc-label-text">{{ trade.trade_label }}</span>
    </div>

    <!-- Expanded Detail Panel -->
    <div v-if="expanded" class="tc-detail">

      <!-- Matched Sell Trades -->
      <div v-if="hasSells" class="tc-sells">
        <div class="tc-sells-title">Matched Sells ({{ trade.sells.length }})</div>
        <div class="tc-sell-row tc-sell-head">
          <span>ID·Acct</span>
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

      <!-- Metrics Bar -->
      <div class="tc-metrics-bar">
        <div v-if="!trade.is_done" class="tc-metric">
          <span class="tc-metric-label">Live Price</span>
          <span class="tc-metric-value text-muted">—</span>
        </div>
        <div v-if="trade.initial_stop_price" class="tc-metric">
          <span class="tc-metric-label">Stop</span>
          <span class="tc-metric-value text-danger">{{ formatCurrency(trade.initial_stop_price) }}</span>
        </div>
        <div v-if="trade.projected_sell_price" class="tc-metric">
          <span class="tc-metric-label">Target</span>
          <span class="tc-metric-value text-success">{{ formatCurrency(trade.projected_sell_price) }}</span>
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
          <input type="text" v-model="editReason" placeholder="Enter reason…" maxlength="500"
            class="form-control form-control-sm" @click.stop />
        </div>
        <div class="tc-edit-field">
          <label class="tc-edit-label">Stop Price</label>
          <input type="number" step="0.01" v-model="editStopPrice" placeholder="0.00"
            class="form-control form-control-sm" @click.stop />
        </div>
        <div class="tc-edit-field">
          <label class="tc-edit-label">Target Sell</label>
          <input type="number" step="0.01" v-model="editTargetSell" placeholder="0.00"
            class="form-control form-control-sm" @click.stop />
        </div>
        <div class="tc-edit-field tc-edit-actions">
          <label class="tc-edit-label">&nbsp;</label>
          <div class="d-flex align-items-center gap-2">
            <button class="btn btn-sm btn-primary tc-save-btn" @click.stop="save" :disabled="saving">
              {{ saving ? 'Saving…' : 'Save' }}
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

const props = defineProps({
  trade: { type: Object, required: true },
  stockType: { type: String, default: 'Stock' },
});

const emit = defineEmits(['trade-updated']);

const expanded = ref(false);
const editReason = ref(props.trade.reason || '');
const editStopPrice = ref(props.trade.initial_stop_price != null ? String(props.trade.initial_stop_price) : '');
const editTargetSell = ref(props.trade.projected_sell_price != null ? String(props.trade.projected_sell_price) : '');
const saving = ref(false);
const saveStatus = ref('');
let saveTimer = null;

const isOption = computed(() => ['C', 'P', 'O'].includes(props.trade.trade_type));
const hasSells = computed(() => Array.isArray(props.trade.sells) && props.trade.sells.length > 0);

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

const saveStatusClass = computed(() => saveStatus.value === 'Saved!' ? 'text-success' : 'text-danger');

function toggle() {
  expanded.value = !expanded.value;
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
  background: #cff4fc;
  border: 1px solid #bacbe3;
  border-left-width: 4px;
  border-radius: 0;
  margin-bottom: 2px;
  overflow: hidden;
  color: #000;
}

.tc-accent-long {
  border-left-color: #0d6efd;
}

.tc-accent-short {
  border-left-color: #dc3545;
}

.tc-accent-call {
  border-left-color: #198754;
}

.tc-accent-put {
  border-left-color: #fd7e14;
}

.tc-accent-other {
  border-left-color: #6c757d;
}

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
  background: #bfdaec;
}

/* ── Chevron ────────────────────────────────────────────────── */
.tc-chevron {
  display: inline-block;
  font-size: 1rem;
  color: #495057;
  flex-shrink: 0;
  transition: transform 0.2s;
  line-height: 1;
}

.tc-chevron.is-open {
  transform: rotate(90deg);
  color: #212529;
}

/* ── Labeled Value (micro-label stacked above value) ────────── */
.tc-labeled-val {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

/* ── Micro Labels ───────────────────────────────────────────── */
.tc-micro-label {
  font-size: 0.62rem;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: #8a9bb0;
  white-space: nowrap;
}

/* ── Groups ─────────────────────────────────────────────────── */
.tc-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.tc-group-id {
  gap: 7px;
  flex-shrink: 0;
}

.tc-group-dates {
  gap: 12px;
  flex-shrink: 0;
}

/* Flexible middle: position + sold + P/L spread proportionally */
.tc-trade-data {
  display: flex;
  align-items: center;
  flex: 1;
  justify-content: space-evenly;
  gap: 8px;
}

.tc-group-position {
  gap: 6px;
}

.tc-group-sold {
  gap: 6px;
}

.tc-group-pl {
  gap: 14px;
}

/* Inline separators (@, =, /) sit at baseline of values */
.tc-sep {
  font-size: 0.75rem;
  color: #9aa3ad;
  align-self: flex-end;
  margin-bottom: 1px;
}

/* ── Text Values ────────────────────────────────────────────── */
.tc-id {
  font-size: 0.8rem;
  color: #212529;
}

.tc-date {
  font-size: 0.82rem;
  color: #212529;
  white-space: nowrap;
}

.tc-closed-date {
  font-size: 0.82rem;
  color: #5a6a7e;
  white-space: nowrap;
}

.tc-qty,
.tc-price,
.tc-basis,
.tc-sold-qty,
.tc-sold-amt {
  font-size: 0.82rem;
  color: #212529;
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
  background: rgba(0, 0, 0, 0.13);
  flex-shrink: 0;
}

/* ── Type Pills ─────────────────────────────────────────────── */
.tc-type-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 99px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  background: rgba(0, 0, 0, 0.1);
  color: #212529;
}

.pill-long {
  background: rgba(13, 110, 253, 0.15);
  color: #0a58ca;
}

.pill-short {
  background: rgba(220, 53, 69, 0.15);
  color: #b02a37;
}

.pill-call {
  background: rgba(25, 135, 84, 0.15);
  color: #146c43;
}

.pill-put {
  background: rgba(253, 126, 20, 0.15);
  color: #ca6510;
}

/* ── Status Pills ───────────────────────────────────────────── */
.tc-status-pill {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 99px;
  font-size: 0.72rem;
  font-weight: 700;
  flex-shrink: 0;
}

.tc-open {
  background: #f8f9fa;
  color: #6c757d;
  border: 1px solid #dee2e6;
}

.tc-win {
  background: #198754;
  color: #fff;
}

.tc-loss {
  background: #dc3545;
  color: #fff;
}

.tc-neutral {
  background: #6c757d;
  color: #fff;
}

/* ── Option Label Sub-row ───────────────────────────────────── */
.tc-option-label {
  padding: 2px 14px 5px 42px;
  font-size: 0.76rem;
  color: #0a58ca;
  letter-spacing: 0.03em;
}

.tc-label-icon {
  font-size: 0.6rem;
  margin-right: 5px;
  opacity: 0.5;
}

/* ── Detail Panel ───────────────────────────────────────────── */
.tc-detail {
  border-top: 1px solid #bacbe3;
  background: #bee5eb;
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
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #495057;
}

.tc-metric-value {
  font-size: 0.88rem;
  font-weight: 600;
  color: #212529;
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
  background: #cff4fc;
  border-radius: 10px;
  border: 1px solid #bacbe3;
}

.tc-edit-field {
  display: flex;
  flex-direction: column;
  min-width: 160px;
}

.tc-edit-label {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #495057;
  margin-bottom: 3px;
}

.tc-save-btn {
  min-width: 64px;
}

.tc-save-status {
  font-size: 0.8rem;
}

/* ── Matched Sells ──────────────────────────────────────────── */
.tc-sells {
  border-radius: 8px;
  overflow: hidden;
}

.tc-sells-title {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: #495057;
  margin-bottom: 5px;
}

.tc-sell-row {
  display: grid;
  grid-template-columns: 72px 84px 46px 68px 84px 84px 76px 62px;
  gap: 8px;
  padding: 5px 10px;
  align-items: center;
  font-size: 0.8rem;
  font-variant-numeric: tabular-nums;
}

.tc-sell-head {
  font-size: 0.67rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #495057;
  background: rgba(0, 0, 0, 0.09);
  border-radius: 6px 6px 0 0;
  padding: 4px 10px;
}

.tc-sell-data {
  background: #e0f4fa;
  color: #000;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.tc-sell-data:last-child {
  border-radius: 0 0 6px 6px;
}
</style>
