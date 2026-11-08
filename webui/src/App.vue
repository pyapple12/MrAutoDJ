<!-- 主屏（PL003.6 hello-DJ 一屏）：连接状态横幅 + A/B 双盘面板 -->
<script setup lang="ts">
import { useEngine } from './composables/useEngine'
import DeckPanel from './components/DeckPanel.vue'

const engine = useEngine()
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
    </header>

    <div class="decks">
      <DeckPanel letter="a" :engine="engine" />
      <DeckPanel letter="b" :engine="engine" />
    </div>

    <footer class="foot">
      <span>网关 ws://127.0.0.1:{{ engine.gatewayPort() }}（PL003 sidecar 骨架）</span>
    </footer>
  </main>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 22px;
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
.decks {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.foot {
  font-size: 11px;
  color: var(--fg-dim);
}
</style>
