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

// Blends from the page background (#002b36) toward the profit/loss accent
// color as |P&L%| grows, so a 0% cell reads as background and intensifies
// from there — clamped between -20% and +20% for the color scale.
function pnlColor(pnlPct) {
  const clamped = Math.max(-20, Math.min(20, pnlPct))
  const intensity = Math.abs(clamped) / 20
  const bg = [0, 43, 54]
  const target = clamped >= 0 ? [133, 153, 0] : [220, 50, 47] // profit green / loss red
  const [r, g, b] = bg.map((c, i) => Math.round(c + (target[i] - c) * intensity))
  return `rgb(${r}, ${g}, ${b})`
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
          color: '#eee8d5',
          font: [
            { family: 'Inter, sans-serif', size: 13, weight: 'bold' },
            { family: 'Inter, sans-serif', size: 10 },
          ],
        },
        backgroundColor: (ctx) => {
          const d = ctx.raw?._data
          if (!d) return '#073642'
          return pnlColor(d.pnlPct)
        },
        borderColor: '#002b36',
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
          backgroundColor: '#073642',
          titleColor: '#eee8d5',
          bodyColor: '#eee8d5',
          borderColor: '#586e75',
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
