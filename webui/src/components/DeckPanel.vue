<!-- 打碟机面板（PL003.6 hello-DJ 一屏）：加载曲/播放/CUE/seek 进度条/BPM/VU —— DOM 实现 -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { DeckState, EngineApi } from '../composables/useEngine'

const props = defineProps<{
  letter: 'a' | 'b'
  engine: EngineApi
}>()

const deck = computed<DeckState>(() => props.engine.state[props.letter])
const pathInput = ref('')
const busy = ref(false)
const errMsg = ref('')

function fmtTime(seconds: number): string {
  // 秒 → m:ss（负值/NaN 钳 0）
  const s = Math.max(0, Math.floor(seconds || 0))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

async function run(fn: () => Promise<unknown>) {
  // 指令执行包装：忙标记 + 中文错误直显（协议错误 message 已中文）
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

const loadTrack = () =>
  run(async () => {
    const p = pathInput.value.trim()
    if (!p) {
      errMsg.value = '请先输入音频文件路径'
      return
    }
    await props.engine.rpc('load', { deck: props.letter, path: p })
  })
const togglePlay = () =>
  run(() => props.engine.rpc(deck.value.paused ? 'play' : 'pause', { deck: props.letter }))
const doCue = () => run(() => props.engine.rpc('cue', { deck: props.letter }))
const doSeek = (ev: Event) =>
  run(() => props.engine.rpc('seek', { deck: props.letter, seconds: Number((ev.target as HTMLInputElement).value) }))

const stateText = computed(() => (deck.value.state === 'playing' ? '播放中' : deck.value.state === 'mixing' ? '混音中' : '空闲'))
</script>

<template>
  <section class="deck-panel">
    <header class="deck-head">
      <h2>DECK {{ letter.toUpperCase() }}</h2>
      <span class="badge" :class="deck.state">{{ stateText }}</span>
    </header>

    <div class="load-row">
      <input v-model="pathInput" type="text" placeholder="音频文件路径（如 E:\\music\\song.mp3）" :disabled="busy" />
      <button class="primary" :disabled="busy" @click="loadTrack">载入</button>
    </div>

    <div class="transport-row">
      <button class="primary play" :class="{ active: deck.state === 'playing' }" :disabled="busy" @click="togglePlay">
        {{ deck.paused ? '播放' : '暂停' }}
      </button>
      <button :disabled="busy" @click="doCue">CUE</button>
      <span class="bpm">{{ deck.bpm > 0 ? deck.bpm.toFixed(1) + ' BPM' : '--- BPM' }}</span>
    </div>

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

    <div class="vu-row">
      <span>VU</span>
      <div class="vu-track">
        <div class="vu-fill" :style="{ width: Math.round(deck.vu * 100) + '%' }"></div>
      </div>
    </div>

    <p v-if="errMsg" class="err">{{ errMsg }}</p>
  </section>
</template>

<style scoped>
.deck-panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.deck-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.deck-head h2 {
  margin: 0;
  font-size: 15px;
  letter-spacing: 2px;
  color: var(--fg-dim);
}
.badge {
  font-size: 11px;
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
.load-row {
  display: flex;
  gap: 8px;
}
.load-row input {
  flex: 1;
}
.transport-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.transport-row .bpm {
  margin-left: auto;
  font-variant-numeric: tabular-nums;
  color: var(--fg-dim);
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
.vu-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
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
