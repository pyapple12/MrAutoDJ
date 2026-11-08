<!-- Beat FX 区（PL004.4，对齐 beat_fx_widget + _apply_beat_fx 语义）：
     效果组 HPF/LPF/Trans/Echo/Delay、通道 1/2/both、拍数、深度、FX ON、
     状态小屏、AUTO/TAP；fx 全量状态由网关 tick 回显（协议 F1-F5） -->
<script setup lang="ts">
import { ref, watch } from 'vue'
import type { EngineApi } from '../composables/useEngine'
import MetalPanel from './skeuo/MetalPanel.vue'
import BacklitButton from './skeuo/BacklitButton.vue'
import MiniDisplay from './skeuo/MiniDisplay.vue'
import Knob from './skeuo/Knob.vue'

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
  <MetalPanel title="BEAT FX">
    <div class="fxpanel">
    <header class="head">
      <MiniDisplay :text="statusText()" :warn="!engine.state.fx.on" />
    </header>
    <div class="row">
      <BacklitButton
        v-for="fx in FX_TYPES"
        :key="fx"
        size="sm"
        :led="effect === fx && on ? 'accent' : null"
        @click="selectFx(fx)"
      >
        {{ fx }}
      </BacklitButton>
      <BacklitButton size="sm" :led="on ? 'accent2' : null" @click="toggleOn">{{ on ? 'ON' : 'OFF' }}</BacklitButton>
    </div>
    <div class="row">
      <span class="lab">通道</span>
      <BacklitButton
        v-for="ch in ['1', '2', 'both'] as const"
        :key="ch"
        size="sm"
        :led="channel === ch ? 'accent2' : null"
        @click="setChannel(ch)"
      >
        {{ ch === 'both' ? '1+2' : ch }}
      </BacklitButton>
      <span class="lab">拍数</span>
      <select v-model.number="beats" @change="applyBeats">
        <option v-for="b in [1, 2, 3, 4, 8]" :key="b" :value="b">{{ b }}</option>
      </select>
      <BacklitButton size="sm" @click="fxAuto">AUTO</BacklitButton>
      <BacklitButton size="sm" @click="fxTap">TAP</BacklitButton>
    </div>
    <div class="row">
      <Knob
        v-model="depth"
        :min="0"
        :max="1"
        :default-value="0.3"
        :size="40"
        label="深度"
        :format="(v) => v.toFixed(2)"
        @update:model-value="applyDepth"
      />
    </div>
    <p v-if="err" class="err">{{ err }}</p>
    </div>
  </MetalPanel>
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
  font-size: 12px;
}
.row input[type='range'] {
  flex: 1;
  accent-color: var(--accent);
}
.lab,
.val {
  font-size: 12px;
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
  font-size: 12px;
  color: #ff6b6b;
}
</style>
