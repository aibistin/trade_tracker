<template>
  <div class="tc-card" :class="accentClass">
    <!-- Main Summary Row -->
    <div class="tc-row" @click="toggle">
      <div class="tc-cell tc-toggle">
        <span class="tc-chevron" :class="{ 'is-open': expanded }">›</span>
      </div>
      <div class="tc-cell tc-id">{{ trade.trade_id }}-{{ trade.account }}</div>
      <div class="tc-cell tc-type">
        <span class="tc-type-pill" :class="typePillClass">{{ formatTradeType(trade) }}</span>
      </div>
      <div class="tc-cell tc-action">{{ formatAction(trade) }}</div>
      <div class="tc-cell tc-date">{{ formatDate(trade.trade_date) }}</div>
      <div class="tc-cell tc-qty">{{ trade.quantity }}</div>
      <div class="tc-cell tc-price">{{ formatCurrency(trade.price) }}</div>
      <div class="tc-cell tc-basis" :class="profitLossClass(trade.amount)">{{ formatCurrency(trade.amount) }}</div>
      <div class="tc-cell tc-sold-qty">{{ formatValue(trade.current_sold_qty) }}</div>
      <div class="tc-cell tc-sold-amt">{{ formatCurrency(trade.current_sold_amt) }}</div>
      <div class="tc-cell tc-pl" :class="profitLossClass(trade.current_profit_loss)">
        {{ formatCurrency(trade.current_profit_loss) }}
      </div>
      <div class="tc-cell tc-plp" :class="profitLossClass(trade.current_percent_profit_loss)">
        {{ trade.current_percent_profit_loss ? formatValue(trade.current_percent_profit_loss) + '%' : '' }}
      </div>
      <div class="tc-cell tc-status">
        <span class="tc-status-pill" :class="statusPillClass">{{ statusText }}</span>
      </div>
    </div>

    <!-- Option Label (always visible for option trades) -->
    <div v-if="isOption && trade.trade_label" class="tc-option-label">
      <span class="tc-label-icon">◆</span>
      <span class="tc-label-text">{{ trade.trade_label }}</span>
    </div>

    <!-- Expanded Detail Panel -->
    <div v-if="expanded" class="tc-detail">

      <!-- Metrics Bar -->
      <div class="tc-metrics-bar">
        <div class="tc-metric">
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
          <input type="text" v-model="editReason" placeholder="Enter reason…" class="form-control form-control-sm"
            @click.stop />
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
            <button class="btn btn-sm btn-primary tc-save-btn" @click.stop="save" :disabled="saving">{{ saving ?
              'Saving…' : 'Save' }}</button>
            <span v-if="saveStatus" class="tc-save-status" :class="saveStatusClass">{{ saveStatus }}</span>
          </div>
        </div>
      </div>

      <!-- Matched Sell Trades -->
      <div v-if="hasSells" class="tc-sells">
        <div class="tc-sells-header">Matched Sells ({{ trade.sells.length }})</div>
        <table class="table table-sm table-dark table-bordered mb-0 tc-sells-table">
          <thead>
            <tr>
              <th>ID-Acct</th>
              <th>Sell Date</th>
              <th>Qty</th>
              <th>Price</th>
              <th>Cost Amt</th>
              <th>Revenue</th>
              <th>P/L</th>
              <th>P/L%</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="sell in trade.sells" :key="sell.trade_id">
              <td>{{ sell.trade_id }}-{{ sell.account }}</td>
              <td>{{ formatDate(sell.trade_date) }}</td>
              <td>{{ sell.quantity }}</td>
              <td>{{ formatCurrency(sell.price) }}</td>
              <td>{{ formatCurrency(sell.basis_amt) }}</td>
              <td>{{ formatCurrency(sell.amount) }}</td>
              <td :class="profitLossClass(sell.profit_loss)">{{ formatCurrency(sell.profit_loss) }}</td>
              <td :class="profitLossClass(sell.percent_profit_loss)">
                {{ sell.percent_profit_loss ? formatValue(sell.percent_profit_loss) + '%' : '' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  </div>
</template>

<script>
import { formatAction, formatCurrency, formatTradeType, profitLossClass, formatValue, formatDate } from '@/utils/tradeUtils.js';
import { API_BASE_URL } from '@/config.js';

export default {
  props: {
    trade: { type: Object, required: true },
    stockType: { type: String, default: 'Stock' },
  },
  data() {
    return {
      expanded: false,
      editReason: this.trade.reason || '',
      editStopPrice: this.trade.initial_stop_price != null ? String(this.trade.initial_stop_price) : '',
      editTargetSell: this.trade.projected_sell_price != null ? String(this.trade.projected_sell_price) : '',
      saving: false,
      saveStatus: '',
      saveTimer: null,
    };
  },
  computed: {
    isOption() {
      return ['C', 'P', 'O'].includes(this.trade.trade_type);
    },
    hasSells() {
      return Array.isArray(this.trade.sells) && this.trade.sells.length > 0;
    },
    statusText() {
      if (!this.trade.is_done) return 'O';
      return this.trade.current_profit_loss > 0 ? 'W' : this.trade.current_profit_loss < 0 ? 'L' : '-';
    },
    statusPillClass() {
      return this.trade.is_done ? 'tc-closed' : 'tc-open';
    },
    accentClass() {
      const t = this.trade.trade_type;
      if (t === 'C') return 'tc-accent-call';
      if (t === 'P') return 'tc-accent-put';
      if (t === 'L') return 'tc-accent-long';
      if (t === 'S') return 'tc-accent-short';
      return 'tc-accent-other';
    },
    typePillClass() {
      const t = this.trade.trade_type;
      if (t === 'C') return 'pill-call';
      if (t === 'P') return 'pill-put';
      if (t === 'L') return 'pill-long';
      if (t === 'S') return 'pill-short';
      return '';
    },
    saveStatusClass() {
      return this.saveStatus === 'Saved!' ? 'text-success' : 'text-danger';
    },
  },
  methods: {
    formatAction,
    formatCurrency,
    formatTradeType,
    profitLossClass,
    formatValue,
    formatDate,
    toggle() {
      this.expanded = !this.expanded;
    },
    async save() {
      this.saving = true;
      this.saveStatus = '';
      if (this.saveTimer) clearTimeout(this.saveTimer);
      try {
        const payload = {
          reason: this.editReason || null,
          initial_stop_price: this.editStopPrice !== '' ? parseFloat(this.editStopPrice) : null,
          projected_sell_price: this.editTargetSell !== '' ? parseFloat(this.editTargetSell) : null,
        };
        const resp = await fetch(`${API_BASE_URL}/trade/update/${this.trade.trade_id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!resp.ok) {
          const err = await resp.json().catch(() => ({}));
          throw new Error(err.error || 'Save failed');
        }
        this.trade.reason = this.editReason || null;
        this.trade.initial_stop_price = this.editStopPrice !== '' ? parseFloat(this.editStopPrice) : null;
        this.trade.projected_sell_price = this.editTargetSell !== '' ? parseFloat(this.editTargetSell) : null;
        this.saveStatus = 'Saved!';
      } catch (e) {
        this.saveStatus = e.message || 'Error saving';
      } finally {
        this.saving = false;
        this.saveTimer = setTimeout(() => { this.saveStatus = ''; }, 3000);
      }
    },
  },
  beforeUnmount() {
    if (this.saveTimer) clearTimeout(this.saveTimer);
  },
};
</script>

<style scoped>
/* ── Card Container ─────────────────────────────────────────── */
/* Matches Bootstrap table-info row: #cff4fc bg, dark text       */
.tc-card {
  background: #cff4fc;
  border: 1px solid #bacbe3;
  border-left-width: 4px;
  border-radius: 0;
  margin-bottom: 2px;
  overflow: hidden;
  color: #000;
}

/* Trade-type left accent colors */
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

/* ── Main Row Grid ──────────────────────────────────────────── */
.tc-row {
  display: grid;
  grid-template-columns: 28px 100px 60px 75px 90px 65px 80px 95px 75px 95px 95px 70px 70px;
  gap: 6px;
  align-items: center;
  padding: 7px 12px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}

.tc-row:hover {
  background: #bfdaec;
}

.tc-cell {
  font-size: 0.82rem;
  color: #212529;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Chevron Toggle ─────────────────────────────────────────── */
.tc-chevron {
  display: inline-block;
  font-size: 1rem;
  color: #495057;
  transition: transform 0.2s;
}

.tc-chevron.is-open {
  transform: rotate(90deg);
  color: #212529;
}

/* ── Type Pills ─────────────────────────────────────────────── */
.tc-type-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 99px;
  font-size: 0.72rem;
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
  padding: 2px 8px;
  border-radius: 99px;
  font-size: 0.72rem;
  font-weight: 600;
}

.tc-open {
  background: rgba(25, 135, 84, 0.2);
  color: #146c43;
}

.tc-closed {
  background: rgba(108, 117, 125, 0.2);
  color: #495057;
}

/* ── Option Label Sub-row ───────────────────────────────────── */
.tc-option-label {
  padding: 2px 12px 5px 46px;
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
/* Slightly darker than the table-info row */
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

/* ── Sell Trades Sub-table ──────────────────────────────────── */
.tc-sells {
  border-radius: 10px;
  overflow: hidden;
}

.tc-sells-header {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #495057;
  margin-bottom: 6px;
}

.tc-sells-table {
  font-size: 0.8rem;
  border-radius: 0;
  margin-bottom: 0;
}

.tc-sells-table th {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
</style>
