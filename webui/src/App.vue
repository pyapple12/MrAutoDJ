<!-- 主屏（PL006 拟物视觉）：MetalPanel 面板族 + SHIFT 背光钮 + Ctrl+T 双主题 +
     ?view=gallery 拟物组件陈列页；数据层（PL005 事件帧/波形/曲库）不变 -->
<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useEngine } from './composables/useEngine'
import { useShift } from './composables/useShift'
import { useTheme } from './composables/useTheme'
import DeckPanel from './components/DeckPanel.vue'
import MixerPanel from './components/MixerPanel.vue'
import BeatFxPanel from './components/BeatFxPanel.vue'
import AutomixPanel from './components/AutomixPanel.vue'
import LibraryPanel from './components/LibraryPanel.vue'
import BacklitButton from './components/skeuo/BacklitButton.vue'
import SkeuoGallery from './components/skeuo/SkeuoGallery.vue'

const engine = useEngine()
const { state: shiftState } = useShift()
const { cycleTheme, theme } = useTheme()

const isGallery = computed(() => new URLSearchParams(window.location.search).get('view') === 'gallery')

function onKeydown(e: KeyboardEvent) {
  // Ctrl+T 主题循环（J2 语义）；空格=目标盘播放/暂停（输入框聚焦时不拦截）
  if (e.ctrlKey && e.code === 'KeyT') {
    e.preventDefault()
    cycleTheme()
    return
  }
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
  <SkeuoGallery v-if="isGallery" />
  <main v-else class="shell">
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
      <BacklitButton led="glow-blue" size="sm" :class="{ 'shift-on': shiftState.on }" title="Shift 锁定（Pad 第二功能/高速搜索）" @click="shiftState.on = !shiftState.on">
        SHIFT
      </BacklitButton>
      <BacklitButton size="sm" :title="`主题切换（当前 ${theme}，Ctrl+T 循环）`" @click="cycleTheme">
        {{ theme === 'dark' ? '亮色' : '暗色' }}
      </BacklitButton>
      <span class="hint">空格=目标盘播放/暂停 · Shift 按住=第二功能 · Ctrl+T 换肤</span>
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
      <span>网关 ws://127.0.0.1:{{ engine.gatewayPort() }}（PL006 拟物视觉 · ?view=gallery 组件陈列）</span>
    </footer>
  </main>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: 14px 18px;
}
.topbar {
  display: flex;
  align-items: baseline;
  gap: var(--sp-3);
}
.topbar h1 {
  margin: 0;
  font-size: 20px;
  letter-spacing: 3px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}
.status {
  font-size: 12px;
  color: var(--fg-dim);
}
.status.on {
  color: var(--glow-green);
}
.status.retry {
  color: var(--accent2);
}
.shift-on {
  --led: var(--glow-blue);
}
.hint {
  font-size: 12px;
  color: var(--fg-dim);
  margin-left: auto;
}
.decks {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--sp-3);
}
/* 768 tablet：双盘单列（防按钮行溢出） */
@media (max-width: 980px) {
  .decks,
  .bottom {
    grid-template-columns: minmax(0, 1fr);
  }
}
.bottom {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
  gap: var(--sp-3);
}
.foot {
  font-size: 12px;
  color: var(--fg-dim);
}
</style>
