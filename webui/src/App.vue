<!-- 主屏（PL004 控制面全量对齐）：状态横幅 + SHIFT 体系 + 空格快捷键 +
     双 Deck（Jog/TEMPO/循环/表演/Pad）+ Mixer + Beat FX + 推荐 -->
<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { useEngine } from './composables/useEngine'
import { useShift } from './composables/useShift'
import DeckPanel from './components/DeckPanel.vue'
import MixerPanel from './components/MixerPanel.vue'
import BeatFxPanel from './components/BeatFxPanel.vue'
import AutomixPanel from './components/AutomixPanel.vue'
import LibraryPanel from './components/LibraryPanel.vue'

const engine = useEngine()
const { state: shiftState } = useShift()

function onKeydown(e: KeyboardEvent) {
  // 空格：目标盘播放/暂停（输入框聚焦时不拦截）
  if (e.code !== 'Space') return
  const el = e.target as HTMLElement
  if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT') return
  e.preventDefault()
  const d = engine.state.target as 'a' | 'b'
  engine.rpc(engine.state[d].paused ? 'play' : 'pause', { deck: d })
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <main class="shell">
    <header class="topbar">
      <h1>MrAutoDJ</h1>
      <span class="status" :class="{ on: engine.state.connected, retry: engine.state.reconnecting }">
        {{
          engine.state.connected
            ? `已连接 v${engine.state.version} · 协议 v${engine.state.protocolVersion} · ${engine.state.tickHz}Hz`
            : engine.state.reconnecting
              ? '重连中…'
              : '未连接'
        }}
      </span>
      <button class="shift-btn" :class="{ on: shiftState.on }" title="Shift 锁定（Pad 第二功能/高速搜索）" @click="shiftState.on = !shiftState.on">
        SHIFT
      </button>
      <span class="hint">空格=目标盘播放/暂停 · Shift 按住=第二功能</span>
    </header>

    <div class="decks">
      <DeckPanel letter="a" :engine="engine" />
      <DeckPanel letter="b" :engine="engine" />
    </div>

    <MixerPanel :engine="engine" />

    <div class="bottom">
      <BeatFxPanel :engine="engine" />
      <AutomixPanel :engine="engine" />
    </div>

    <LibraryPanel :engine="engine" />

    <footer class="foot">
      <span>网关 ws://127.0.0.1:{{ engine.gatewayPort() }}（PL005 数据层）</span>
    </footer>
  </main>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px 18px;
}
.topbar {
  display: flex;
  align-items: baseline;
  gap: 14px;
}
.topbar h1 {
  margin: 0;
  font-size: 20px;
  letter-spacing: 3px;
}
.status {
  font-size: 12px;
  color: var(--fg-dim);
}
.status.on {
  color: var(--accent);
}
.status.retry {
  color: var(--accent2);
}
.shift-btn.on {
  background: var(--accent);
  border-color: var(--accent);
  color: #0b0e14;
}
.hint {
  font-size: 11px;
  color: var(--fg-dim);
  margin-left: auto;
}
.decks {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.bottom {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 12px;
}
.foot {
  font-size: 11px;
  color: var(--fg-dim);
}
</style>
