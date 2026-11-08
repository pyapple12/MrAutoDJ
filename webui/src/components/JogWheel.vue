<!-- 转盘（PL004.2，对齐 ui/jog_wheel 语义）：Canvas 绘制 + 四类交互
     按住拖=搓碟（jog_scratch 像素→样本）；未按住拖=弯音（累积+80ms 归零）；
     Shift+拖=高速搜索（±4 档）；滚轮=弯音格进；vinyl 开关为本地判定态 -->
<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import type { EngineApi } from '../composables/useEngine'
import { useShift } from '../composables/useShift'

const props = defineProps<{
  letter: 'a' | 'b'
  engine: EngineApi
}>()

const { isShift } = useShift()
const canvas = ref<HTMLCanvasElement | null>(null)
const vinyl = ref(true)
const touching = ref(false)

// 换算常量（对齐 ui.json：jog_scratch_gain=256 / jog_bend_step=0.05 /
// jog_search_step=4.0 / jog_bend_reset_ms=80——协议 J2/J3/J4）
const SCRATCH_GAIN = 256
const BEND_STEP = 0.05
const SEARCH_STEP = 4.0
const BEND_RESET_MS = 80
const BEND_MAX = 0.5

let raf = 0
let lastX = 0
let lastY = 0
let lastT = 0
let bendPending = 0
let bendTimer: number | null = null
let searchRate = 0

function deckState() {
  return props.engine.state[props.letter]
}

function draw() {
  // 转盘绘制：外环金属圈 + 内盘 + 播放指示点（角度随 position/duration）
  const c = canvas.value
  if (!c) return
  const ctx = c.getContext('2d')
  if (!ctx) return
  const w = c.width
  const h = c.height
  const cx = w / 2
  const cy = h / 2
  const rOuter = Math.min(cx, cy) - 2
  const rInner = rOuter * 0.72
  ctx.clearRect(0, 0, w, h)
  // 外环
  const ring = ctx.createLinearGradient(0, 0, w, h)
  ring.addColorStop(0, '#3a4356')
  ring.addColorStop(0.5, '#141924')
  ring.addColorStop(1, '#3a4356')
  ctx.beginPath()
  ctx.arc(cx, cy, rOuter, 0, Math.PI * 2)
  ctx.fillStyle = ring
  ctx.fill()
  // 内盘
  ctx.beginPath()
  ctx.arc(cx, cy, rInner, 0, Math.PI * 2)
  ctx.fillStyle = touching.value ? '#1d2432' : '#10141d'
  ctx.fill()
  ctx.strokeStyle = '#2a3242'
  ctx.stroke()
  // 中心柱
  ctx.beginPath()
  ctx.arc(cx, cy, rInner * 0.16, 0, Math.PI * 2)
  ctx.fillStyle = '#2a3242'
  ctx.fill()
  // 播放指示点（转盘角度随播放位置转）
  const d = deckState()
  if (d.duration > 0) {
    const ang = (d.position / d.duration) * Math.PI * 2 - Math.PI / 2
    const px = cx + Math.cos(ang) * rInner * 0.82
    const py = cy + Math.sin(ang) * rInner * 0.82
    ctx.beginPath()
    ctx.arc(px, py, 5, 0, Math.PI * 2)
    ctx.fillStyle = d.state === 'playing' || d.state === 'mixing' ? '#ff7a2f' : '#5a6578'
    ctx.fill()
  }
  raf = requestAnimationFrame(draw)
}

function relPos(ev: PointerEvent) {
  // 指针相对盘心的位置（半径判定盘内）
  const c = canvas.value!
  const rect = c.getBoundingClientRect()
  const x = ev.clientX - rect.left - rect.width / 2
  const y = ev.clientY - rect.top - rect.height / 2
  const r = Math.min(rect.width, rect.height) / 2
  return { x, y, inside: Math.hypot(x, y) <= r }
}

function onDown(ev: PointerEvent) {
  // 按下：盘内即触摸（jog_touch）；记录起点；Shift+拖进入搜索
  const p = relPos(ev)
  if (!p.inside) return
  ;(ev.target as HTMLElement).setPointerCapture(ev.pointerId)
  touching.value = true
  lastX = p.x
  lastY = p.y
  lastT = performance.now()
  props.engine.rpc('jog_touch', { deck: props.letter, on: true })
}

