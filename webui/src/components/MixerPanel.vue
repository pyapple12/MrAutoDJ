<!-- Mixer 区（PL006.2 拟物化）：skeuo Knob（TRIM/EQ）+ VuMeter 辉光灯柱 +
     skeuo Fader（横推）+ MiniDisplay 小屏 + BacklitButton；主音量旋钮；
     PHONES 预听独占切换；交互语义对齐（拖拽+双击回中+数值提示） -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { EngineApi } from '../composables/useEngine'
import MetalPanel from './skeuo/MetalPanel.vue'
import BacklitButton from './skeuo/BacklitButton.vue'
import Knob from './skeuo/Knob.vue'
import Fader from './skeuo/Fader.vue'
import VuMeter from './skeuo/VuMeter.vue'

const props = defineProps<{ engine: EngineApi }>()

const err = ref('')
const masterVol = ref(1.0)
const xfaderPos = ref(0.0)
const faderStart = ref(false)
const phonesVol = ref(1.0)
const phonesBal = ref(0.0)

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
const setPhonesBal = () => run(() => props.engine.rpc('set_phones_balance', { balance: phonesBal.value }))

const xfaderLabel = computed(() => {
  // 横推位置读数（-1=A 全出 / 0=居中 / 1=B 全出）
  const v = xfaderPos.value
  if (v < -0.02) return `A ${Math.abs(v).toFixed(2)}`
  if (v > 0.02) return `B ${v.toFixed(2)}`
  return '居中'
})
</script>

<template>
  <MetalPanel title="MIXER">
    <div class="mixer">
      <div class="ch">
        <div class="knobs">
          <Knob v-model="trim.a" :min="0" :max="2" :default-value="1" label="TRIM A" @update:model-value="setTrim('a')" />
          <Knob v-model="eq.a.low" :min="-1" :max="1" label="低" @update:model-value="setEq('a', 'low')" />
          <Knob v-model="eq.a.mid" :min="-1" :max="1" label="中" @update:model-value="setEq('a', 'mid')" />
          <Knob v-model="eq.a.high" :min="-1" :max="1" label="高" @update:model-value="setEq('a', 'high')" />
        </div>
        <VuMeter :vu="engine.state.a.vu" />
        <BacklitButton size="sm" @click="tap('a')">TAP A</BacklitButton>
      </div>

      <div class="center">
        <BacklitButton
          size="sm"
          :led="faderStart ? 'accent' : null"
          title="Fader Start：横推向对侧时自动播放/暂停"
          @click="faderStart = !faderStart; toggleFaderStart()"
        >
          FS
        </BacklitButton>
        <div class="xfader-row">
          <span class="lab">A</span>
          <Fader v-model="xfaderPos" :min="-1" :max="1" @update:model-value="setXfader" />
          <span class="lab">B</span>
          <span class="val">{{ xfaderLabel }}</span>
        </div>
        <div class="master-row">
          <span class="lab">主音量</span>
          <Knob
            v-model="masterVol"
            :min="0"
            :max="2"
            :default-value="1"
            :size="40"
            label="主"
            :format="(v) => v.toFixed(2)"
            @update:model-value="setMaster"
          />
        </div>
        <div class="phones">
          <BacklitButton
            v-for="d in ['a', 'b'] as const"
            :key="d"
            size="sm"
            :led="engine.state.cue_active === d ? 'glow-green' : null"
            @click="preview(d)"
          >
            CUE {{ d.toUpperCase() }}
          </BacklitButton>
          <span class="lab">音量</span>
          <Knob
            v-model="phonesVol"
            :min="0"
            :max="1"
            :default-value="1"
            :size="32"
            label="监听"
            :format="(v) => v.toFixed(2)"
            @update:model-value="setPhonesVol"
          />
          <Knob
            v-model="phonesBal"
            :min="-1"
            :max="1"
            label="平衡"
            :size="32"
            :format="(v) => (v < -0.02 ? `L ${Math.abs(v).toFixed(2)}` : v > 0.02 ? `R ${v.toFixed(2)}` : '居中')"
            @update:model-value="setPhonesBal"
          />
        </div>
      </div>

      <div class="ch">
        <div class="knobs">
          <Knob v-model="trim.b" :min="0" :max="2" :default-value="1" label="TRIM B" @update:model-value="setTrim('b')" />
          <Knob v-model="eq.b.low" :min="-1" :max="1" label="低" @update:model-value="setEq('b', 'low')" />
          <Knob v-model="eq.b.mid" :min="-1" :max="1" label="中" @update:model-value="setEq('b', 'mid')" />
          <Knob v-model="eq.b.high" :min="-1" :max="1" label="高" @update:model-value="setEq('b', 'high')" />
        </div>
        <VuMeter :vu="engine.state.b.vu" />
        <BacklitButton size="sm" @click="tap('b')">TAP B</BacklitButton>
      </div>

      <p v-if="err" class="err">{{ err }}</p>
    </div>
  </MetalPanel>
</template>

<style scoped>
.mixer {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: var(--sp-3);
  position: relative;
}
/* 手机/平板宽度：单列纵向（A / 中控 / B） */
@media (max-width: 900px) {
  .mixer {
    grid-template-columns: minmax(0, 1fr);
  }
}
.ch {
  display: flex;
  gap: var(--sp-2);
  align-items: center;
  justify-content: center;
}
.knobs {
  display: flex;
  gap: var(--sp-2);
}
.center {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  align-items: stretch;
  min-width: 280px;
}
.xfader-row,
.master-row,
.phones {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}
.master-row {
  justify-content: center;
}
.lab,
.val {
  font-size: 12px;
  color: var(--fg-dim);
  white-space: nowrap;
}
.val {
  font-variant-numeric: tabular-nums;
  color: var(--glow-blue);
}
.err {
  position: absolute;
  bottom: 4px;
  right: 10px;
  margin: 0;
  font-size: 12px;
  color: var(--danger);
}
</style>
