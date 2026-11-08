<!-- 拟物 VU 灯柱（PL006.2/PL006.3）：分段辉光 LED（阈值色分带，ui.json
     led_*_threshold 配置驱动）+ 峰值保持衰减（peak-hold 1.2s/段 60fps 衰减） -->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    vu: number
    segments?: number
    peakHoldMs?: number
  }>(),
  { segments: 12, peakHoldMs: 1200 },
)

// 分段色带（阈值 ui.json led_green/yellow_threshold，CSS 变量 --led-green/--led-yellow）
function colorOf(t: number): string {
  if (t < 0.6) return 'var(--glow-green)'
  if (t < 0.85) return 'var(--warning)'
  return 'var(--danger)'
}

const litCount = computed(() => Math.round(Math.max(0, Math.min(1, props.vu)) * props.segments))

// 峰值保持：vu 达到新峰记录段位 + 定时按帧衰减（60fps 下滑）
const peakSeg = ref(0)
let decayTimer: number | null = null
let peakTime = 0

watch(
  () => props.vu,
  (v) => {
    const seg = Math.round(Math.max(0, Math.min(1, v)) * props.segments)
    if (seg >= peakSeg.value) {
      peakSeg.value = seg
      peakTime = performance.now()
    }
    if (decayTimer === null) {
      decayTimer = window.setInterval(() => {
        // 峰值保持 peakHoldMs 后每 60ms 降一段（对齐 VU 机械衰减观感）
        if (performance.now() - peakTime > props.peakHoldMs && peakSeg.value > litCount.value) {
          peakSeg.value = Math.max(litCount.value, peakSeg.value - 1)
          peakTime = performance.now() - props.peakHoldMs + 60
        }
        if (peakSeg.value <= litCount.value && performance.now() - peakTime > props.peakHoldMs) {
          window.clearInterval(decayTimer!)
          decayTimer = null
        }
      }, 60)
    }
  },
)
onBeforeUnmount(() => {
  if (decayTimer !== null) window.clearInterval(decayTimer)
})
</script>

<template>
  <div class="vu" role="meter" :aria-valuenow="vu.toFixed(2)">
    <div
      v-for="i in segments"
      :key="i"
      class="seg"
      :class="{ lit: i <= litCount, peak: i === peakSeg && i > litCount }"
      :style="{ '--seg-color': colorOf((i - 1) / segments) }"
    ></div>
  </div>
</template>

<style scoped>
.vu {
  display: flex;
  flex-direction: column-reverse;
  gap: 2px;
  width: 16px;
  height: 120px;
  padding: 3px;
  background: var(--panel-inset);
  border: 1px solid var(--line);
  border-radius: 4px;
  box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.55);
}
.seg {
  flex: 1;
  border-radius: 1px;
  background: color-mix(in srgb, var(--seg-color) 14%, var(--panel-inset));
}
/* 点亮：辉光（blur 光晕） */
.seg.lit {
  background: var(--seg-color);
  box-shadow:
    0 0 5px color-mix(in srgb, var(--seg-color) 75%, transparent),
    0 0 2px color-mix(in srgb, var(--seg-color) 90%, transparent);
}
/* 峰值保持段：半亮 */
.seg.peak {
  background: color-mix(in srgb, var(--seg-color) 55%, var(--panel-inset));
}
</style>
