<!-- 拟物转盘（PL006.2/PL006.3，升级原 JogWheel）：Canvas 拟物盘（金属外环
     各向异性高光/乙烯基纹路旋转/中心柱镜面）+ 播放指示点 + 四类交互
     （按住拖=搓碟/滚轮+关Vinyl拖=弯音/Shift+拖=搜索/vinyl 本地态）；
     渲染 tick 数据驱动（后台页签 rAF 节流教训——不用 rAF 循环） -->
<script setup lang="ts">
import { onMounted, watch } from 'vue'
import type { EngineApi } from '../../composables/useEngine'
import { useShift } from '../../composables/useShift'

const props = defineProps<{
  letter: 'a' | 'b'
  engine: EngineApi
}>()

const { isShift } = useShift()

const vinyl = defineModel<boolean>('vinyl', { default: true })
const touching = defineModel<boolean>('touching', { default: false })

const SCRATCH_GAIN = 256
const BEND_STEP = 0.05
const SEARCH_STEP = 4.0
const BEND_RESET_MS = 80
const BEND_MAX = 0.5

let lastX = 0
let lastY = 0
let lastT = 0
let bendPending = 0
let bendTimer: number | null = null
let searchRate = 0

function relPos(ev: PointerEvent) {
  const c = document.querySelector(`canvas.jog[data-deck="${props.letter}"]`) as HTMLCanvasElement
  const rect = c.getBoundingClientRect()
  const x = ev.clientX - rect.left - rect.width / 2
  const y = ev.clientY - rect.top - rect.height / 2
  const r = Math.min(rect.width, rect.height) / 2
  return { x, y, inside: Math.hypot(x, y) <= r }
}

function draw() {
  const c = document.querySelector(`canvas.jog[data-deck="${props.letter}"]`) as HTMLCanvasElement | null
  if (!c) return
  const ctx = c.getContext('2d')!
  const w = c.width
  const cx = w / 2
  const cy = w / 2
  const rOuter = cx - 2
  ctx.clearRect(0, 0, w, w)

  // 外环金属（径向+角向高光——各向异性观感超越线性渐变）
  const ring = ctx.createRadialGradient(cx - rOuter * 0.35, cy - rOuter * 0.45, rOuter * 0.1, cx, cy, rOuter)
  ring.addColorStop(0, '#4a5568')
  ring.addColorStop(0.55, '#1a212e')
  ring.addColorStop(0.85, '#2e3848')
  ring.addColorStop(1, '#12161f')
  ctx.beginPath()
  ctx.arc(cx, cy, rOuter, 0, Math.PI * 2)
  ctx.fillStyle = ring
  ctx.fill()
  // 外环边缘高光弧（左上光源）
  ctx.beginPath()
  ctx.arc(cx, cy, rOuter - 1.5, Math.PI * 0.75, Math.PI * 1.75)
  ctx.strokeStyle = 'rgba(255,255,255,0.22)'
  ctx.lineWidth = 2
  ctx.stroke()
  ctx.lineWidth = 1

  // 内盘（乙烯基：黑色基底 + 细纹路随播放位置旋转）
  const rInner = rOuter * 0.7
  const d = props.engine.state[props.letter]
  const rot = d.duration > 0 ? (d.position / d.duration) * Math.PI * 2 : 0
  ctx.save()
  ctx.beginPath()
  ctx.arc(cx, cy, rInner, 0, Math.PI * 2)
  ctx.clip()
  ctx.fillStyle = touching.value ? '#171c26' : '#0c0f16'
  ctx.fillRect(0, 0, w, w)
  // 乙烯基纹路（绕中心放射细线，随 rot 旋转——播放时可见转动）
  ctx.translate(cx, cy)
  ctx.rotate(rot)
  ctx.strokeStyle = 'rgba(255,255,255,0.05)'
  for (let i = 0; i < 36; i++) {
    const a = (i / 36) * Math.PI * 2
    ctx.beginPath()
    ctx.moveTo(Math.cos(a) * rInner * 0.35, Math.sin(a) * rInner * 0.35)
    ctx.lineTo(Math.cos(a) * rInner, Math.sin(a) * rInner)
    ctx.stroke()
  }
  // 高光弧随盘转（增强转动观感）
  ctx.beginPath()
  ctx.arc(0, 0, rInner - 4, -2.6, -1.2)
  ctx.strokeStyle = 'rgba(255,255,255,0.10)'
  ctx.lineWidth = 6
  ctx.stroke()
  ctx.lineWidth = 1
  ctx.restore()

  // 中心柱（镜面金属小圆）
  ctx.beginPath()
  ctx.arc(cx, cy, rInner * 0.14, 0, Math.PI * 2)
  const hub = ctx.createRadialGradient(cx - 2, cy - 3, 1, cx, cy, rInner * 0.14)
  hub.addColorStop(0, '#8a93a5')
  hub.addColorStop(1, '#2a3242')
  ctx.fillStyle = hub
  ctx.fill()

  // 播放指示点（盘缘，随位置转；播放时发主题色辉光）
  if (d.duration > 0) {
    const px = cx + Math.cos(rot - Math.PI / 2) * rInner * 0.82
    const py = cy + Math.sin(rot - Math.PI / 2) * rInner * 0.82
    const playing = d.state === 'playing' || d.state === 'mixing'
    ctx.beginPath()
    ctx.arc(px, py, 5, 0, Math.PI * 2)
    ctx.fillStyle = playing ? '#ff7a2f' : '#5a6578'
    if (playing) {
      ctx.shadowColor = '#ff7a2f'
      ctx.shadowBlur = 10
    }
    ctx.fill()
    ctx.shadowBlur = 0
  }
}

