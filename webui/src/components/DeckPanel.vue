<!-- 打碟机面板（PL004.2 全量对齐）：载入/传输/CUE/进度 + Jog 转盘 +
     TEMPO 推子（量程循环+Pitch 反显）/Keylock/Key Shift/Sync/循环键行/
     表演键（SLIP/CENSOR/STUTTER）/Instant Doubles + Pad×8 五模式 -->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { DeckState, EngineApi } from '../composables/useEngine'
import MetalPanel from './skeuo/MetalPanel.vue'
import BacklitButton from './skeuo/BacklitButton.vue'
import Fader from './skeuo/Fader.vue'
import JogWheel from './skeuo/JogWheel.vue'
import PadBank from './PadBank.vue'
import WaveformView from './WaveformView.vue'

const props = defineProps<{
  letter: 'a' | 'b'
  engine: EngineApi
}>()

const deck = computed<DeckState>(() => props.engine.state[props.letter])
const pathInput = ref('')
const lastPath = ref('')
const busy = ref(false)
const errMsg = ref('')
const tempoV = ref(0) // TEMPO 推子 -1..1（rate = 1 + v*range/100）
const syncFromTick = ref(false)

const range = computed(() => props.engine.state.tempo_range[props.letter] ?? 6)
const rangeLabel = computed(() => (range.value >= 100 ? 'WIDE' : `±${range.value}%`))
const pitchPct = computed(() => (deck.value.tempo_rate - 1.0) * 100)

function fmtTime(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds || 0))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

