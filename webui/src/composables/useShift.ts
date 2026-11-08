// Shift 全局状态（PL004.5，对齐 ui/shift_state：SHIFT 按钮与键盘 Shift 共用）
// pad/jog 等指令的 shift 第二功能读此状态；键盘 Shift 按住即时生效
import { reactive } from 'vue'

const state = reactive({
  on: false, // SHIFT 按钮锁定态
  held: false, // 键盘 Shift 按住态（keydown/keyup 同步）
})

// 当前是否处于 Shift 态（按钮锁定或键盘按住；事件级 shiftKey 可直接覆盖）
function isShift(ev?: { shiftKey?: boolean }): boolean {
  if (ev && ev.shiftKey) return true
  return state.on || state.held
}

// 全局键盘监听（模块级一次挂载；Tab 焦点等不受影响）
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Shift') state.held = true
  })
  window.addEventListener('keyup', (e) => {
    if (e.key === 'Shift') state.held = false
  })
}

export function useShift() {
  return { state, isShift }
}
