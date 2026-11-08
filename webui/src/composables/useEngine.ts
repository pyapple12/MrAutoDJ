// 引擎连接组合式函数（PL003.6）：WS 连接管理 + RPC Promise 化 + tick 状态订阅
// 协议：docs/ipc_protocol.md v1；端口解析：URL ?gw= → Tauri 事件 gateway-port → 默认 8765

import { listen } from '@tauri-apps/api/event'
import { reactive, readonly } from 'vue'

// 单盘状态快照（tick 帧内 a/b 字段，协议 §4.1 v1.1）
export interface DeckState {
  state: string
  paused: boolean
  position: number
  duration: number
  bpm: number
  cue: number
  vu: number
  tempo_rate: number
  key_shift: number
  keylock: boolean
  loop: boolean
  slip: boolean
  hot_cues: readonly boolean[]
  sampler_loaded: readonly boolean[]
}

// Beat FX 组状态（网关持有，协议 F1-F2）
export interface FxState {
  effect: string
  depth: number
  on: boolean
  channel: '1' | '2' | 'both' | string
  beats: number
}

// 曲库条目（library_scan files 视图，协议 L1）
export interface LibEntry {
  path: string
  name: string
  bpm: number
  key: string
  energy: number
  analyzed: boolean
}

// 波形数据包（wave 元数据帧 + 二进制 peaks 帧合成，协议 §4.2）
export interface WaveData {
  path: string
  width: number
  duration: number
  bpm: number
  downbeats: number[]
  peaks: Float32Array // (width, 2) 交错 min/max，f32
}

// hello 握手帧字段经 Record 解析（协议 §2）；tick 顶层字段见 handleMessage
// tick 状态帧（协议 §4.1，盘级结构以 DeckState 为准）
interface TickFrame {
  type: 'tick'
  t: number
  a: DeckState
  b: DeckState
}

// RPC 响应二态（协议 §3）
interface RpcOk {
  id: number
  ok: true
  result: unknown
}
interface RpcErr {
  id: number
  ok: false
  error: { code: string; message: string }
}
type RpcResp = RpcOk | RpcErr

const DEFAULT_PORT = 8765

const emptyDeck = (): DeckState => ({
  state: 'idle',
  paused: true,
  position: 0,
  duration: 0,
  bpm: 0,
  cue: 0,
  vu: 0,
  tempo_rate: 1,
  key_shift: 0,
  keylock: false,
  loop: false,
  slip: false,
  hot_cues: Array.from({ length: 8 }, () => false),
  sampler_loaded: Array.from({ length: 8 }, () => false),
})

// Tauri 环境判定（@tauri-apps/api 注入 __TAURI_INTERNALS__）
const isTauri = '__TAURI_INTERNALS__' in window

// 初始端口：URL ?gw= 优先（浏览器联调），否则默认 8765（Tauri 事件会覆盖）
function initialPort(): number {
  const q = new URLSearchParams(window.location.search).get('gw')
  return q ? Number(q) || DEFAULT_PORT : DEFAULT_PORT
}