// tick 30Hz 数据驱动（PL006.3：转盘随播放旋转；后台页签也持续更新）
watch(
  () => [props.engine.state[props.letter].position, props.engine.state[props.letter].state],
  () => draw(),
  { flush: 'post' },
)
onMounted(() => draw())

function onDown(ev: PointerEvent) {
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
  if (!touching.value) return
  const p = relPos(ev)
  const now = performance.now()
  const dt = Math.max(1, now - lastT)
  const speed = (Math.hypot(p.x - lastX, p.y - lastY) / dt) * 1000
  const gain = SCRATCH_GAIN * Math.max(0.5, Math.min(3.0, speed / 800))
  const dPx = p.x - lastX
  if (isShift(ev)) {
    searchRate = dPx > 0 ? SEARCH_STEP : dPx < 0 ? -SEARCH_STEP : 0
    props.engine.rpc('jog_search', { deck: props.letter, rate: searchRate })
  } else if (vinyl.value) {
    const delta = Math.round(dPx * gain)
    if (delta !== 0) props.engine.rpc('jog_scratch', { deck: props.letter, delta })
  } else {
    queueBend((lastY - p.y) * 0.01)
  }
  lastX = p.x
  lastY = p.y
  lastT = now
}

function onUp() {
  if (!touching.value) return
  touching.value = false
  props.engine.rpc('jog_touch', { deck: props.letter, on: false })
  if (searchRate !== 0) {
    searchRate = 0
    props.engine.rpc('jog_search', { deck: props.letter, rate: 0.0 })
  }
}

function queueBend(delta: number) {
  bendPending = Math.max(-BEND_MAX, Math.min(BEND_MAX, bendPending + delta))
  props.engine.rpc('jog_bend', { deck: props.letter, rate: bendPending })
  if (bendTimer !== null) window.clearTimeout(bendTimer)
  bendTimer = window.setTimeout(() => {
    bendPending = 0
    props.engine.rpc('jog_bend', { deck: props.letter, rate: 0.0 })
  }, BEND_RESET_MS)
}

function onWheel(ev: WheelEvent) {
  ev.preventDefault()
  const notches = Math.sign(ev.deltaY)
  if (notches !== 0) queueBend(-notches * BEND_STEP)
}

defineExpose({ draw })
</script>

<template>
  <div class="jog-wrap">
    <canvas
      class="jog"
      :data-deck="letter"
      width="220"
      height="220"
      @pointerdown="onDown"
      @pointermove="onMove"
      @pointerup="onUp"
      @pointercancel="onUp"
      @wheel="onWheel"
    ></canvas>
    <div class="jog-bar">
      <slot name="vinyl" />
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
  filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.5));
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
.hint {
  font-size: 12px;
  color: var(--fg-dim);
}
</style>
