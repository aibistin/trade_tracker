<template>
  <div class="cumulative-chart-wrap">
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import {
  Chart, CategoryScale, LinearScale, PointElement,
  LineElement, Filler, Tooltip, Legend
} from 'chart.js'

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const props = defineProps({
  buckets: { type: Array, default: () => [] },
})

const canvasRef = ref(null)
let chartInstance = null

const cumulativeData = computed(() => {
  if (!props.buckets.length) return { labels: [], values: [] }
  const labels = []
  const values = []
  let running = 0
  for (const b of props.buckets) {
    running += b.pnl_dollars
    labels.push(b.label)
    values.push(Math.round(running * 100) / 100)
  }
  return { labels, values }
})

function buildChart() {
  const canvas = canvasRef.value
  if (!canvas || !cumulativeData.value.labels.length) return

  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  const { labels, values } = cumulativeData.value
  const lastVal = values[values.length - 1] ?? 0
  const lineColor = lastVal >= 0 ? '#00c896' : '#ff4060'
  const fillColor = lastVal >= 0 ? 'rgba(0,200,150,0.08)' : 'rgba(255,64,96,0.08)'

  chartInstance = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Cumulative P&L ($)',
        data: values,
        borderColor: lineColor,
        backgroundColor: fillColor,
        pointBackgroundColor: values.map(v => v >= 0 ? '#00c896' : '#ff4060'),
        pointBorderColor: values.map(v => v >= 0 ? '#00c896' : '#ff4060'),
        pointRadius: 3,
        pointHoverRadius: 5,
        borderWidth: 2,
        tension: 0.3,
        fill: true,
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
          titleFont: { family: 'Inter, sans-serif', size: 11 },
          bodyFont: { family: 'Inter, sans-serif', size: 11 },
          callbacks: {
            label: (ctx) => {
              const val = ctx.parsed.y
              return ` Cumulative: ${val >= 0 ? '+' : ''}$${val.toFixed(2)}`
            },
          },
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#6b7a96', font: { family: 'Inter, sans-serif', size: 10 } },
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: {
            color: '#6b7a96',
            font: { family: 'Inter, sans-serif', size: 10 },
            callback: (v) => `$${v.toFixed(0)}`,
          },
        },
      },
    },
  })
}

watch(() => props.buckets, () => {
  buildChart()
}, { deep: true })

onMounted(() => {
  buildChart()
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})
</script>

<style scoped>
.cumulative-chart-wrap {
  position: relative;
  height: 260px;
  width: 100%;
}

.cumulative-chart-wrap canvas {
  width: 100% !important;
  height: 100% !important;
}
</style>
