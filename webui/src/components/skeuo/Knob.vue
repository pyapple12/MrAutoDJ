<!-- 拟物旋钮（PL006.2，升级 RotaryKnob）：SVG 金属帽（径向渐变+高光弧）+
     刻度环 + 发光指针；交互语义对齐（纵向拖拽/双击回默认/禁用灰显） -->
<script setup lang="ts">
import { computed, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    min: number
    max: number
    defaultValue?: number
    label?: string
    format?: (v: number) => string
    size?: number
  }>(),
  { defaultValue: 0, label: '', size: 0 },
)

const emit = defineEmits<{ (e: 'update:modelValue', v: number): void }>()
const value = defineModel<number>({ required: true })
const dragging = ref(false)
const tip = computed(() => (props.format ? props.format(value.value) : value.value.toFixed(2)))
const t = computed(() => Math.max(0, Math.min(1, (value.value - props.min) / (props.max - props.min))))
const angle = computed(() => -135 + t.value * 270)
const sz = computed(() => (props.size ? `${props.size}px` : 'var(--knob-mixer, 52px)'))

function onDown(ev: PointerEvent) {
  ;(ev.currentTarget as HTMLElement).setPointerCapture(ev.pointerId)
  dragging.value = true
  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
}
function onMove(ev: PointerEvent) {
  if (!dragging.value) return
  const step = (props.max - props.min) / 150
  const v = Math.max(props.min, Math.min(props.max, value.value - ev.movementY * step))
  value.value = v
  emit('update:modelValue', v)
}
function onUp() {
  dragging.value = false
  window.removeEventListener('pointermove', onMove)
  window.removeEventListener('pointerup', onUp)
}
function reset() {
  value.value = props.defaultValue
  emit('update:modelValue', props.defaultValue)
}

// 刻度环（11 格，-135°..+135°）
const ticks = Array.from({ length: 11 }, (_, i) => -135 + i * 27)
</script>

<template>
  <div class="knob-wrap" :title="`${label} ${tip}（拖拽调整 · 双击回默认）`">
    <svg :width="sz" :height="sz" viewBox="0 0 64 64" class="knob" :class="{ dragging }" @pointerdown="onDown" @dblclick="reset">
      <!-- 刻度环 -->
      <g class="ticks">
        <line
          v-for="a in ticks"
          :key="a"
          :x1="32 + 26 * Math.sin((a * Math.PI) / 180)"
          :y1="32 - 26 * Math.cos((a * Math.PI) / 180)"
          :x2="32 + 29 * Math.sin((a * Math.PI) / 180)"
          :y2="32 - 29 * Math.cos((a * Math.PI) / 180)"
        />
      </g>
      <!-- 金属帽：径向渐变 + 顶部高光弧 -->
      <defs>
        <radialGradient id="knobMetal" cx="38%" cy="30%" r="75%">
          <stop offset="0%" stop-color="color-mix(in srgb, var(--panel) 82%, #ffffff)" />
          <stop offset="55%" stop-color="var(--panel)" />
          <stop offset="100%" stop-color="var(--panel-inset)" />
        </radialGradient>
      </defs>
      <circle cx="32" cy="32" r="24" fill="url(#knobMetal)" stroke="var(--line)" />
      <path d="M 12 24 A 22 22 0 0 1 44 11" fill="none" class="hl-arc" />
      <!-- 发光指针 -->
      <line
        :x1="32 + 5 * Math.sin((angle * Math.PI) / 180)"
        :y1="32 - 5 * Math.cos((angle * Math.PI) / 180)"
        :x2="32 + 19 * Math.sin((angle * Math.PI) / 180)"
        :y2="32 - 19 * Math.cos((angle * Math.PI) / 180)"
        class="needle"
      />
    </svg>
    <span class="klabel">{{ label }}</span>
    <span class="kval">{{ tip }}</span>
  </div>
</template>

<style scoped>
.knob-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  user-select: none;
}
.knob {
  cursor: ns-resize;
  touch-action: none;
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.45));
}
.ticks line {
  stroke: var(--fg-dim);
  stroke-width: 1.5;
  opacity: 0.55;
}
.hl-arc {
  stroke: rgba(255, 255, 255, 0.28);
  stroke-width: 2;
  fill: none;
}
.needle {
  stroke: var(--glow-blue);
  stroke-width: 3.5;
  stroke-linecap: round;
  filter: drop-shadow(0 0 4px var(--glow-blue));
  /* PL008.10 指示联动：拖拽中辉光增强（指针即操作反馈） */
  transition: filter 80ms ease;
}
.knob.dragging .needle {
  filter: drop-shadow(0 0 9px var(--glow-blue)) drop-shadow(0 0 3px #ffffff);
}
.klabel {
  font-size: 12px;
  color: var(--fg-dim);
}
.kval {
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  color: var(--fg);
}
</style>
