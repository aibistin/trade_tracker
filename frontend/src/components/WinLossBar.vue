<template>
  <div v-if="total > 0" class="wlb-wrapper">
    <div class="wlb-label">
      <span class="wlb-wins">{{ wins }}W</span>
      <span class="wlb-sep"> / </span>
      <span class="wlb-losses">{{ losses }}L</span>
      <span class="wlb-avg"> &middot; {{ (battingAvg * 100).toFixed(1) }}% win rate</span>
      <span v-if="avgWin != null" class="wlb-detail">
        &middot; avg win <span class="wlb-wins">{{ formatCurrency(avgWin) }}</span>
      </span>
      <span v-if="avgLoss != null" class="wlb-detail">
        / avg loss <span class="wlb-losses">{{ formatCurrency(avgLoss) }}</span>
      </span>
    </div>
    <div class="wlb-track">
      <div class="wlb-fill wlb-fill-win" :style="{ width: winPct + '%' }"></div>
      <div class="wlb-fill wlb-fill-loss" :style="{ width: lossPct + '%' }"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatCurrency } from '@/utils/tradeUtils.js'

const props = defineProps({
  wins: { type: Number, default: 0 },
  losses: { type: Number, default: 0 },
  avgWin: { type: Number, default: null },
  avgLoss: { type: Number, default: null },
})

const total = computed(() => props.wins + props.losses)
const winPct = computed(() => total.value > 0 ? (props.wins / total.value) * 100 : 0)
const lossPct = computed(() => total.value > 0 ? (props.losses / total.value) * 100 : 0)
const battingAvg = computed(() => total.value > 0 ? props.wins / total.value : 0)
</script>

<style scoped>
.wlb-wrapper {
  margin: 0 0 12px 0;
}

.wlb-label {
  font-size: 0.76rem;
  margin-bottom: 4px;
}

.wlb-wins {
  color: var(--color-profit);
  font-weight: 700;
}

.wlb-losses {
  color: var(--color-loss);
  font-weight: 700;
}

.wlb-sep {
  color: var(--color-terminal-text-dim);
}

.wlb-avg {
  color: var(--color-terminal-text-muted);
}

.wlb-detail {
  color: var(--color-terminal-text-muted);
  font-size: 0.73rem;
}

.wlb-track {
  height: 5px;
  border-radius: 3px;
  background: var(--color-terminal-panel);
  display: flex;
  overflow: hidden;
}

.wlb-fill {
  height: 100%;
  transition: width 0.4s ease;
}

.wlb-fill-win {
  background: var(--color-profit);
}

.wlb-fill-loss {
  background: var(--color-loss);
}
</style>
