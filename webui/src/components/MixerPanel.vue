<!-- Mixer 区（PL004.3）：TRIM/EQ 旋钮（拖拽+双击回中）、VU 灯柱（tick 驱动）、
     主音量/横推、FaderStart/Tap、PHONES 预听独占切换 -->
<script setup lang="ts">
import { ref } from 'vue'
import type { EngineApi } from '../composables/useEngine'
import RotaryKnob from './RotaryKnob.vue'
import VuMeter from './VuMeter.vue'

const props = defineProps<{ engine: EngineApi }>()

const err = ref('')
const masterVol = ref(1.0)
const xfaderPos = ref(0.0)
const faderStart = ref(false)
const phonesVol = ref(1.0)

// 每盘旋钮本地值（发起指令后由引擎生效；旋钮值即指令参数）
const trim = ref<Record<'a' | 'b', number>>({ a: 1.0, b: 1.0 })
const eq = ref<Record<'a' | 'b', Record<'low' | 'mid' | 'high', number>>>({
  a: { low: 0, mid: 0, high: 0 },
  b: { low: 0, mid: 0, high: 0 },
})

async function run(fn: () => Promise<unknown>) {
  err.value = ''
  try {
    await fn()
  } catch (e) {
    err.value = e instanceof Error ? e.message : String(e)
  }
}

const setTrim = (d: 'a' | 'b') => run(() => props.engine.rpc('set_pregain', { deck: d, gain: trim.value[d] }))
const setEq = (d: 'a' | 'b', band: 'low' | 'mid' | 'high') =>
  run(() => props.engine.rpc('set_eq', { deck: d, band, gain: eq.value[d][band] }))
const setMaster = () => run(() => props.engine.rpc('set_volume', { volume: masterVol.value }))
const setXfader = () => run(() => props.engine.rpc('set_xfader', { position: xfaderPos.value }))
const toggleFaderStart = () => run(() => props.engine.rpc('fader_start', { on: faderStart.value }))
const tap = (d: 'a' | 'b') => run(() => props.engine.rpc('tap', { deck: d }))
const preview = (d: 'a' | 'b') => run(() => props.engine.rpc('phones_preview', { deck: d }))
const setPhonesVol = () => run(() => props.engine.rpc('set_phones_volume', { volume: phonesVol.value }))
</script>

<template>
  <section class="mixer">
    <div class="ch">
      <div class="knobs">
        <RotaryKnob v-model="trim.a" :min="0" :max="2" :default-value="1" label="TRIM A" @update:model-value="setTrim('a')" />
        <RotaryKnob v-model="eq.a.low" :min="-1" :max="1" label="低" @update:model-value="setEq('a', 'low')" />
        <RotaryKnob v-model="eq.a.mid" :min="-1" :max="1" label="中" @update:model-value="setEq('a', 'mid')" />
        <RotaryKnob v-model="eq.a.high" :min="-1" :max="1" label="高" @update:model-value="setEq('a', 'high')" />
      </div>
      <VuMeter :vu="engine.state.a.vu" />
      <button class="tap" @click="tap('a')">TAP A</button>
    </div>

    <div class="center">
      <button
        class="fs"
        :class="{ on: faderStart }"
        title="Fader Start：横推向对侧时自动播放/暂停"
        @click="faderStart = !faderStart; toggleFaderStart()"
      >
        FS
      </button>
      <div class="xfader-row">
        <span class="lab">A</span>
        <input v-model.number="xfaderPos" type="range" min="-1" max="1" step="0.01" @change="setXfader" />
        <span class="lab">B</span>
      </div>
      <div class="master-row">
        <span class="lab">主音量</span>
        <input v-model.number="masterVol" type="range" min="0" max="2" step="0.01" @change="setMaster" />
        <span class="val">{{ masterVol.toFixed(2) }}</span>
      </div>
      <div class="phones">
        <button
          v-for="d in ['a', 'b'] as const"
          :key="d"
          class="cue-btn"
          :class="{ on: engine.state.cue_active === d }"
          @click="preview(d)"
        >
          CUE {{ d.toUpperCase() }}
        </button>
        <span class="lab">音量</span>
        <input v-model.number="phonesVol" type="range" min="0" max="1" step="0.01" @change="setPhonesVol" />
      </div>
    </div>

    <div class="ch">
      <div class="knobs">
        <RotaryKnob v-model="trim.b" :min="0" :max="2" :default-value="1" label="TRIM B" @update:model-value="setTrim('b')" />
        <RotaryKnob v-model="eq.b.low" :min="-1" :max="1" label="低" @update:model-value="setEq('b', 'low')" />
        <RotaryKnob v-model="eq.b.mid" :min="-1" :max="1" label="中" @update:model-value="setEq('b', 'mid')" />
        <RotaryKnob v-model="eq.b.high" :min="-1" :max="1" label="高" @update:model-value="setEq('b', 'high')" />
      </div>
      <VuMeter :vu="engine.state.b.vu" />
      <button class="tap" @click="tap('b')">TAP B</button>
    </div>

    <p v-if="err" class="err">{{ err }}</p>
  </section>
</template>

<style scoped>
.mixer {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 14px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px 16px;
  position: relative;
}
.ch {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: center;
}
.knobs {
  display: flex;
  gap: 8px;
}
.center {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: stretch;
  min-width: 260px;
}
.xfader-row,
.master-row,
.phones {
  display: flex;
  align-items: center;
  gap: 8px;
}
.xfader-row input,
.master-row input,
.phones input {
  flex: 1;
  accent-color: var(--accent);
}
.lab,
.val {
  font-size: 11px;
  color: var(--fg-dim);
  white-space: nowrap;
}
.val {
  font-variant-numeric: tabular-nums;
}
button.fs,
button.tap,
button.cue-btn {
  padding: 4px 12px;
  font-size: 11px;
}
button.fs.on,
button.cue-btn.on {
  background: var(--accent);
  border-color: var(--accent);
  color: #0b0e14;
}
button.cue-btn.on {
  background: #2fe37a;
  border-color: #2fe37a;
}
.err {
  position: absolute;
  bottom: 4px;
  right: 10px;
  margin: 0;
  font-size: 11px;
  color: #ff6b6b;
}
</style>
