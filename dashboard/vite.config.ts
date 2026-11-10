import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// GitHub Pages project site: https://tinnery.github.io/noos-enterprise/
export default defineConfig({
  base: '/noos-enterprise/',
  plugins: [vue()],
  server: {
    port: 5173,
    host: true,
  },
})