async function run(fn: () => Promise<unknown>) {
  if (busy.value) return
  busy.value = true
  errMsg.value = ''
  try {
    await fn()
  } catch (e) {
    errMsg.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}

// tick 回显 TEMPO 帽位（用户操作 300ms 内不覆盖，防回环）
watch(
  () => deck.value.tempo_rate,
  (r) => {
    if (syncFromTick.value) return
    const v = Math.max(-1, Math.min(1, (r - 1.0) / (range.value / 100)))
    tempoV.value = Number(v.toFixed(3))
  },
)

const loadTrack = () =>
  run(async () => {
    const p = pathInput.value.trim()
    if (!p) {
      errMsg.value = '请先输入音频文件路径'
      return
    }
    await props.engine.rpc('load', { deck: props.letter, path: p })
    lastPath.value = p
    // 波形请求由 useEngine load 成功钩子自动发出（PL005.3）
  })

// 拖拽装载（曲库行 dragstart text/mrautodj-path → drop 装载）
const onDrop = (ev: DragEvent) =>
  run(async () => {
    const p = ev.dataTransfer?.getData('text/mrautodj-path')
    if (!p) return
    ev.preventDefault()
    await props.engine.rpc('load', { deck: props.letter, path: p })
    lastPath.value = p
  })
const togglePlay = () =>
  run(() => props.engine.rpc(deck.value.paused ? 'play' : 'pause', { deck: props.letter }))
const doCue = () => run(() => props.engine.rpc('cue', { deck: props.letter }))
const doSeek = (ev: Event) =>
  run(() => props.engine.rpc('seek', { deck: props.letter, seconds: Number((ev.target as HTMLInputElement).value) }))

// TEMPO 推子（skeuo Fader）：拖拽实时更新 tempoV → 发乐速倍率；手动解除 Sync（协议 D1）
watch(
  tempoV,
  (v) => {
    if (syncFromTick.value) return
    const rate = 1.0 + v * (range.value / 100)
    void props.engine.rpc('set_tempo_rate', { deck: props.letter, rate })
  },
)
const cycleRange = () => run(() => props.engine.rpc('cycle_tempo_range', { deck: props.letter }))

// Keylock / Key Shift / Sync
const toggleKeylock = () => run(() => props.engine.rpc('set_keylock', { deck: props.letter, on: !deck.value.keylock }))
const shiftSemi = (delta: number) =>
  run(() =>
    props.engine.rpc('set_key_shift', {
      deck: props.letter,
      semitones: delta === 0 ? 0 : deck.value.key_shift + delta,
    }),
  )
const toggleSync = () =>
  run(() => props.engine.rpc('set_sync', { deck: props.letter, on: !props.engine.state.sync[props.letter] }))

// 循环键行（协议 D4-D6）
const toggleLoop = () => run(() => props.engine.rpc('set_loop', { deck: props.letter, on: !deck.value.loop }))
const loopAction = (action: string) => run(() => props.engine.rpc('loop', { deck: props.letter, action }))
const beatloop4 = () => run(() => props.engine.rpc('beatloop', { deck: props.letter, beats: 4 }))

// 表演键（协议 P3-P4）+ Instant Doubles（M4）
const toggleSlip = () => run(() => props.engine.rpc('slip', { deck: props.letter, on: !deck.value.slip }))
const censorOn = ref(false)
const toggleCensorOn = () =>
  run(async () => {
    // censor 灯态引擎不回显（无 getter）——按钮按发 on=!on 本地翻转
    await props.engine.rpc('censor', { deck: props.letter, on: !censorOn.value })
    censorOn.value = !censorOn.value
  })
const stutter = () => run(() => props.engine.rpc('stutter', { deck: props.letter }))
const instantDoubles = () =>
  run(async () => {
    if (!lastPath.value) {
      errMsg.value = '当前盘未装载曲目'
      return
    }
    await props.engine.rpc('instant_doubles', { deck: props.letter, path: lastPath.value })
  })

const stateText = computed(() =>
  deck.value.state === 'playing' ? '播放中' : deck.value.state === 'mixing' ? '混音中' : '空闲',
)
</script>

<template>
  <MetalPanel
    class="deck-panel"
    :class="{ target: engine.state.target === letter }"
    :title="`DECK ${letter.toUpperCase()}`"
    @dragover.prevent
    @drop="onDrop"
  >
    <header class="deck-head">
      <span class="badge" :class="deck.state">{{ stateText }}</span>
      <span v-if="engine.state.target === letter" class="target-mark">目标盘</span>
      <BacklitButton size="sm" title="复制当前曲目到另一盘同位置（Instant Doubles）" @click="instantDoubles">
        ⧉ Doubles
      </BacklitButton>
      <BacklitButton
        size="sm"
        :led="engine.state.target === letter ? 'accent2' : null"
        title="设为目标盘（mix/prepare 的 now 盘）"
        @click="engine.rpc('set_target', { deck: letter })"
      >
        设目标
      </BacklitButton>
    </header>

    <div class="load-row">
      <input v-model="pathInput" type="text" placeholder="音频文件路径（如 E:\\music\\song.mp3）" :disabled="busy" />
      <BacklitButton :led="null" :disabled="busy" @click="loadTrack">
        {{ busy ? '载入中…' : '载入' }}
      </BacklitButton>
    </div>

    <div class="jog-tempo">
      <JogWheel :letter="letter" :engine="engine" />
      <div class="tempo-col">
        <div class="tempo-head">
          <BacklitButton size="sm" led="accent2" @click="cycleRange">{{ rangeLabel }}</BacklitButton>
          <span class="pitch">{{ `Pitch ${pitchPct >= 0 ? '+' : ''}${pitchPct.toFixed(1)}%` }}</span>
        </div>
        <Fader v-model="tempoV" :min="-1" :max="1" />
        <div class="keys-row">
          <BacklitButton size="sm" :led="deck.keylock ? 'accent' : null" @click="toggleKeylock">KEYLOCK</BacklitButton>
          <BacklitButton size="sm" title="移调 -1" @click="shiftSemi(-1)">KEY−</BacklitButton>
          <BacklitButton size="sm" title="复位移调" @click="shiftSemi(0)">KEY0</BacklitButton>
          <BacklitButton size="sm" title="移调 +1" @click="shiftSemi(1)">KEY+</BacklitButton>
          <span class="ks">{{ deck.key_shift > 0 ? `+${deck.key_shift}` : deck.key_shift }}</span>
        </div>
        <BacklitButton size="sm" :led="engine.state.sync[letter] ? 'glow-blue' : null" @click="toggleSync">
          SYNC
        </BacklitButton>
      </div>
    </div>

    <div class="transport-row">
      <BacklitButton
        :led="deck.state === 'playing' || deck.state === 'mixing' ? 'accent2' : null"
        :disabled="busy"
        @click="togglePlay"
      >
        {{ deck.paused ? '播放' : '暂停' }}
      </BacklitButton>
      <BacklitButton :disabled="busy" @click="doCue">CUE</BacklitButton>
      <span class="bpm">{{ deck.bpm > 0 ? deck.bpm.toFixed(1) + ' BPM' : '--- BPM' }}</span>
      <span class="eff" v-if="deck.bpm > 0 && deck.tempo_rate !== 1">→ {{ (deck.bpm * deck.tempo_rate).toFixed(1) }}</span>
    </div>

    <WaveformView :letter="letter" :engine="engine" :wave="engine.waveFor(engine.state.deckPath[letter] || '')" />

    <div class="progress-row">
      <span>{{ fmtTime(deck.position) }}</span>
      <input
        class="seek"
        type="range"
        min="0"
        :max="Math.max(deck.duration, 0.1)"
        step="0.1"
        :value="deck.position"
        :disabled="deck.duration <= 0 || busy"
        @change="doSeek"
      />
      <span>{{ fmtTime(deck.duration) }}</span>
    </div>

    <div class="loop-row">
      <BacklitButton size="sm" :led="deck.loop ? 'accent' : null" @click="toggleLoop">循环</BacklitButton>
      <BacklitButton size="sm" title="循环入点" @click="loopAction('in')">IN</BacklitButton>
      <BacklitButton size="sm" title="循环出点并激活" @click="loopAction('out')">OUT</BacklitButton>
      <BacklitButton size="sm" title="从当前位置起 4 拍循环" @click="beatloop4">4BEAT</BacklitButton>
      <BacklitButton size="sm" title="循环减半" @click="loopAction('halve')">◀</BacklitButton>
      <BacklitButton size="sm" title="循环加倍" @click="loopAction('double')">▶</BacklitButton>
    </div>

    <div class="perf-row">
      <BacklitButton size="sm" :led="deck.slip ? 'accent' : null" title="滑行：表演后松手落回真实位置" @click="toggleSlip">
        SLIP
      </BacklitButton>
      <BacklitButton size="sm" :led="censorOn ? 'var(--danger)' : null" title="消音" @click="toggleCensorOn">
        CENSOR
      </BacklitButton>
      <BacklitButton size="sm" title="结巴重复" @click="stutter">STUTTER</BacklitButton>
    </div>

    <PadBank :letter="letter" :engine="engine" />

    <p v-if="errMsg" class="err">{{ errMsg }}</p>
  </MetalPanel>
</template>

<style scoped>
.deck-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0; /* grid 1fr 子项防 min-content 撑爆列宽 */
}
/* 目标盘：橙色描边高亮（覆盖 MetalPanel 边框） */
.deck-panel.target {
  border-color: var(--accent2);
  box-shadow:
    0 0 0 1px var(--accent2),
    0 2px 10px -2px color-mix(in srgb, var(--accent2) 45%, transparent);
}
.deck-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.badge {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 99px;
  border: 1px solid var(--line);
  color: var(--fg-dim);
}
.badge.playing {
  color: var(--accent);
  border-color: var(--accent);
}
.badge.mixing {
  color: var(--accent2);
  border-color: var(--accent2);
}
.target-mark {
  font-size: 12px;
  color: var(--accent2);
}
.mini {
  padding: 3px 10px;
  font-size: 12px;
}
.mini.on {
  background: var(--accent);
  border-color: var(--accent);
  color: #0b0e14;
}
button.range {
  border-color: var(--accent2);
  color: var(--accent2);
}
.load-row {
  display: flex;
  gap: 8px;
}
.load-row input {
  flex: 1;
}
.jog-tempo {
  display: grid;
  grid-template-columns: minmax(0, auto) minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}
.tempo-col {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.tempo-head {
  display: flex;
  align-items: center;
  gap: 10px;
}
.pitch {
  font-variant-numeric: tabular-nums;
  font-size: 12px;
  color: var(--fg-dim);
}
input.tempo {
  width: 100%;
  accent-color: var(--accent);
}
.keys-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.ks {
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  color: var(--accent2);
}
button.sync.on {
  background: var(--accent);
  border-color: var(--accent);
  color: #0b0e14;
}
.transport-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.transport-row .bpm,
.transport-row .eff {
  margin-left: auto;
  font-variant-numeric: tabular-nums;
  color: var(--fg-dim);
}
.transport-row .eff {
  margin-left: 0;
  color: var(--accent);
}
button.play.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #0b0e14;
}
.progress-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-variant-numeric: tabular-nums;
  font-size: 12px;
  color: var(--fg-dim);
}
input[type='range'].seek {
  flex: 1;
  accent-color: var(--accent);
}
.loop-row,
.perf-row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.vu-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--fg-dim);
}
.vu-track {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: var(--line);
  overflow: hidden;
}
.vu-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  transition: width 60ms linear;
}
.err {
  margin: 0;
  font-size: 12px;
  color: #ff6b6b;
}
</style>
