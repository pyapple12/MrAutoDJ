<!-- 曲库面板（PL005.1）：目录扫描（Tauri dialog/手输）+ 搜索过滤 +
     虚拟滚动表 + 兼容标记 + 双击装载（500ms Instant Doubles）+ 拖拽到盘
     分析进度（PL005.2 事件帧：逐曲回填 + analysis_done） -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { EngineApi, LibEntry } from '../composables/useEngine'
import MetalPanel from './skeuo/MetalPanel.vue'
import BacklitButton from './skeuo/BacklitButton.vue'
import MiniDisplay from './skeuo/MiniDisplay.vue'

const props = defineProps<{ engine: EngineApi }>()

// 曲库目录持久化（PL008.7）：localStorage 记忆上次目录，刷新自动重扫
// （分析缓存命中即时回填）；Tauri/浏览器均适用
const folder = ref(localStorage.getItem('mrautodj.lib.folder') ?? '')
const filter = ref('')
const err = ref('')
const scanning = ref(false)

// 连接后自动重扫（有记忆目录时）——等 snapshot/首轮 tick 稳定后触发一次
if (folder.value) {
  const stop = window.setInterval(() => {
    if (props.engine.state.connected) {
      window.clearInterval(stop)
      void scan()
    }
  }, 400)
  window.setTimeout(() => window.clearInterval(stop), 15000) // 兜底清定时器
}
const ROW_H = 30
const VIEW_H = 264
let lastDbl: { path: string; t: number } | null = { path: '', t: 0 }

const isTauri = '__TAURI_INTERNALS__' in window

const entries = computed<readonly LibEntry[]>(() => {
  // 搜索过滤（名称/路径/调性大小写不敏感）
  const q = filter.value.trim().toLowerCase()
  if (!q) return props.engine.state.entries
  return props.engine.state.entries.filter(
    (e) =>
      e.name.toLowerCase().includes(q) ||
      e.path.toLowerCase().includes(q) ||
      e.key.toLowerCase().includes(q),
  )
})

// 虚拟滚动窗口（可视范围 ±5 行 buffer）
const scrollTop = ref(0)
const totalH = computed(() => entries.value.length * ROW_H)
const startIdx = computed(() => Math.max(0, Math.floor(scrollTop.value / ROW_H) - 5))
const endIdx = computed(() => Math.min(entries.value.length, startIdx.value + Math.ceil(VIEW_H / ROW_H) + 10))
const visible = computed(() => entries.value.slice(startIdx.value, endIdx.value))
const otherDeckBpm = computed(() => {
  // 兼容标记参照：对侧目标盘有效 BPM（与当前目标盘对评）
  const d = props.engine.state.target === 'a' ? 'b' : 'a'
  const st = props.engine.state[d]
  return st.bpm > 0 ? st.bpm * st.tempo_rate : 0
})
const otherDeckKey = computed(() => {
  // 兼容标记参照：对侧盘调性（网关未回显 key——经 state.deckPath→entries 反查，
  // 装载自曲库的曲目可得；手输路径装载无 key → 解析失败中性）
  const d = props.engine.state.target === 'a' ? 'b' : 'a'
  const path = props.engine.state.deckPath[d]
  const hit = props.engine.state.entries.find((x) => x.path === path)
  return hit?.key ?? ''
})

// Camelot 兼容分（PL008.4：对齐 automix.key_score 打分表——同调 1.0 / 相邻能量阶
// 0.9 / 相对调 0.85 / 对角 0.6 / 其他 0.2；解析失败中性 0.5）
const KEY_SAME = 1.0
const KEY_ENERGY = 0.9
const KEY_RELATIVE = 0.85
const KEY_DIAGONAL = 0.6
const KEY_OTHER = 0.2
const KEY_NEUTRAL = 0.5