export function useEngine() {
  // 连接与两盘状态（tick 帧整帧覆盖，服务端是唯一数据源）
  const state = reactive({
    connected: false,
    reconnecting: false,
    version: '',
    protocolVersion: 0,
    tickHz: 0,
    a: emptyDeck(),
    b: emptyDeck(),
    target: 'a',
    tempo_range: { a: 6, b: 6 } as Record<string, number>,
    sync: { a: false, b: false } as Record<string, boolean>,
    fx: { effect: '', depth: 0, on: false, channel: '1', beats: 4 } as FxState,
    cue_active: null as string | null,
    // PL005 数据层状态（事件帧驱动）
    entries: [] as LibEntry[],
    analyzing: false,
    analysisDone: null as { succeeded: number; total: number } | null,
    prepared: null as { deck: string; ok: boolean; name: string; error: string } | null,
    playQueue: [] as { deck: string; name: string }[], // mix_started 已播顺序
    deckPath: { a: '', b: '' } as Record<string, string>, // 各盘当前曲目路径（波形关联）
  })

  // 波形数据仓库（path → 峰值包；wave 帧到达时填充，容量上限防内存膨胀）
  const waves = reactive(new Map<string, WaveData>())
  const WAVE_KEEP = 8
  let pendingWaveMeta: { path: string; width: number; duration: number; bpm: number; downbeats: number[] } | null = null

  let ws: WebSocket | null = null
  let port = initialPort()
  let nextId = 1
  let retryMs = 500
  let retryTimer: number | null = null
  let manualClose = false
  const pending = new Map<
    number,
    {
      resolve: (v: unknown) => void
      reject: (e: Error) => void
      cmd?: string
      args?: Record<string, unknown>
    }
  >()

  function scheduleReconnect() {
    // 指数退避重连（0.5s 起 ×2 上限 5s，协议 §6）
    if (manualClose || retryTimer !== null) return
    state.reconnecting = true
    retryTimer = window.setTimeout(() => {
      retryTimer = null
      connect()
    }, retryMs)
    retryMs = Math.min(retryMs * 2, 5000)
  }

  function handleMessage(ev: MessageEvent) {
    // 入站分帧：文本 JSON（hello/tick/RPC 响应/事件帧）；二进制 = wave peaks
    if (ev.data instanceof ArrayBuffer) {
      handleWaveBinary(ev.data)
      return
    }
    if (typeof ev.data !== 'string') return
    let msg: Record<string, unknown>
    try {
      msg = JSON.parse(ev.data)
    } catch {
      return
    }
    if (msg.type === 'hello') {
      state.version = String(msg.version)
      state.protocolVersion = Number(msg.protocol_version)
      state.tickHz = Number(msg.tick_hz)
      state.connected = true
      state.reconnecting = false
      retryMs = 500
      return
    }
    if (msg.type === 'tick') {
      const t = msg as unknown as TickFrame
      Object.assign(state.a, t.a)
      Object.assign(state.b, t.b)
      state.target = String(msg.target ?? state.target)
      Object.assign(state.tempo_range, (msg.tempo_range as object) ?? {})
      Object.assign(state.sync, (msg.sync as object) ?? {})
      Object.assign(state.fx, (msg.fx as object) ?? {})
      state.cue_active = (msg.cue_active as string | null) ?? null
      return
    }
    // PL005 事件帧
    if (msg.type === 'wave') {
      // wave 元数据帧：暂存，等成对的二进制 peaks 帧到达后合成入库
      pendingWaveMeta = msg as unknown as typeof pendingWaveMeta
      return
    }
    if (msg.type === 'analysis') {
      const p = String(msg.path)
      const e = state.entries.find((x) => x.path === p)
      if (e) {
        e.bpm = Number(msg.bpm) || 0
        e.key = String(msg.key ?? '?')
        e.energy = Number(msg.energy) || 0
        e.analyzed = Boolean(msg.ok)
      }
      return
    }
    if (msg.type === 'analysis_done') {
      state.analyzing = false
      state.analysisDone = { succeeded: Number(msg.succeeded), total: Number(msg.total) }
      return
    }
    if (msg.type === 'prepared') {
      state.prepared = {
        deck: String(msg.deck),
        ok: Boolean(msg.ok),
        name: String(msg.name ?? ''),
        error: String(msg.error ?? ''),
      }
      return
    }
    if (msg.type === 'mix_started') {
      state.playQueue.unshift({ deck: String(msg.deck), name: String(msg.now_name ?? '') })
      if (state.playQueue.length > 16) state.playQueue.pop()
      return
    }
    if ('id' in msg && 'ok' in msg) {
      const resp = msg as unknown as RpcResp
      const entry = pending.get(resp.id)
      if (!entry) return
      pending.delete(resp.id)
      if (resp.ok) {
        entry.resolve(resp.result)
        // load 成功钩子：记录盘路径 + 自动请求波形（PL005.3 一次传输）
        if (entry.cmd === 'load') {
          const deckLetter = String((entry.args as Record<string, unknown>)?.deck ?? '')
          const path = String((entry.args as Record<string, unknown>)?.path ?? '')
          if (deckLetter === 'a' || deckLetter === 'b') state.deckPath[deckLetter] = path
          if (path) void rpc('waveform', { path })
        }
      } else {
        entry.reject(new Error(`[${resp.error.code}] ${resp.error.message}`))
      }
    }
  }

  function handleWaveBinary(buf: ArrayBuffer) {
    // wave 二进制 peaks 帧：与 pendingWaveMeta 合成入库（LRU 上限 8 条）
    if (!pendingWaveMeta) return
    const m = pendingWaveMeta
    pendingWaveMeta = null
    const peaks = new Float32Array(buf)
    waves.set(m.path, { ...m, peaks })
    if (waves.size > WAVE_KEEP) {
      const first = waves.keys().next().value
      if (first !== undefined) waves.delete(first)
    }
  }

  function connect() {
    // 建连：端口由 URL/事件决定；连接即收 hello（协议 §2）
    manualClose = false
    try {
      ws = new WebSocket(`ws://127.0.0.1:${port}`)
      ws.binaryType = 'arraybuffer' // wave 二进制 peaks 帧
    } catch {
      scheduleReconnect()
      return
    }
    ws.onmessage = handleMessage
    ws.onopen = () => {
      // hello 到达前不置 connected（握手帧为准）
    }
    ws.onclose = () => {
      ws = null
      state.connected = false
      scheduleReconnect()
    }
    ws.onerror = () => {
      ws?.close()
    }
  }

  function setEntries(files: LibEntry[]) {
    // 曲库条目填充（library_scan 响应；条目后续由 analysis 事件帧逐曲回填）
    state.entries.splice(0, state.entries.length, ...files)
    state.analysisDone = null
  }

  function rpc(cmd: string, args: Record<string, unknown> = {}): Promise<unknown> {    // RPC 调用：Promise 化（id 匹配响应；未连接直接拒绝）
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return Promise.reject(new Error('[offline] 未连接到引擎网关'))
    }
    const id = nextId++
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject, cmd, args })
      ws!.send(JSON.stringify({ id, cmd, args }))
    })
  }

  function reconnect(portOverride?: number) {
    // 手动重连（Tauri 端口事件到达时调用；清理旧连接与退避计时）
    if (retryTimer !== null) {
      window.clearTimeout(retryTimer)
      retryTimer = null
    }
    manualClose = true
    ws?.close()
    ws = null
    if (portOverride !== undefined) port = portOverride
    retryMs = 500
    state.reconnecting = false
    connect()
  }

  // Tauri 环境：监听壳注入的实际端口（sidecar 就绪握手后 emit）
  if (isTauri) {
    listen<number>('gateway-port', (ev) => reconnect(Number(ev.payload) || DEFAULT_PORT))
  }

  connect()

  return {
    state: readonly(state),
    rpc,
    reconnect,
    gatewayPort: () => port,
    waves: readonly(waves),
    waveFor: (p: string) => waves.get(p) ?? null,
    setEntries,
  }
}

export type EngineApi = ReturnType<typeof useEngine>
