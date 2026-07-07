<template>
  <div class="heatmap-container">
    <canvas ref="canvasRef"></canvas>
    <div v-if="!hasData" class="heatmap-empty">
      <span class="text-muted">Load live prices to view portfolio heatmap</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { Chart, Tooltip } from 'chart.js'
import { TreemapController, TreemapElement } from 'chartjs-chart-treemap'

Chart.register(TreemapController, TreemapElement, Tooltip)

const props = defineProps({
  holdings: { type: Array, default: () => [] },
  livePrices: { type: Object, default: () => ({}) },
})

const canvasRef = ref(null)
let chartInstance = null

const heatmapData = computed(() => {
  return props.holdings
    .filter(h => props.livePrices[h.symbol]?.price != null)
    .map(h => {
      const price = props.livePrices[h.symbol].price
      const costBasis = h.shares * h.average_price
      const marketValue = h.shares * price
      const pnl = marketValue - costBasis
      const pnlPct = costBasis !== 0 ? (pnl / Math.abs(costBasis)) * 100 : 0
      return {
        symbol: h.symbol,
        tradeType: h.trade_type,
        weight: Math.abs(marketValue),
        pnl,
        pnlPct,
        marketValue,
        costBasis,
      }
    })
    .filter(d => d.weight > 0)
    .sort((a, b) => b.weight - a.weight)
})

const hasData = computed(() => heatmapData.value.length > 0)

function pnlColor(pnlPct) {
  // Clamp intensity between -20% and +20% for color scaling
  const clamped = Math.max(-20, Math.min(20, pnlPct))
  const intensity = Math.abs(clamped) / 20
  if (clamped >= 0) {
    // Green: from near-black to #00c896
    const r = Math.round(5 + 0 * intensity)
    const g = Math.round(30 + (200 - 30) * intensity)
    const b = Math.round(20 + (150 - 20) * intensity)
    return `rgb(${r}, ${g}, ${b})`
  } else {
    // Red: from near-black to #ff4060
    const r = Math.round(40 + (255 - 40) * intensity)
    const g = Math.round(10 + (64 - 10) * intensity * 0.3)
    const b = Math.round(15 + (96 - 15) * intensity * 0.4)
    return `rgb(${r}, ${g}, ${b})`
  }
}

function buildChart() {
  if (!canvasRef.value || !hasData.value) return

  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  const data = heatmapData.value

  chartInstance = new Chart(canvasRef.value, {
    type: 'treemap',
    data: {
      datasets: [{
        tree: data,
        key: 'weight',
        labels: {
          display: true,
          formatter: (ctx) => {
            const d = ctx.raw?._data
            if (!d) return ''
            return [d.symbol, `${d.pnlPct >= 0 ? '+' : ''}${d.pnlPct.toFixed(1)}%`]
          },
          color: '#dce4f0',
          font: [
            { family: 'Inter, sans-serif', size: 13, weight: 'bold' },
            { family: 'Inter, sans-serif', size: 10 },
          ],
        },
        backgroundColor: (ctx) => {
          const d = ctx.raw?._data
          if (!d) return '#1a1e27'
          return pnlColor(d.pnlPct)
        },
        borderColor: '#0d0f13',
        borderWidth: 2,
        spacing: 1,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1a1e27',
          titleColor: '#dce4f0',
          bodyColor: '#dce4f0',
          borderColor: '#262b38',
          borderWidth: 1,
          titleFont: { family: 'Inter, sans-serif', size: 12 },
          bodyFont: { family: 'Inter, sans-serif', size: 11 },
          callbacks: {
            title: (items) => {
              const d = items[0]?.raw?._data
              return d ? d.symbol : ''
            },
            label: (ctx) => {
              const d = ctx.raw?._data
              if (!d) return ''
              return [
                `Market Value: $${d.marketValue.toFixed(2)}`,
                `Cost Basis: $${d.costBasis.toFixed(2)}`,
                `P&L: ${d.pnl >= 0 ? '+' : ''}$${d.pnl.toFixed(2)} (${d.pnlPct >= 0 ? '+' : ''}${d.pnlPct.toFixed(1)}%)`,
              ]
            },
          },
        },
      },
    },
  })
}

watch(heatmapData, () => {
  buildChart()
}, { deep: true })

onMounted(() => {
  if (hasData.value) buildChart()
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})
</script>

<style scoped>
.heatmap-container {
  position: relative;
  height: 300px;
  width: 100%;
}

.heatmap-container canvas {
  width: 100% !important;
  height: 100% !important;
}

.heatmap-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.82rem;
}
</style>
