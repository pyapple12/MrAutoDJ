// PL008.9 深度测试补强：WaveformView 渲染分支 / JogWheel 搓碟指令序列交互冒烟
// jsdom 无 Canvas 后端——stub getContext 记录绘制调用（断言"画了什么"而非像素）
import { describe, it, expect, vi, beforeAll } from 'vitest'
import { mount } from '@vue/test-utils'
import WaveformView from '../components/WaveformView.vue'
import JogWheel from '../components/skeuo/JogWheel.vue'
import type { EngineApi, WaveData } from '../composables/useEngine'

const ctxCalls: Record<string, number> = {}
const ctxStub = new Proxy(
  {
    // 固定字段（draw 用到的属性）+ 身份标记（诊断用）
    canvas: null,
    fillStyle: '',
    strokeStyle: '',
    lineWidth: 1,
    font: '',
    textAlign: '',
    shadowColor: '',
    shadowBlur: 0,
    __stub: true,
  },
  {
    get(t, prop) {
      if (typeof prop !== 'string') return undefined
      if (prop in t) return (t as Record<string, unknown>)[prop]
      // 渐变工厂：返回带 addColorStop 的 stub 对象（JogWheel 金属环渐变）
      if (prop === 'createRadialGradient' || prop === 'createLinearGradient') {
        return () => ({ addColorStop: vi.fn() })
      }
      // 方法调用：计数并返回 undefined（fillText 等无返回值方法）
      ctxCalls[prop] = (ctxCalls[prop] ?? 0) + 1
      return vi.fn()
    },
    set(t, prop, v) {
      if (typeof prop === 'string') (t as Record<string, unknown>)[prop] = v
      return true
    },
  },
)

beforeAll(() => {
  // jsdom getContext 原生返回 null——直接替换原型方法（spyOn 对部分 jsdom
  // 内建方法不可配置）
  (HTMLCanvasElement.prototype as unknown as { getContext: unknown }).getContext =
    (() => ctxStub) as unknown as never
})

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
      connected: true, reconnecting: false, version: '0.2.9',
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

describe('WaveformView 渲染分支（PL008.9）', () => {
  it('无 wave 数据：空态分支（fillText 提示）', () => {
    ctxCalls.clearRect = 0
    ctxCalls.fillText = 0
    const eng = makeEngineStub()
    const w = mount(WaveformView, {
      props: { letter: 'a', engine: eng, wave: null },
      attachTo: document.body,
    })
    expect(ctxCalls.clearRect).toBeGreaterThan(0) // draw 走过
    expect(ctxCalls.fillText).toBeGreaterThan(0) // 空态提示"载入曲目后显示波形"
    w.unmount()
  })

  it('有 wave 数据：峰值/网格/播放头绘制调用（tick watch 驱动）', async () => {
    const eng = makeEngineStub()
    const wave: WaveData = {
      path: 'E:/m/a.mp3', width: 8, duration: 60, bpm: 128, downbeats: [30],
      peaks: new Float32Array([0, 0.8, 0, 0.6, 0, 0.4, 0, 0.2, 0, -0.2, 0, -0.4, 0, -0.6, 0, -0.8]),
    }
    ctxCalls.clearRect = 0
    ctxCalls.moveTo = 0
    const w = mount(WaveformView, {
      props: { letter: 'b', engine: eng, wave },
      attachTo: document.body,
    })
    await w.vm.$nextTick()
    expect(ctxCalls.clearRect).toBeGreaterThan(0)
    expect(ctxCalls.moveTo).toBeGreaterThan(8) // 8 列峰值 + 网格 + 播放头（moveTo 起笔）
    expect(w.find('canvas.wave').attributes('data-deck')).toBe('b')
    w.unmount()
  })
})

describe('JogWheel 搓碟指令序列（PL008.9）', () => {
  it('pointerdown→pointermove（vinyl）→jog_touch/jog_scratch 序列→pointerup', async () => {
    const eng = makeEngineStub()
    const w = mount(JogWheel, {
      props: { letter: 'a', engine: eng, vinyl: true, touching: false },
      attachTo: document.body,
    })
    const cv = w.find('canvas.jog').element as HTMLCanvasElement
    // jsdom rect 全 0 / 无 setPointerCapture——双补（盘内判定与 onDown 依赖）
    cv.getBoundingClientRect = () =>
      ({ left: 0, top: 0, width: 220, height: 220, right: 220, bottom: 220, x: 0, y: 0, toJSON: () => ({}) }) as DOMRect
    cv.setPointerCapture = () => {}
    // 盘心坐标（220×220，中心 110,110——盘内）
    await cv.dispatchEvent(new PointerEvent('pointerdown', {
      bubbles: true, pointerId: 1, clientX: 110, clientY: 110,
    }))
    expect(eng.rpc).toHaveBeenCalledWith('jog_touch', { deck: 'a', on: true })
    // 拖动 20px（vinyl 模式 → jog_scratch，gain≥256×0.5）
    await cv.dispatchEvent(new PointerEvent('pointermove', {
      bubbles: true, pointerId: 1, clientX: 130, clientY: 110,
    }))
    const scratchCall = (eng.rpc as ReturnType<typeof vi.fn>).mock.calls.find(
      (c) => c[0] === 'jog_scratch',
    )
    expect(scratchCall).toBeTruthy()
    expect((scratchCall![1] as { delta: number }).delta).not.toBe(0)
    await cv.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 1 }))
    expect(eng.rpc).toHaveBeenCalledWith('jog_touch', { deck: 'a', on: false })
    w.unmount()
  })

  it('滚轮弯音（jog_bend 脉冲）', async () => {
    const eng = makeEngineStub()
    const w = mount(JogWheel, {
      props: { letter: 'b', engine: eng, vinyl: true, touching: false },
      attachTo: document.body,
    })
    const cv = w.find('canvas.jog').element as HTMLCanvasElement
    await cv.dispatchEvent(new WheelEvent('wheel', { bubbles: true, cancelable: true, deltaY: -100 }))
    const bendCall = (eng.rpc as ReturnType<typeof vi.fn>).mock.calls.find((c) => c[0] === 'jog_bend')
    expect(bendCall).toBeTruthy()
    // 向上滚 = 正弯音（BEND_STEP 0.05）
    expect((bendCall![1] as { rate: number }).rate).toBeCloseTo(0.05, 5)
    w.unmount()
  })
})
