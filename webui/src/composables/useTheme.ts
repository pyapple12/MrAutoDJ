// 主题切换（PL006.1，对齐 palette/J2 Ctrl+T 语义）：dark/light 运行时双主题
// 切换 = document.documentElement.dataset.theme 翻转（tokens.css [data-theme=light]
// 覆盖表生效）——CSS 过渡承担全控件刷新，无需重启
import { ref } from 'vue'

const theme = ref<'dark' | 'light'>('dark')

function applyTheme(t: 'dark' | 'light') {
  theme.value = t
  if (t === 'light') document.documentElement.dataset.theme = 'light'
  else delete document.documentElement.dataset.theme // dark = 默认 :root
}

function cycleTheme() {
  // Ctrl+T 循环（dark → light → dark）
  applyTheme(theme.value === 'dark' ? 'light' : 'dark')
}

// 初始应用（模块级一次）
applyTheme('dark')

export function useTheme() {
  return { theme, cycleTheme }
}
