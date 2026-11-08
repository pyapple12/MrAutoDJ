<!-- 拟物背光按钮（PL006.2，对齐 GlowButton 语义）：金属凸面 + LED 背光
     （真辉光 box-shadow blur 超越 QPainter 拟物）+ 按下凹陷态 -->
<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    led?: string | null // LED 色 token 名（'accent'/'accent2'/'glow-green'/'glow-blue'）或 null
    size?: 'sm' | 'md'
  }>(),
  { led: null, size: 'md' },
)

function ledVar(): string | null {
  if (!props.led) return null
  const map: Record<string, string> = {
    accent: 'var(--accent)',
    accent2: 'var(--accent2)',
    'glow-green': 'var(--glow-green)',
    'glow-blue': 'var(--glow-blue)',
  }
  return map[props.led] ?? props.led
}

// CSS 自定义属性样式（vue-tsc 对 --* 键的类型挑剔——显式宽松绑定）
const ledStyle = computed(() => {
  const c = ledVar()
  return c ? ({ '--led': c } as Record<string, string>) : undefined
})
</script>

<template>
  <button class="bl" :class="size + (ledVar() ? ' lit' : '')" :style="ledStyle">
    <slot />
  </button>
</template>

<style scoped>
.bl {
  --led: var(--fg-dim);
  position: relative;
  background: linear-gradient(180deg, color-mix(in srgb, var(--panel) 92%, #ffffff), var(--panel-inset));
  border: 1px solid var(--line);
  border-radius: 6px;
  color: var(--fg);
  padding: 7px 16px;
  font-size: 13px;
  cursor: pointer;
  box-shadow: 0 2px 3px rgba(0, 0, 0, 0.4);
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.5);
}
.bl:active:not(:disabled) {
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.5);
  transform: translateY(1px);
}
.bl.sm {
  padding: 3px 10px;
  font-size: 12px;
}
/* LED 背光：点亮时文字与底部光晕同色（blur 辉光超越 QPainter） */
.bl.lit {
  color: var(--led);
  border-color: color-mix(in srgb, var(--led) 55%, var(--line));
  box-shadow:
    0 2px 3px rgba(0, 0, 0, 0.4),
    0 -6px 14px -4px color-mix(in srgb, var(--led) 65%, transparent) inset,
    0 0 12px -2px color-mix(in srgb, var(--led) 55%, transparent);
}
.bl:disabled {
  filter: grayscale(0.8);
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
