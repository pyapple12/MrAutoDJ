<!-- Beat FX 区（PL004.4，对齐 beat_fx_widget + _apply_beat_fx 语义）：
     效果组 HPF/LPF/Trans/Echo/Delay、通道 1/2/both、拍数、深度、FX ON、
     状态小屏、AUTO/TAP；fx 全量状态由网关 tick 回显（协议 F1-F5） -->
<script setup lang="ts">
import { ref, watch } from 'vue'
import type { EngineApi } from '../composables/useEngine'

const props = defineProps<{ engine: EngineApi }>()

const FX_TYPES = ['HPF', 'LPF', 'Trans', 'Echo', 'Delay']
const err = ref('')
const effect = ref('')
const depth = ref(0.3)
const on = ref(false)
const channel = ref<'1' | '2' | 'both'>('1')
const beats = ref(4)
const syncFromTick = ref(false)

// tick 回显 → 面板状态（仅当用户未在拖动时跟随；防回环）
watch(
  () => props.engine.state.fx,
  (fx) => {
    if (syncFromTick.value) return
    effect.value = fx.effect
    depth.value = fx.depth
    on.value = fx.on
    channel.value = fx.channel as '1' | '2' | 'both'
    beats.value = fx.beats
  },
  { deep: true },
)

async function run(fn: () => Promise<unknown>) {
  err.value = ''
  syncFromTick.value = true // 本次用户操作期间不被 tick 回显覆盖
  try {
    await fn()
  } catch (e) {
    err.value = e instanceof Error ? e.message : String(e)
  } finally {
    window.setTimeout(() => (syncFromTick.value = false), 300)
  }
}

const selectFx = (fx: string) =>
  run(async () => {
    effect.value = fx
    on.value = true
    await props.engine.rpc('set_fx', { effect: fx, depth: depth.value, on: true })
  })
const toggleOn = () =>
  run(async () => {
    on.value = !on.value
    await props.engine.rpc('set_fx', { effect: effect.value, depth: depth.value, on: on.value })
  })
const applyDepth = () =>
  run(() => props.engine.rpc('set_fx', { effect: effect.value, depth: depth.value, on: on.value }))
const setChannel = (ch: '1' | '2' | 'both') =>
  run(async () => {
    channel.value = ch
    await props.engine.rpc('set_fx_channel', { channel: ch })
  })
const applyBeats = () => run(() => props.engine.rpc('set_fx_beats', { beats: beats.value }))
const fxAuto = () => run(() => props.engine.rpc('fx_auto', {}))
const fxTap = () => run(() => props.engine.rpc('fx_tap', {}))

function statusText(): string {
  // 状态小屏（J0.7：效果/拍数/通道一目了然）
  const fx = props.engine.state.fx
  if (!fx.on || !fx.effect) return 'FX OFF'
  const chLabel = { '1': 'A', '2': 'B', both: 'A+B' }[fx.channel] ?? 'A'
  return `${fx.effect} ${fx.beats}拍 ${chLabel}`
}
</script>

<template>
  <section class="fxpanel">
    <header class="head">
      <h3>BEAT FX</h3>
      <span class="status">{{ statusText() }}</span>
    </header>
    <div class="row">
      <button
        v-for="fx in FX_TYPES"
        :key="fx"
        class="fx-btn"
        :class="{ sel: effect === fx }"
        @click="selectFx(fx)"
      >
        {{ fx }}
      </button>
      <button class="onoff" :class="{ on }" @click="toggleOn">{{ on ? 'ON' : 'OFF' }}</button>
    </div>
    <div class="row">
      <span class="lab">通道</span>
      <button
        v-for="ch in ['1', '2', 'both'] as const"
        :key="ch"
        class="ch-btn"
        :class="{ sel: channel === ch }"
        @click="setChannel(ch)"
      >
        {{ ch === 'both' ? '1+2' : ch }}
      </button>
      <span class="lab">拍数</span>
      <select v-model.number="beats" @change="applyBeats">
        <option v-for="b in [1, 2, 3, 4, 8]" :key="b" :value="b">{{ b }}</option>
      </select>
      <button class="mini" @click="fxAuto">AUTO</button>
      <button class="mini" @click="fxTap">TAP</button>
    </div>
    <div class="row">
      <span class="lab">深度</span>
      <input v-model.number="depth" type="range" min="0" max="1" step="0.01" @change="applyDepth" />
      <span class="val">{{ depth.toFixed(2) }}</span>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
  </section>
</template>

<style scoped>
.fxpanel {
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
  align-items: baseline;
  justify-content: space-between;
}
.head h3 {
  margin: 0;
  font-size: 13px;
  letter-spacing: 2px;
  color: var(--fg-dim);
}
.status {
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  color: var(--accent);
}
.row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.fx-btn.sel {
  border-color: var(--accent);
  color: var(--accent);
}
.onoff.on {
  background: var(--accent);
  border-color: var(--accent);
  color: #0b0e14;
}
.ch-btn.sel {
  border-color: var(--accent2);
  color: var(--accent2);
}
.mini {
  padding: 3px 10px;
  font-size: 11px;
}
.row input[type='range'] {
  flex: 1;
  accent-color: var(--accent);
}
.lab,
.val {
  font-size: 11px;
  color: var(--fg-dim);
}
.val {
  font-variant-numeric: tabular-nums;
}
select {
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 4px;
  color: var(--fg);
  padding: 3px 6px;
}
.err {
  margin: 0;
  font-size: 11px;
  color: #ff6b6b;
}
</style>
