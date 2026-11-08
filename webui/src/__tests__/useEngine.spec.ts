// useEngine 协议逻辑单测（PL007.4 基线）：RPC 帧封装/id 匹配/事件帧处理/波形入库
// 不真连 WS——mock window.WebSocket 捕获出站帧、注入入站帧
import { describe, it, expect, afterEach } from 'vitest'
import { useEngine } from '../composables/useEngine'

// 伪造 MessageEvent（jsdom 无真 WebSocket 服务端）
function makeEvent(data: string | ArrayBuffer): MessageEvent {
  return { data } as MessageEvent
}

// WebSocket mock：onmessage 用 setter 捕获（useEngine 在构造后赋值 onmessage）；
// send 捕获出站 RPC 帧（lastRpc 供断言与 id 匹配注入）
let lastRpc: { id: number; cmd: string; args: Record<string, unknown> } | null = null
let wsHandler: ((ev: MessageEvent) => void) | null = null

class FakeWS {
  binaryType = ''
  sent: string[] = []
  constructor(public url: string) {
    expect(url).toContain('ws://127.0.0.1:')
  }
  set onmessage(fn: ((ev: MessageEvent) => void) | null) {
    wsHandler = fn
  }
  get onmessage() {
    return wsHandler
  }
  send(d: string) {
    lastRpc = JSON.parse(d)
    this.sent.push(d)
  }
  close() {}
}

const realWS = window.WebSocket

function installFakeWS() {
  lastRpc = null
  wsHandler = null
  ;(window as unknown as { WebSocket: unknown }).WebSocket = FakeWS
}

afterEach(() => {
  ;(window as unknown as { WebSocket: unknown }).WebSocket = realWS
})

describe('useEngine 协议逻辑', () => {
  it('tick 帧覆盖两盘状态与顶级字段；RPC 出站帧结构与响应匹配', async () => {
    installFakeWS()
    const eng = useEngine()
    const tick = {
      type: 'tick',
      t: 1,
      a: {
        state: 'playing', paused: false, position: 12, duration: 60,
        bpm: 128, cue: 3, vu: 0.5, tempo_rate: 1.06, key_shift: 2,
        keylock: true, loop: false, slip: false,
        hot_cues: [true, false], sampler_loaded: [false],
      },
      b: {
        state: 'idle', paused: true, position: 0, duration: 0, bpm: 0, cue: 0,
        vu: 0, tempo_rate: 1, key_shift: 0, keylock: false, loop: false,
        slip: false, hot_cues: [], sampler_loaded: [],
      },
      target: 'b',
      tempo_range: { a: 6, b: 10 },
      sync: { a: true, b: false },
      fx: { effect: 'echo', depth: 0.3, on: true, channel: '1', beats: 4 },
      cue_active: 'b',
    }
    wsHandler!(makeEvent(JSON.stringify(tick)))
    expect(eng.state.a.bpm).toBe(128)
    expect(eng.state.a.tempo_rate).toBe(1.06)
    expect(eng.state.target).toBe('b')
    expect(eng.state.tempo_range.b).toBe(10)
    expect(eng.state.sync.a).toBe(true)
    expect(eng.state.fx.effect).toBe('echo')
    expect(eng.state.cue_active).toBe('b')

    // RPC：出站帧结构
    const p = eng.rpc('set_volume', { volume: 1.5 })
    expect(lastRpc!.cmd).toBe('set_volume')
    expect(lastRpc!.args).toEqual({ volume: 1.5 })
    expect(lastRpc!.id).toBeGreaterThan(0)
    // 注入 ok 响应（id 匹配 resolve）
    wsHandler!(makeEvent(JSON.stringify({ id: lastRpc!.id, ok: true, result: { volume: 1.5 } })))
    await expect(p).resolves.toEqual({ volume: 1.5 })
  })

  it('错误响应 reject 并携带中文消息', async () => {
    installFakeWS()
    const eng = useEngine()
    const p = eng.rpc('nope')
    wsHandler!(makeEvent(JSON.stringify({
      id: lastRpc!.id,
      ok: false,
      error: { code: 'unknown_cmd', message: '未知指令: nope' },
    })))
    await expect(p).rejects.toThrow('[unknown_cmd] 未知指令: nope')
  })

  it('analysis 事件帧回填条目 + analysis_done 收尾', () => {
    installFakeWS()
    const eng = useEngine()
    eng.setEntries([
      { path: 'E:/m/a.mp3', name: 'a.mp3', bpm: 0, key: '?', energy: 0, analyzed: false },
    ])
    wsHandler!(makeEvent(JSON.stringify({
      type: 'analysis', path: 'E:/m/a.mp3', name: 'a.mp3', ok: true,
      bpm: 126.5, key: '8A', energy: 4, error: '',
    })))
    expect(eng.state.entries[0].bpm).toBe(126.5)
    expect(eng.state.entries[0].analyzed).toBe(true)
    wsHandler!(makeEvent(JSON.stringify({ type: 'analysis_done', succeeded: 1, total: 1 })))
    expect(eng.state.analyzing).toBe(false)
    expect(eng.state.analysisDone).toEqual({ succeeded: 1, total: 1 })
  })

  it('prepared 与 mix_started 事件帧入状态', () => {
    installFakeWS()
    const eng = useEngine()
    wsHandler!(makeEvent(JSON.stringify({
      type: 'prepared', deck: 'a', ok: true, path: 'E:/m/b.mp3', name: 'b.mp3', error: '',
    })))
    expect(eng.state.prepared).toEqual({ deck: 'a', ok: true, name: 'b.mp3', error: '' })
    wsHandler!(makeEvent(JSON.stringify({
      type: 'mix_started', deck: 'a', now: 'E:/m/b.mp3', now_name: 'b.mp3',
      finished: 'E:/m/a.mp3', chained: true,
    })))
    expect(eng.state.playQueue[0]).toEqual({ deck: 'a', name: 'b.mp3' })
  })

  it('wave 元数据 + 二进制帧合成入库（LRU）', () => {
    installFakeWS()
    const eng = useEngine()
    wsHandler!(makeEvent(JSON.stringify({
      type: 'wave', path: 'E:/m/a.mp3', width: 4, duration: 30,
      bpm: 120, downbeats: [0, 22050],
    })))
    // f32 LE 4 列 ×2 通道 = 8 float（ArrayBuffer 帧形态）
    const peaks = new Float32Array([0, 0.5, 0, 0.4, 0, -0.5, 0, -0.4])
    wsHandler!(makeEvent(peaks.buffer))
    const w = eng.waveFor('E:/m/a.mp3')
    expect(w).not.toBeNull()
    expect(w!.width).toBe(4)
    // f32 精度：0.4 → 0.4000000059604645，逐元素近似比较
    const arr = Array.from(w!.peaks)
    expect(arr.length).toBe(8)
    const expectVals = [0, 0.5, 0, 0.4, 0, -0.5, 0, -0.4]
    arr.forEach((v, i) => expect(v).toBeCloseTo(expectVals[i], 5))
  })
})