function onMove(ev: PointerEvent) {
  // 拖动：touch+vinyl=搓碟（像素→样本，速度因子 0.5..3）；Shift=搜索；
  // 未触摸拖=弯音（竖直位移累积）
  if (!touching.value) return
  const p = relPos(ev)
  const now = performance.now()
  const dt = Math.max(1, now - lastT)
  const speed = Math.hypot(p.x - lastX, p.y - lastY) / dt * 1000 // px/s
  const gain = SCRATCH_GAIN * Math.max(0.5, Math.min(3.0, speed / 800))
  const dPx = p.x - lastX
  if (isShift(ev)) {
    // SHIFT 高速搜索：方向按水平位移，档位 ±4（松手归零）
    searchRate = dPx > 0 ? SEARCH_STEP : dPx < 0 ? -SEARCH_STEP : 0
    props.engine.rpc('jog_search', { deck: props.letter, rate: searchRate })
  } else if (vinyl.value) {
    // 搓碟：位移累积成样本增量（对齐 scratch_moved 累加语义）
    const delta = Math.round(dPx * gain)
    if (delta !== 0) props.engine.rpc('jog_scratch', { deck: props.letter, delta })
  } else {
    // 弯音：竖直拖累积（对齐 bend 累积语义）
    queueBend((lastY - p.y) * 0.01)
  }
  lastX = p.x
  lastY = p.y
  lastT = now
}

function onUp() {
  // 松开：结束触摸/搜索归零（弯音由 80ms 定时归零）
  if (!touching.value) return
  touching.value = false
  props.engine.rpc('jog_touch', { deck: props.letter, on: false })
  if (searchRate !== 0) {
    searchRate = 0
    props.engine.rpc('jog_search', { deck: props.letter, rate: 0.0 })
  }
}

function queueBend(delta: number) {
  // 弯音累积（同向叠加反向抵消，钳 ±0.5）+ 80ms 无操作归零（UI 同款）
  bendPending = Math.max(-BEND_MAX, Math.min(BEND_MAX, bendPending + delta))
  props.engine.rpc('jog_bend', { deck: props.letter, rate: bendPending })
  if (bendTimer !== null) window.clearTimeout(bendTimer)
  bendTimer = window.setTimeout(() => {
    bendPending = 0
    props.engine.rpc('jog_bend', { deck: props.letter, rate: 0.0 })
  }, BEND_RESET_MS)
}

function onWheel(ev: WheelEvent) {
  // 滚轮弯音：每格 ±0.05（deltaY 向下为负速/倒拉）
  ev.preventDefault()
  const notches = Math.sign(ev.deltaY)
  if (notches !== 0) queueBend(-notches * BEND_STEP)
}

onMounted(() => {
  raf = requestAnimationFrame(draw)
})
onBeforeUnmount(() => cancelAnimationFrame(raf))
</script>

<template>
  <div class="jog-wrap">
    <canvas
      ref="canvas"
      class="jog"
      width="220"
      height="220"
      @pointerdown="onDown"
      @pointermove="onMove"
      @pointerup="onUp"
      @pointercancel="onUp"
      @wheel="onWheel"
    ></canvas>
    <div class="jog-bar">
      <button
        class="vinyl"
        :class="{ on: vinyl }"
        title="Vinyl 模式：开=盘内拖搓碟，关=盘内拖弯音"
        @click="vinyl = !vinyl"
      >
        VINYL
      </button>
      <span class="hint">按住拖=搓碟 · 滚轮/关Vinyl拖=弯音 · Shift+拖=搜索</span>
    </div>
  </div>
</template>

<style scoped>
.jog-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.jog {
  touch-action: none;
  cursor: grab;
  border-radius: 50%;
}
.jog:active {
  cursor: grabbing;
}
.jog-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
button.vinyl.on {
  border-color: var(--accent);
  color: var(--accent);
}
.hint {
  font-size: 12px;
  color: var(--fg-dim);
}
</style>
