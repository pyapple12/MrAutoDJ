<!-- Pad×8 五模式面板（PL004.2，对齐 _on_pad 五模式语义与灯态）
     Hot Cue：无 shift 有灯则播放否则设置，shift 清除
     Beat Loop：拍梯 1-2-4-8-16-32，shift 关循环
     Beat Jump：前 4 后 4（1/2/4/8 拍）
     Sampler：shift 卸载 / 有装载则播放（未装载仅提示）
     Key Shift：半音表 0,+1,+2,+3,-3,-2,-1,0；shift 累加（0 复位） -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { EngineApi } from '../composables/useEngine'
import { useShift } from '../composables/useShift'

const props = defineProps<{
  letter: 'a' | 'b'
  engine: EngineApi
}>()

const { isShift } = useShift()
const MODES = ['Hot Cue', 'Beat Loop', 'Beat Jump', 'Sampler', 'Key Shift'] as const
const mode = ref<(typeof MODES)[number]>('Hot Cue')
const err = ref('')
const BEAT_LADDER = [1, 2, 4, 8, 16, 32]
const SEMITONES = [0, 1, 2, 3, -3, -2, -1, 0]

const deck = computed(() => props.engine.state[props.letter])

const padLabels = computed<string[]>(() => {
  // Pad 标签随模式（对齐 PySide6 pad_widget 文案语义）
  if (mode.value === 'Hot Cue') return Array.from({ length: 8 }, (_, i) => String(i + 1))
  if (mode.value === 'Beat Loop') return Array.from({ length: 8 }, (_, i) => `${BEAT_LADDER[i % BEAT_LADDER.length]}拍`)
  if (mode.value === 'Beat Jump')
    return Array.from({ length: 8 }, (_, i) => {
      const step = [1, 2, 4, 8][i % 4]
      return `${i < 4 ? '◀' : '▶'}${step}`
    })
  if (mode.value === 'Sampler') return Array.from({ length: 8 }, (_, i) => `S${i + 1}`)
  return SEMITONES.map((s) => (s > 0 ? `+${s}` : String(s)))
})

async function hit(idx: number, ev: PointerEvent | MouseEvent) {
  // Pad 触发：shift 经全局状态（按钮锁定或事件 ShiftKey）显式传协议
  err.value = ''
  try {
    await props.engine.rpc('pad', {
      deck: props.letter,
      idx,
      mode: mode.value,
      shift: isShift(ev as { shiftKey?: boolean }),
    })
  } catch (e) {
    err.value = e instanceof Error ? e.message : String(e)
  }
}
</script>

<template>
  <section class="padbank">
    <header class="mode-row">
      <button
        v-for="m in MODES"
        :key="m"
        class="mode-btn"
        :class="{ on: mode === m }"
        @click="mode = m"
      >
        {{ m }}
      </button>
    </header>
    <div class="pads">
      <button
        v-for="(label, i) in padLabels"
        :key="i"
        class="pad"
        :class="{
          lit:
            (mode === 'Hot Cue' && deck.hot_cues[i]) ||
            (mode === 'Sampler' && deck.sampler_loaded[i]) ||
            (mode === 'Key Shift' && deck.key_shift === SEMITONES[i]),
        }"
        @pointerdown="hit(i, $event)"
      >
        {{ label }}
      </button>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
  </section>
</template>

<style scoped>
.padbank {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.mode-row {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
.mode-btn {
  padding: 4px 10px;
  font-size: 11px;
  border-radius: 4px;
}
.mode-btn.on {
  border-color: var(--accent);
  color: var(--accent);
}
.pads {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 6px;
}
.pad {
  aspect-ratio: 1;
  min-height: 40px;
  padding: 0;
  font-size: 12px;
  border-radius: 6px;
}
.pad.lit {
  background: var(--accent);
  border-color: var(--accent);
  color: #0b0e14;
  font-weight: 600;
}
.err {
  margin: 0;
  font-size: 11px;
  color: #ff6b6b;
}
</style>
