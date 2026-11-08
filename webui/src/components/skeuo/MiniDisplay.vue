<!-- 拟物小屏（PL006.2，对齐 MiniDisplay 语义）：液晶内嵌屏（内阴影+扫描线+
     等宽数字字体+背光微亮） -->
<script setup lang="ts">
const props = withDefaults(defineProps<{ text?: string; warn?: boolean }>(), {
  text: '--',
  warn: false,
})
</script>

<template>
  <div class="lcd" :class="{ warn }">
    <span class="scan"></span>
    <span class="text">{{ text }}</span>
  </div>
</template>

<style scoped>
.lcd {
  position: relative;
  min-width: 88px;
  padding: 4px 10px;
  background: linear-gradient(180deg, var(--panel-inset), color-mix(in srgb, var(--panel-inset) 88%, #000000));
  border: 1px solid var(--line);
  border-radius: 4px;
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.6);
  overflow: hidden;
  text-align: center;
}
/* 背光微亮（暗室 LCD 观感） */
.lcd::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(122, 200, 255, 0.05), transparent 60%);
  pointer-events: none;
}
/* 扫描线纹理 */
.scan {
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(0deg, transparent 0 2px, rgba(0, 0, 0, 0.12) 2px 3px);
  pointer-events: none;
}
.text {
  position: relative;
  font-family: ui-monospace, monospace;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 1px;
  font-variant-numeric: tabular-nums;
  color: var(--glow-blue);
  text-shadow: 0 0 6px color-mix(in srgb, var(--glow-blue) 70%, transparent);
}
.warn .text {
  color: var(--warning);
  text-shadow: 0 0 6px color-mix(in srgb, var(--warning) 70%, transparent);
}
</style>
