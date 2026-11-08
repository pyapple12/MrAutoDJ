<!-- 拟物组件陈列页（PL006.2 storybook）：?view=gallery 访问——六组件逐件
     对照 PySide6 版行为（拖拽方向/双击回中/LED 态/禁用灰显），含交互说明 -->
<script setup lang="ts">
import { ref } from 'vue'
import MetalPanel from './MetalPanel.vue'
import BacklitButton from './BacklitButton.vue'
import Knob from './Knob.vue'
import Fader from './Fader.vue'
import VuMeter from './VuMeter.vue'
import MiniDisplay from './MiniDisplay.vue'
import JogWheel from './JogWheel.vue'

const knobVal = ref(0.3)
const trimVal = ref(1.0)
const faderVal = ref(0)
const vfaderVal = ref(0)
const vuVal = ref(0.62)
const lcdText = ref('128.0 BPM')
const galleryVinyl = ref(true)
// 陈列页假引擎（只读 state 喂 Canvas 转盘渲染；as never 直通组件 props 类型）
const engineStub = {
  state: {
    a: { position: 123456, duration: 8820000, state: 'playing', bpm: 128, tempo_rate: 1, key_shift: 0, keylock: false, loop: false, slip: false, hot_cues: [], sampler_loaded: [], paused: false, cue: 0, vu: 0.62 },
    b: { position: 0, duration: 0, state: 'idle', bpm: 0, tempo_rate: 1, key_shift: 0, keylock: false, loop: false, slip: false, hot_cues: [], sampler_loaded: [], paused: true, cue: 0, vu: 0.3 },
    target: 'a',
  },
  rpc: () => Promise.resolve(),
} as never
</script>

<template>
  <main class="gallery">
    <header class="head">
      <h1>拟物组件库 · Skeuo Gallery</h1>
      <span class="hint">交互说明内嵌于每个组件 tooltip；主题切换 Ctrl+T</span>
    </header>

    <MetalPanel title="MetalPanel 金属面板">
      <p class="note">拉丝金属各向异性纹理 + 内嵌铭牌 + 边缘高光（CSS repeating-gradient）。</p>
    </MetalPanel>

    <MetalPanel title="BacklitButton 背光按钮">
      <div class="row">
        <BacklitButton>熄灭</BacklitButton>
        <BacklitButton led="accent" size="sm">LED accent</BacklitButton>
        <BacklitButton led="accent2">LED orange</BacklitButton>
        <BacklitButton led="glow-green" size="sm">LED green</BacklitButton>
        <BacklitButton disabled>禁用灰显</BacklitButton>
      </div>
      <p class="note">点亮态：文字变色 + 底部内辉光 + 外光晕（box-shadow blur）。</p>
    </MetalPanel>

    <MetalPanel title="Knob 旋钮">
      <div class="row">
        <Knob v-model="knobVal" :min="-1" :max="1" label="低" />
        <Knob v-model="trimVal" :min="0" :max="2" :default-value="1" label="TRIM" />
        <Knob v-model="knobVal" :min="-1" :max="1" :size="28" label="FX 小" />
      </div>
      <p class="note">纵向拖拽 · 双击回默认 · 刻度环 + 金属帽径向渐变 + 发光指针。</p>
    </MetalPanel>

    <MetalPanel title="Fader 推子">
      <div class="row">
        <Fader v-model="faderVal" :min="-1" :max="1" />
        <Fader v-model="vfaderVal" :min="-1" :max="1" vertical length="120px" />
      </div>
      <p class="note">轨槽内嵌阴影 + 拟物帽 + 发光标线；点击/拖拽直接跟手。</p>
    </MetalPanel>

    <MetalPanel title="VuMeter 灯柱 + MiniDisplay 小屏">
      <div class="row">
        <VuMeter :vu="vuVal" />
        <MiniDisplay :text="lcdText" />
        <MiniDisplay text="FX OFF" warn />
        <label class="vu-slider">vu
          <input v-model.number="vuVal" type="range" min="0" max="1" step="0.01" />
        </label>
      </div>
      <p class="note">灯柱阈值色带（ui.json led_*_threshold）+ 辉光 + 峰值保持衰减；小屏液晶扫描线。</p>
    </MetalPanel>

    <MetalPanel title="JogWheel 转盘（Canvas 拟物）">
      <div class="row">
        <JogWheel v-model:vinyl="galleryVinyl" letter="a" :engine="engineStub" />
      </div>
      <p class="note">金属外环 + 乙烯基纹路随播放旋转 + 镜面中心柱 + 播放指示辉光点。</p>
    </MetalPanel>
  </main>
</template>

<style scoped>
.gallery {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px 22px;
  max-width: 900px;
}
.head {
  display: flex;
  align-items: baseline;
  gap: 14px;
}
.head h1 {
  margin: 0;
  font-size: 18px;
  letter-spacing: 2px;
}
.hint {
  font-size: 12px;
  color: var(--fg-dim);
}
.row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}
.note {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--fg-dim);
}
.vu-slider {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--fg-dim);
}
</style>