function parseCamelot(key: string): [number, string] | null {
  // "8A" / "12B" → (号, 字母)；非法 null（曲库 key 字段为 Camelot 记谱）
  const m = /^(\d{1,2})([AB])$/.exec((key ?? '').trim().toUpperCase())
  if (!m) return null
  const n = Number(m[1])
  return n >= 1 && n <= 12 ? [n, m[2]] : null
}

function camelotScore(keyA: string, keyB: string): number {
  const ka = parseCamelot(keyA)
  const kb = parseCamelot(keyB)
  if (!ka || !kb) return KEY_NEUTRAL
  if (ka[0] === kb[0]) return ka[1] === kb[1] ? KEY_SAME : KEY_RELATIVE
  const diff = Math.abs(ka[0] - kb[0])
  const adjacent = diff === 1 || diff === 11
  if (ka[1] === kb[1]) return adjacent ? KEY_ENERGY : KEY_OTHER
  return adjacent ? KEY_DIAGONAL : KEY_OTHER
}

function compatClass(e: LibEntry): string {
  // 双维交集定色（PL008.4）：调性 ≥0.85 且 BPM ±6% → 绿；单维达标 → 黄；否则灰
  if ((e.bpm <= 0 || otherDeckBpm.value <= 0) && !parseCamelot(e.key)) return 'gray'
  const bpmOk = (() => {
    if (e.bpm <= 0 || otherDeckBpm.value <= 0) return null
    const r = e.bpm / otherDeckBpm.value
    if (r > 0.94 && r < 1.06) return true
    if (r > 0.88 && r < 1.12) return false // ±12% 黄区
    return null
  })()
  const keyOk = camelotScore(e.key, otherDeckKey.value) >= 0.85
  if (bpmOk === null) return keyOk ? 'yellow' : 'gray' // 无 BPM：仅调性达标给黄
  if (bpmOk && keyOk) return 'green'
  if (bpmOk || (bpmOk === false && keyOk && !e.bpm)) return 'yellow'
  if (bpmOk === false && keyOk) return 'yellow'
  return 'gray'
}

async function pickFolder() {
  // Tauri 环境走 dialog 插件；浏览器 dev 手输路径
  err.value = ''
  if (isTauri) {
    try {
      const mod = await import('@tauri-apps/plugin-dialog')
      const picked = await mod.open({ directory: true, multiple: false })
      if (typeof picked === 'string' && picked) folder.value = picked
    } catch (e) {
      err.value = e instanceof Error ? e.message : String(e)
      return
    }
  }
  await scan()
}

async function scan() {
  const f = folder.value.trim()
  if (!f) {
    err.value = '请先输入曲库目录'
    return
  }
  scanning.value = true
  err.value = ''
  try {
    const r = (await props.engine.rpc('library_scan', { folder: f })) as {
      files: LibEntry[]
      analyzing: boolean
    }
    props.engine.setEntries(r.files) // 条目填充（后续 analysis 事件帧逐曲回填）
    localStorage.setItem('mrautodj.lib.folder', f) // PL008.7：目录持久化
  } catch (e) {
    err.value = e instanceof Error ? e.message : String(e)
  } finally {
    scanning.value = false
  }
}

async function dblClick(e: LibEntry) {
  // 双击装载：500ms 内同路径再次双击 = Instant Doubles（复制到另一盘同位置）
  // 波形请求由 useEngine load 成功钩子自动发出
  const now = performance.now()
  err.value = ''
  try {
    if (lastDbl && lastDbl.path === e.path && now - lastDbl.t < 500) {
      await props.engine.rpc('instant_doubles', { deck: props.engine.state.target, path: e.path })
      lastDbl = null
      return
    }
    lastDbl = { path: e.path, t: now }
    const target = props.engine.state.target as 'a' | 'b'
    await props.engine.rpc('load', { deck: target, path: e.path, bpm: e.bpm || undefined })
  } catch (ex) {
    err.value = ex instanceof Error ? ex.message : String(ex)
  }
}

function dragStart(ev: DragEvent, e: LibEntry) {
  // 拖拽到盘：dataTransfer 携带路径（DeckPanel drop 接收装载）
  ev.dataTransfer?.setData('text/mrautodj-path', e.path)
  ev.dataTransfer!.effectAllowed = 'copy'
}

