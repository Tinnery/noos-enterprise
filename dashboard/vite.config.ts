import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Vite 配置：纯前端单页应用，无后端。
// 数据通过本地 JSON 文件（src/data/taxonomy.json）加载。
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: true,
  },
})
