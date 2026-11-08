import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

// vitest 基线（PL007.4）：jsdom 环境 + 组件冒烟；只建基线不追覆盖
export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    include: ['src/**/__tests__/**/*.spec.ts'],
  },
})
