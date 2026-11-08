<!-- 推荐区（PL004.4，对齐 M2 推荐区接线；automix 注入前网关返回 not_ready——
     按钮可用、错误中文化展示，曲库数据层 PL005 接入后激活） -->
<script setup lang="ts">
import { ref } from 'vue'
import type { EngineApi } from '../composables/useEngine'

const props = defineProps<{ engine: EngineApi }>()

const err = ref('')
const recName = ref('--')
const recWhy = ref('AUTO 推荐待曲库数据层接入（PL005）')
const autoOn = ref(false)

async function run(fn: () => Promise<unknown>) {
  err.value = ''
  try {
    await fn()
  } catch (e) {
    err.value = e instanceof Error ? e.message : String(e)
  }
}

const recommend = () =>
  run(async () => {
    const r = (await props.engine.rpc('recommend')) as { name: string; explanation: string }
    recName.value = r.name.slice(0, 12)
    recWhy.value = r.explanation
    await props.engine.rpc('prepare_next')
  })
const toggleAuto = () =>
  run(async () => {
    autoOn.value = !autoOn.value
    await props.engine.rpc('set_automix', { on: autoOn.value })
  })
</script>

<template>
  <section class="recpanel">
    <header class="head">
      <h3>推荐</h3>
      <button class="next" @click="recommend">NEXT</button>
      <button class="auto" :class="{ on: autoOn }" @click="toggleAuto">AUTO</button>
    </header>
    <div class="body">
      <span class="name">{{ recName }}</span>
      <span class="why">{{ recWhy }}</span>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
  </section>
</template>

<style scoped>
.recpanel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.head h3 {
  margin: 0;
  font-size: 13px;
  letter-spacing: 2px;
  color: var(--fg-dim);
  margin-right: auto;
}
.next {
  border-color: var(--accent);
  color: var(--accent);
}
.auto.on {
  background: var(--accent);
  border-color: var(--accent);
  color: #0b0e14;
}
.body {
  display: flex;
  gap: 10px;
  align-items: baseline;
}
.name {
  font-size: 14px;
  font-weight: 600;
  min-width: 96px;
}
.why {
  font-size: 12px;
  color: var(--fg-dim);
}
.err {
  margin: 0;
  font-size: 11px;
  color: #ff6b6b;
}
</style>
