<!-- 波形视图（PL005.3）：单 Canvas 三层分层绘制
     ① 峰值波形（min/max 垂线，播放头左侧已播高亮/右侧暗）
     ② 下拍网格竖线（load 响应 downbeats 秒→x）
     ③ 播放头（tick 30Hz 驱动——watch position 同步绘制，
        不依赖 rAF：后台页签 rAF 节流会导致画面冻结） -->
<script setup lang="ts">
import { onMounted, watch } from 'vue'
import type { EngineApi, WaveData } from '../composables/useEngine'

const props = defineProps<{
  letter: 'a' | 'b'
  engine: EngineApi
  wave: WaveData | null
}>()

const ACCENT: Record<string, string> = { a: '#2f8bff', b: '#ff7a2f' }

function draw() {
  const c = document.querySelector(`canvas.wave[data-deck="${props.letter}"]`) as HTMLCanvasElement | null
  if (!c) return
  const ctx = c.getContext('2d')
  if (!ctx) return
  const w = c.width
  const h = c.height
  ctx.clearRect(0, 0, w, h)
  const wave = props.wave
  if (!wave || wave.peaks.length === 0) {
    ctx.fillStyle = '#2a3242'
    ctx.font = '11px system-ui'
    ctx.textAlign = 'center'
    ctx.fillText('载入曲目后显示波形', w / 2, h / 2)
    return
  }
  const deck = props.engine.state[props.letter]
  const cols = wave.peaks.length / 2 // (width, 2) 交错
  const mid = h / 2
  const amp = h / 2 - 4
  // ① 峰值层：播放头位置分色（秒→列映射按 duration）
  const posSec = deck.position
  const playedX = wave.duration > 0 ? (posSec / wave.duration) * w : 0
  for (let i = 0; i < cols; i++) {
    const x = (i / cols) * w
    const mn = wave.peaks[i * 2]
    const mx = wave.peaks[i * 2 + 1]
    const yTop = mid - Math.max(-1, Math.min(1, mx)) * amp
    const yBot = mid - Math.max(-1, Math.min(1, mn)) * amp
    ctx.strokeStyle = x <= playedX ? ACCENT[props.letter] ?? '#2f8bff' : '#39445c'
    ctx.beginPath()
    ctx.moveTo(x, yTop)
    ctx.lineTo(x, Math.max(yBot, yTop + 1))
    ctx.stroke()
  }
  // ② 下拍网格层（秒→x；仅画可见域内）
  ctx.strokeStyle = 'rgba(122, 132, 153, 0.35)'
  for (const sec of wave.downbeats) {
    const x = (sec / wave.duration) * w
    if (x < 0 || x > w) continue
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, h)
    ctx.stroke()
  }
  // ③ 播放头 + 拖尾（PL008.10：播放头后 24px 渐隐尾迹——滚动观感增强）
  const tail = ctx.createLinearGradient(playedX, 0, playedX + 24, 0)
  tail.addColorStop(0, 'rgba(232, 237, 247, 0.35)')
  tail.addColorStop(1, 'rgba(232, 237, 247, 0)')
  ctx.fillStyle = tail
  ctx.fillRect(playedX, 0, Math.min(24, w - playedX), h)
  ctx.strokeStyle = '#e8edf7'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(playedX, 0)
  ctx.lineTo(playedX, h)
  ctx.stroke()
  ctx.lineWidth = 1
}

// tick 30Hz 数据驱动重绘（position 变化即画；wave 更新同样触发）
watch(
  () => [props.engine.state[props.letter].position, props.wave],
  () => draw(),
  { flush: 'post' },
)
onMounted(() => draw())
</script>

<template>
  <canvas
    ref="canvas"
    class="wave"
    width="1200"
    height="96"
    :data-deck="letter"
    :data-wave-path="wave ? wave.path : 'none'"
  ></canvas>
</template>

<style scoped>
.wave {
  width: 100%;
  height: 96px;
  display: block;
  background: #0c1018;
  border: 1px solid var(--line);
  border-radius: 6px;
}
</style>
