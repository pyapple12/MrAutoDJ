<!-- 拟物金属面板（PL006.2）：拉丝金属纹理（CSS repeating-gradient 各向异性）
     + 内嵌标题铭牌 + 边缘高光线；对齐 PanelFrame 拟物语言 -->
<script setup lang="ts">
defineProps<{
  title?: string
  flush?: boolean // 无标题紧凑模式
}>()
</script>

<template>
  <section class="metal" :class="{ flush }">
    <span v-if="title && !flush" class="plate">{{ title }}</span>
    <slot />
  </section>
</template>

<style scoped>
.metal {
  position: relative;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(0, 0, 0, 0.12)),
    repeating-linear-gradient(
      93deg,
      var(--panel) 0px,
      var(--panel) 2px,
      color-mix(in srgb, var(--panel) 88%, #ffffff) 3px,
      var(--panel) 4px
    );
  border: 1px solid var(--line);
  border-radius: 10px;
  box-shadow:
    inset 0 1px 0 color-mix(in srgb, var(--line) 60%, #ffffff),
    inset 0 -1px 0 rgba(0, 0, 0, 0.4),
    0 2px 8px rgba(0, 0, 0, 0.35);
  padding: 14px 16px;
  padding-top: 34px;
}
.metal.flush {
  padding-top: 14px;
}
.plate {
  position: absolute;
  top: 8px;
  left: 12px;
  font-size: 12px;
  letter-spacing: 0;
  color: var(--fg-dim);
  padding: 3px 12px;
  background: linear-gradient(180deg, var(--panel), var(--panel-inset));
  border: 1px solid var(--line);
  border-radius: 3px;
  text-shadow: 0 1px 0 rgba(0, 0, 0, 0.6);
}
:root[data-theme='light'] .metal {
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -1px 0 color-mix(in srgb, var(--line) 70%, #000000),
    0 2px 6px rgba(0, 0, 0, 0.12);
}
</style>
