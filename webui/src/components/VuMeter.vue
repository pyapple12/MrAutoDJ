<!-- VU 灯柱（PL004.3，tick 流驱动）：16 段竖向灯柱，绿→黄→红分区 -->
<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{ vu: number; segments?: number }>(), {
  segments: 16,
})

const litCount = computed(() => Math.round(Math.max(0, Math.min(1, props.vu)) * props.segments))

function colorOf(i: number): string {
  // 分区配色：底部绿 70%、中段黄 20%、顶部红 10%（对齐 LED 灯柱语言）
  const t = i / props.segments
  if (t < 0.7) return '#2fe37a'
  if (t < 0.9) return '#ffd23f'
  return '#ff5555'
}
</script>

<template>
  <div class="vu" role="meter" :aria-valuenow="vu.toFixed(2)">
    <div
      v-for="i in segments"
      :key="i"
      class="seg"
      :class="{ lit: i <= litCount }"
      :style="{ background: i <= litCount ? colorOf(i - 1) : undefined }"
    ></div>
  </div>
</template>

<style scoped>
.vu {
  display: flex;
  flex-direction: column-reverse;
  gap: 2px;
  width: 14px;
  height: 120px;
  padding: 3px;
  background: #0c1018;
  border: 1px solid var(--line);
  border-radius: 4px;
}
.seg {
  flex: 1;
  border-radius: 1px;
  background: #1a2130;
}
.seg.lit {
  box-shadow: 0 0 4px currentColor;
}
</style>
