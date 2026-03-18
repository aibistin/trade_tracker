<template>
  <div v-if="total > 0" class="wlb-wrapper">
    <div class="wlb-label">
      <span class="wlb-wins">{{ wins }}W</span>
      <span class="wlb-sep"> / </span>
      <span class="wlb-losses">{{ losses }}L</span>
      <span class="wlb-avg"> · {{ (battingAvg * 100).toFixed(1) }}% win rate</span>
    </div>
    <div class="wlb-track">
      <div class="wlb-fill wlb-fill-win" :style="{ width: winPct + '%' }"></div>
      <div class="wlb-fill wlb-fill-loss" :style="{ width: lossPct + '%' }"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  wins: { type: Number, default: 0 },
  losses: { type: Number, default: 0 },
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
  font-size: 0.78rem;
  margin-bottom: 4px;
}

.wlb-wins {
  color: #198754;
  font-weight: 700;
}

.wlb-losses {
  color: #dc3545;
  font-weight: 700;
}

.wlb-sep {
  color: #6c757d;
}

.wlb-avg {
  color: #495057;
}

.wlb-track {
  height: 6px;
  border-radius: 3px;
  background: #dee2e6;
  display: flex;
  overflow: hidden;
}

.wlb-fill {
  height: 100%;
  transition: width 0.4s ease;
}

.wlb-fill-win {
  background: #198754;
}

.wlb-fill-loss {
  background: #dc3545;
}
</style>
