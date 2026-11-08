// 组件冒烟基线（PL007.4）：MixerPanel/PadBank 挂载与交互指令触发；只建基线不追覆盖
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MixerPanel from '../components/MixerPanel.vue'
import PadBank from '../components/PadBank.vue'
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
      a: { ...deck }, b: { ...deck, state: 'idle', paused: true, position: 0, duration: 0, bpm: 0, vu: 0 },
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
