<!-- Automix 面板（PL005.4，扩展 PL004 RecPanel）：NEXT/AUTO/推荐理由 +
     Prepare 状态（烘焙中/完成/失败——prepared 事件帧）+ EQ 渐变进行中提示
     （任一盘 MIXING 态）+ 已播队列（mix_started 事件帧聚合） -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { EngineApi } from '../composables/useEngine'
import MetalPanel from './skeuo/MetalPanel.vue'
import BacklitButton from './skeuo/BacklitButton.vue'
import MiniDisplay from './skeuo/MiniDisplay.vue'

const props = defineProps<{ engine: EngineApi }>()

const err = ref('')
const recName = ref('--')
const recWhy = ref('点击 NEXT 推荐下一曲（需当前盘已知 BPM 与曲库数据）')
const autoOn = ref(false)
const mixing = computed(
  () => props.engine.state.a.state === 'mixing' || props.engine.state.b.state === 'mixing',
)
const preparedText = computed(() => {
  const p = props.engine.state.prepared
  if (props.engine.state.analyzing) return ''
  if (!p) return ''
  return p.ok ? `✓ 已预备 ${p.name}（对侧盘）` : `✗ 预备失败：${p.error}`
})

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
    // NEXT 语义（对齐 UI）：推荐后立即 Prepare 装填（烘焙异步——prepared 事件回显）
    await props.engine.rpc('prepare_next')
  })
const toggleAuto = () =>
  run(async () => {
    autoOn.value = !autoOn.value
    await props.engine.rpc('set_automix', { on: autoOn.value })
  })
const mixNow = () =>
  run(() => props.engine.rpc('mix', { deck: props.engine.state.target }))
</script>

<template>
  <MetalPanel class="automix-panel" title="推荐 / AUTO">
    <div class="recpanel">
    <header class="head">
      <MiniDisplay :text="recName" :warn="recName === '--'" />
      <BacklitButton size="sm" led="accent" @click="recommend">NEXT</BacklitButton>
      <BacklitButton size="sm" :disabled="mixing" title="立即触发转场（当前目标盘 → 预备曲）" @click="mixNow">MIX</BacklitButton>
      <BacklitButton size="sm" :led="autoOn ? 'accent' : null" @click="toggleAuto">AUTO</BacklitButton>
    </header>
    <div class="body">
      <span class="why">{{ recWhy }}</span>
    </div>
    <p class="usage">NEXT 推荐并预备到对侧盘 · MIX 立即触发转场 · AUTO 开启后 Mix 完成自动接歌</p>
    <p v-if="preparedText" class="prepared" :class="{ fail: engine.state.prepared?.ok === false }">
      {{ preparedText }}
    </p>
    <p v-if="mixing" class="mixing-hint">EQ 渐变转场进行中…</p>
    <div v-if="engine.state.playQueue.length" class="queue">
      <span class="q-lab">已播</span>
      <span v-for="(q, i) in engine.state.playQueue.slice(0, 4)" :key="i" class="q-item">
        {{ q.deck.toUpperCase() }}:{{ q.name }}
      </span>
    </div>
    <p v-else class="q-empty">尚无已播曲目（Mix 完成后在此滚动）</p>
    <p v-if="err" class="err">{{ err }}</p>
    </div>
  </MetalPanel>
</template>

<style scoped>
/* 面板弹性填充：body 吃掉与邻居的高度差（panel-void 治理） */
.automix-panel {
  display: flex;
  flex-direction: column;
}
.recpanel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.head :deep(.lcd) {
  margin-right: auto;
}
.body {
  flex: 1;
  display: flex;
  gap: 10px;
  align-items: center;
}
.mini {
  padding: 3px 10px;
  font-size: 12px;
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
.prepared {
  margin: 0;
  font-size: 12px;
  color: var(--glow-green);
}
.usage {
  margin: 0;
  font-size: 12px;
  color: var(--fg-dim);
}
.prepared.fail {
  color: #ff6b6b;
}
.mixing-hint {
  margin: 0;
  font-size: 12px;
  color: var(--accent2);
}
.queue {
  display: flex;
  gap: 8px;
  align-items: center;
  overflow: hidden;
  white-space: nowrap;
}
.q-lab {
  font-size: 12px;
  color: var(--fg-dim);
}
.q-item {
  font-size: 12px;
  color: var(--fg);
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 2px 6px;
}
.q-empty {
  margin: 0;
  font-size: 12px;
  color: var(--fg-dim);
}
.err {
  margin: 0;
  font-size: 12px;
  color: #ff6b6b;
}
</style>
