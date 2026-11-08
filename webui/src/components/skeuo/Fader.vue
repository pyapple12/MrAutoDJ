<!-- 拟物推子（PL006.2，对齐 FaderSlider 语义）：金属轨槽 + 拟物帽（高光+握位纹）
     纵向/横向；拖拽跟手（60fps pointer 直驱） -->
<script setup lang="ts">
import { computed, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    min: number
    max: number
    vertical?: boolean
    length?: string
  }>(),
  { vertical: false, length: '' },
)

const value = defineModel<number>({ required: true })
const track = ref<HTMLElement | null>(null)
const dragging = ref(false)

const t = computed(() => (value.value - props.min) / (props.max - props.min))

function applyFromEvent(ev: PointerEvent) {
  // 跟手：指针位置 → 值（轨槽几何映射）
  const el = track.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  const frac = props.vertical
    ? 1 - (ev.clientY - rect.top) / rect.height
    : (ev.clientX - rect.left) / rect.width
  value.value = props.min + Math.max(0, Math.min(1, frac)) * (props.max - props.min)
}

function onDown(ev: PointerEvent) {
  dragging.value = true
  ;(track.value as HTMLElement).setPointerCapture?.(ev.pointerId)
  applyFromEvent(ev)
  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
}
function onMove(ev: PointerEvent) {
  if (dragging.value) applyFromEvent(ev)
}
function onUp() {
  dragging.value = false
  window.removeEventListener('pointermove', onMove)
  window.removeEventListener('pointerup', onUp)
}
</script>

<template>
  <div
    ref="track"
    class="fader"
    :class="{ v: vertical, dragging }"
    :style="length ? (vertical ? { height: length } : { width: length }) : undefined"
    @pointerdown="onDown"
  >
    <!-- 轨槽（内嵌阴影） -->
    <div class="slot"></div>
    <!-- 刻度 -->
    <div class="ticks">
      <i v-for="i in 9" :key="i"></i>
    </div>
    <!-- 拟物帽 -->
    <div class="cap" :style="vertical ? { top: `${(1 - t) * 100}%` } : { left: `${t * 100}%` }">
      <span class="line"></span>
    </div>
  </div>
</template>

<style scoped>
.fader {
  position: relative;
  width: 160px;
  max-width: 100%;
  height: 22px;
  cursor: pointer;
  touch-action: none;
  overflow: clip;
}
.fader.v {
  width: 22px;
  height: 160px;
}
.slot {
  position: absolute;
  inset: 8px;
  background: var(--panel-inset);
  border: 1px solid var(--line);
  border-radius: 4px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.55);
}
.v .slot {
  inset: 8px 8px;
}
.ticks i {
  position: absolute;
  background: var(--fg-dim);
  opacity: 0.4;
}
.fader:not(.v) .ticks i {
  top: 2px;
  height: 4px;
  width: 1px;
  left: calc((i - 1) * 12.5%);
}
.fader:not(.v) .ticks i:nth-child(2) { left: 12.5%; }
.fader:not(.v) .ticks i:nth-child(3) { left: 25%; }
.fader:not(.v) .ticks i:nth-child(4) { left: 37.5%; }
.fader:not(.v) .ticks i:nth-child(5) { left: 50%; }
.fader:not(.v) .ticks i:nth-child(6) { left: 62.5%; }
.fader:not(.v) .ticks i:nth-child(7) { left: 75%; }
.fader:not(.v) .ticks i:nth-child(8) { left: 87.5%; }
.fader:not(.v) .ticks i:nth-child(9) { left: 100%; margin-left: -1px; }
.v .ticks i {
  left: 2px;
  width: 4px;
  height: 1px;
  top: calc((i - 1) * 12.5%);
}
.v .ticks i:nth-child(2) { top: 12.5%; }
.v .ticks i:nth-child(3) { top: 25%; }
.v .ticks i:nth-child(4) { top: 37.5%; }
.v .ticks i:nth-child(5) { top: 50%; }
.v .ticks i:nth-child(6) { top: 62.5%; }
.v .ticks i:nth-child(7) { top: 75%; }
.v .ticks i:nth-child(8) { top: 87.5%; }
.v .ticks i:nth-child(9) { top: 100%; margin-top: -1px; }
/* 拟物帽：金属渐变 + 中央标线 + 握位纹 */
.cap {
  position: absolute;
  transform: translate(-50%, -50%);
  width: 18px;
  height: 26px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--panel) 78%, #ffffff), var(--panel-inset));
  border: 1px solid var(--line);
  border-radius: 3px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}
.v .cap {
  width: 26px;
  height: 18px;
}
.cap .line {
  width: 12px;
  height: 2px;
  background: var(--glow-blue);
  box-shadow: 0 0 5px var(--glow-blue);
  border-radius: 1px;
}
.dragging .cap {
  box-shadow:
    0 0 6px rgba(0, 0, 0, 0.55),
    inset 0 0 0 1px rgba(255, 255, 255, 0.12);
}
</style>
