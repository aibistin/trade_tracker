<template>
  <div class="sparkline-wrap" :style="{ width: width + 'px', height: height + 'px' }">
    <canvas ref="canvasRef" :width="width" :height="height"></canvas>
    <div v-if="!priceData.length" class="sparkline-empty">
      <span class="text-muted">--</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue'

const props = defineProps({
  priceData: { type: Array, default: () => [] },
  // Array of { date, price, type: 'buy'|'sell' }
  annotations: { type: Array, default: () => [] },
  width: { type: Number, default: 160 },
  height: { type: Number, default: 40 },
  lineColor: { type: String, default: null },
  showArea: { type: Boolean, default: true },
})

const canvasRef = ref(null)

const effectiveLineColor = computed(() => {
  if (props.lineColor) return props.lineColor
  if (props.priceData.length < 2) return '#93a1a1'
  const first = props.priceData[0]?.close ?? props.priceData[0]?.price ?? 0
  const last = props.priceData[props.priceData.length - 1]?.close ?? props.priceData[props.priceData.length - 1]?.price ?? 0
  return last >= first ? '#859900' : '#dc322f'
})

function draw() {
  const canvas = canvasRef.value
  if (!canvas || !props.priceData.length) return

  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  canvas.width = props.width * dpr
  canvas.height = props.height * dpr
  ctx.scale(dpr, dpr)
  ctx.clearRect(0, 0, props.width, props.height)

  const prices = props.priceData.map(d => d.close ?? d.price ?? 0)
  const dates = props.priceData.map(d => d.date ?? d.timestamp ?? '')
  const minP = Math.min(...prices)
  const maxP = Math.max(...prices)
  const range = maxP - minP || 1
  const pad = 2

  function xForIdx(i) {
    return pad + (i / (prices.length - 1)) * (props.width - pad * 2)
  }

  function yForPrice(p) {
    return props.height - pad - ((p - minP) / range) * (props.height - pad * 2)
  }

  // Draw area fill
  if (props.showArea && prices.length > 1) {
    ctx.beginPath()
    ctx.moveTo(xForIdx(0), yForPrice(prices[0]))
    for (let i = 1; i < prices.length; i++) {
      ctx.lineTo(xForIdx(i), yForPrice(prices[i]))
    }
    ctx.lineTo(xForIdx(prices.length - 1), props.height)
    ctx.lineTo(xForIdx(0), props.height)
    ctx.closePath()
    const grad = ctx.createLinearGradient(0, 0, 0, props.height)
    const baseColor = effectiveLineColor.value
    grad.addColorStop(0, baseColor + '30')
    grad.addColorStop(1, baseColor + '05')
    ctx.fillStyle = grad
    ctx.fill()
  }

  // Draw line
  if (prices.length > 1) {
    ctx.beginPath()
    ctx.moveTo(xForIdx(0), yForPrice(prices[0]))
    for (let i = 1; i < prices.length; i++) {
      ctx.lineTo(xForIdx(i), yForPrice(prices[i]))
    }
    ctx.strokeStyle = effectiveLineColor.value
    ctx.lineWidth = 1.5
    ctx.lineJoin = 'round'
    ctx.stroke()
  }

  // Draw annotations (buy/sell markers)
  for (const ann of props.annotations) {
    const dateStr = ann.date ?? ''
    const idx = dates.indexOf(dateStr)
    if (idx === -1) continue

    const x = xForIdx(idx)
    const y = yForPrice(prices[idx])
    const isBuy = ann.type === 'buy'

    // Draw marker
    ctx.beginPath()
    if (isBuy) {
      // Upward triangle for buy
      ctx.moveTo(x, y - 5)
      ctx.lineTo(x - 3.5, y + 2)
      ctx.lineTo(x + 3.5, y + 2)
    } else {
      // Downward triangle for sell
      ctx.moveTo(x, y + 5)
      ctx.lineTo(x - 3.5, y - 2)
      ctx.lineTo(x + 3.5, y - 2)
    }
    ctx.closePath()
    ctx.fillStyle = isBuy ? '#859900' : '#dc322f'
    ctx.fill()
    ctx.strokeStyle = '#002b36'
    ctx.lineWidth = 0.5
    ctx.stroke()
  }
}

watch(() => [props.priceData, props.annotations, props.lineColor], () => {
  draw()
}, { deep: true })

onMounted(() => {
  draw()
})

onBeforeUnmount(() => {
  // Nothing to clean up for raw canvas
})
</script>

<style scoped>
.sparkline-wrap {
  position: relative;
  display: inline-block;
  flex-shrink: 0;
}

.sparkline-wrap canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.sparkline-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
}
</style>