const fmtProgress = computed(() => {
  const d = props.engine.state.analysisDone
  if (props.engine.state.analyzing) return '分析中…'
  if (!d || d.total === 0) return ''
  return `分析完成 ${d.succeeded}/${d.total}${d.succeeded < d.total ? `（${d.total - d.succeeded} 失败）` : ''}`
})
</script>

<template>
  <MetalPanel title="曲库">
    <div class="library">
    <header class="head">
      <input v-model="folder" class="folder" type="text" placeholder="曲库目录（如 E:\\music）" @keyup.enter="scan" />
      <BacklitButton size="sm" led="accent" :disabled="scanning" @click="pickFolder">
        {{ isTauri ? '选择目录' : '扫描' }}
      </BacklitButton>
      <input v-model="filter" class="search" type="text" placeholder="搜索（名称/调性）" />
      <MiniDisplay :text="fmtProgress || 'READY'" :warn="engine.state.analyzing" />
    </header>
    <div
      class="table"
      @scroll="scrollTop = ($event.target as HTMLElement).scrollTop"
    >
      <div class="thead">
        <span class="c-name">名称</span>
        <span class="c-bpm">BPM</span>
        <span class="c-key">调性</span>
        <span class="c-en">能量</span>
        <span class="c-cp">兼容</span>
      </div>
      <div class="tbody" :style="{ height: totalH + 'px' }">
        <div
          v-for="e in visible"
          :key="e.path"
          class="row"
          :style="{ transform: `translateY(${(entries.indexOf(e)) * ROW_H}px)`, height: ROW_H + 'px' }"
          :draggable="true"
          @dragstart="dragStart($event, e)"
          @dblclick="dblClick(e)"
          :title="`${e.name}（双击装载到目标盘 · 500ms 内再双击 Instant Doubles · 可拖拽到指定盘）`"
        >
          <span class="c-name" :class="{ dim: !e.analyzed }">{{ e.name }}</span>
          <span class="c-bpm">{{ e.bpm > 0 ? e.bpm.toFixed(1) : '---' }}</span>
          <span class="c-key">{{ e.key }}</span>
          <span class="c-en">{{ e.energy || '·' }}</span>
          <span class="c-cp"><i class="dot" :class="compatClass(e)"></i></span>
        </div>
      </div>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
    </div>
  </MetalPanel>
</template>

<style scoped>
.library {
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
}
.folder {
  flex: 2;
}
.search {
  flex: 1;
}
.prog {
  font-size: 12px;
  color: var(--accent2);
  white-space: nowrap;
}
.table {
  overflow-y: auto;
  height: 264px;
  border: 1px solid var(--line);
  border-radius: 6px;
}
.thead {
  display: flex;
  gap: 8px;
  padding: 4px 10px;
  font-size: 12px;
  color: var(--fg-dim);
  border-bottom: 1px solid var(--line);
  position: sticky;
  top: 0;
  background: var(--panel);
  z-index: 1;
}
.tbody {
  position: relative;
}
.row {
  position: absolute;
  left: 0;
  right: 0;
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 0 10px;
  font-size: 12px;
  cursor: grab;
  border-bottom: 1px solid rgba(35, 42, 56, 0.5);
}
.row:hover {
  background: rgba(47, 139, 255, 0.08);
}
.c-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.c-name.dim {
  color: var(--fg-dim);
}
.c-bpm {
  width: 56px;
  font-variant-numeric: tabular-nums;
}
.c-key {
  width: 40px;
}
.c-en {
  width: 36px;
}
.c-cp {
  width: 24px;
  text-align: center;
}
.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #2a3242;
}
.dot.green {
  background: #2fe37a;
}
.dot.yellow {
  background: #ffd23f;
}
.err {
  margin: 0;
  font-size: 12px;
  color: #ff6b6b;
}
</style>
