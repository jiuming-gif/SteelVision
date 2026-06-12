import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:5000',
      '/predict': 'http://localhost:5000',
      '/register': 'http://localhost:5000',
      '/login': 'http://localhost:5000',
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
