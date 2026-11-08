// 组件冒烟基线（PL007.4）：MixerPanel/PadBank/LibraryPanel 挂载与交互指令触发；只建基线不追覆盖
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MixerPanel from '../components/MixerPanel.vue'
import PadBank from '../components/PadBank.vue'
import LibraryPanel from '../components/LibraryPanel.vue'
import type { EngineApi } from '../composables/useEngine'

// 引擎 stub：state 喂渲染、rpc 用 vi.fn 捕获指令
function makeEngineStub(): EngineApi {
  const deck = {
    state: 'playing', paused: false, position: 10, duration: 60,
    bpm: 128, cue: 0, vu: 0.4, tempo_rate: 1, key_shift: 0,
    keylock: false, loop: false, slip: false,
    hot_cues: Array.from({ length: 8 }, () => false),
    sampler_loaded: Array.from({ length: 8 }, () => false),
  }
  return {
    state: {
      connected: true, reconnecting: false, version: '0.2.8',
      protocolVersion: 1, tickHz: 30,
      a: { ...deck }, b: { ...deck, state: 'idle', paused: true, position: 0, duration: 0, vu: 0 },
      target: 'a', tempo_range: { a: 6, b: 6 }, sync: { a: false, b: false },
      fx: { effect: '', depth: 0, on: false, channel: '1', beats: 4 },
      cue_active: null, entries: [], analyzing: false, analysisDone: null,
      prepared: null, playQueue: [], deckPath: { a: '', b: '' },
    },
    rpc: vi.fn().mockResolvedValue({}),
    reconnect: vi.fn(),
    gatewayPort: () => 8765,
    waves: new Map(),
    waveFor: () => null,
    setEntries: vi.fn(),
  } as unknown as EngineApi
}

describe('MixerPanel 冒烟', () => {
  it('挂载渲染双通道旋钮与监听钮', () => {
    const eng = makeEngineStub()
    const w = mount(MixerPanel, { props: { engine: eng } })
    expect(w.text()).toContain('TRIM A')
    expect(w.text()).toContain('TRIM B')
    expect(w.text()).toContain('CUE A')
    expect(w.text()).toContain('CUE B')
  })

  it('TAP 按钮触发 tap 指令', async () => {
    const eng = makeEngineStub()
    const w = mount(MixerPanel, { props: { engine: eng } })
    const tap = w.findAll('button').find((b) => b.text() === 'TAP A')
    expect(tap).toBeTruthy()
    await tap!.trigger('click')
    expect(eng.rpc).toHaveBeenCalledWith('tap', { deck: 'a' })
  })

  it('CUE 监听按钮触发 phones_preview 指令', async () => {
    const eng = makeEngineStub()
    const w = mount(MixerPanel, { props: { engine: eng } })
    const cue = w.findAll('button').find((b) => b.text() === 'CUE A')
    await cue!.trigger('click')
    expect(eng.rpc).toHaveBeenCalledWith('phones_preview', { deck: 'a' })
  })
})

describe('LibraryPanel 兼容标记 Camelot 维度（PL008.4）', () => {
  it('camelotScore 打分表对齐 automix.key_score', async () => {
    // 经组件导出不可行——挂载后经 compatClass 类名间接断言：
    // 对侧盘 key=8A（entries 反查），BPM 相同（±6% 内）
    const eng = makeEngineStub()
    // 对侧盘 B 装载 1.mp3（8A）、曲库五条不同调性——stub state 直改（非 readonly）
    const st = eng.state as unknown as {
      entries: unknown[]
      deckPath: Record<string, string>
    }
    st.entries = [
      { path: 'E:/m/1.mp3', name: '1.mp3', bpm: 128, key: '8A', energy: 4, analyzed: true },
      { path: 'E:/m/2.mp3', name: '2.mp3', bpm: 128, key: '9A', energy: 4, analyzed: true },
      { path: 'E:/m/3.mp3', name: '3.mp3', bpm: 128, key: '8B', energy: 4, analyzed: true },
      { path: 'E:/m/4.mp3', name: '4.mp3', bpm: 128, key: '5B', energy: 4, analyzed: true },
      { path: 'E:/m/5.mp3', name: '5.mp3', bpm: 128, key: '??', energy: 4, analyzed: true },
    ]
    st.deckPath = { a: 'E:/m/0.mp3', b: 'E:/m/1.mp3' }
    const w = mount(LibraryPanel, { props: { engine: eng } })
    const dots = w.findAll('.dot')
    expect(dots.length).toBe(5)
    const cls = (i: number) => dots[i].classes().find((c) => ['green', 'yellow', 'gray'].includes(c))
    expect(cls(0)).toBe('green') // 8A 同调 1.0 + BPM 达标 → 双维绿
    expect(cls(1)).toBe('green') // 9A 相邻能量阶 0.9 + BPM → 绿
    expect(cls(2)).toBe('green') // 8B 相对调 0.85 + BPM → 绿
    expect(cls(3)).toBe('yellow') // 5B 其他 0.2 → 仅 BPM 单维黄
    expect(cls(4)).toBe('yellow') // ?? 解析失败中性 0.5 → 仅 BPM 单维黄
  })
})

describe('PadBank 冒烟', () => {
  it('渲染五模式与 8 槽 Pad', () => {
    const eng = makeEngineStub()
    const w = mount(PadBank, { props: { letter: 'a', engine: eng } })
    for (const m of ['Hot Cue', 'Beat Loop', 'Beat Jump', 'Sampler', 'Key Shift']) {
      expect(w.text()).toContain(m)
    }
    expect(w.findAll('.pads button').length).toBe(8)
  })

  it('Pad pointerdown 触发 pad 指令（模式与 shift 显式传递）', async () => {
    const eng = makeEngineStub()
    const w = mount(PadBank, { props: { letter: 'b', engine: eng } })
    const pad = w.findAll('.pads button')[0]
    // shiftKey 为 getter-only——trigger 无参默认 shift=false（与显式传参等价路径）
    await pad.trigger('pointerdown')
    expect(eng.rpc).toHaveBeenCalledWith('pad', {
      deck: 'b', idx: 0, mode: 'Hot Cue', shift: false,
    })
  })
})
