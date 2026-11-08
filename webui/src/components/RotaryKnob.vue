<!-- 旋钮（PL004.3，对齐 ui/widgets/rotary_knob 语义）：SVG 指针旋钮
     纵向拖拽调值 / 双击回默认 / 数值提示（title） -->
<script setup lang="ts">
import { computed, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    min: number
    max: number
    defaultValue?: number
    label?: string
    format?: (v: number) => string
  }>(),
  { defaultValue: 0, label: '' },
)

const emit = defineEmits<{ (e: 'update:modelValue', v: number): void }>()

const value = defineModel<number>({ required: true })
const dragging = ref(false)
const tip = computed(() => (props.format ? props.format(value.value) : value.value.toFixed(2)))

// 角度域（-135°..+135°，对齐拟物旋钮语言）
const angle = computed(() => {
  const t = (value.value - props.min) / (props.max - props.min)
  return -135 + Math.max(0, Math.min(1, t)) * 270
})

function onDown(ev: PointerEvent) {
  // 按下开始拖拽（纵向像素→值域线性映射）
  ;(ev.currentTarget as HTMLElement).setPointerCapture(ev.pointerId)
  dragging.value = true
  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
}

function onMove(ev: PointerEvent) {
  if (!dragging.value) return
  const step = (props.max - props.min) / 150 // 150px 全程
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
  // 双击回默认值（UI 旋钮同款）
  value.value = props.defaultValue
  emit('update:modelValue', props.defaultValue)
}
</script>

<template>
  <div class="knob-wrap" :title="`${label} ${tip}（拖拽调整 · 双击回默认）`">
    <svg viewBox="0 0 64 64" class="knob" @pointerdown="onDown" @dblclick="reset">
      <circle cx="32" cy="32" r="28" class="body" />
      <circle cx="32" cy="32" r="24" class="face" />
      <line
        :x1="32 + 8 * Math.sin((angle * Math.PI) / 180)"
        :y1="32 - 8 * Math.cos((angle * Math.PI) / 180)"
        :x2="32 + 22 * Math.sin((angle * Math.PI) / 180)"
        :y2="32 - 22 * Math.cos((angle * Math.PI) / 180)"
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
  width: 52px;
  height: 52px;
  cursor: ns-resize;
  touch-action: none;
}
.body {
  fill: #1a2030;
  stroke: #2a3242;
}
.face {
  fill: #0f1420;
}
.needle {
  stroke: var(--accent);
  stroke-width: 3;
  stroke-linecap: round;
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
