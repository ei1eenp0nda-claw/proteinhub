import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ['haughtily-ornithologic-coy.ngrok-free.dev', '.ngrok-free.dev', 'localhost'],
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  },
  build: {
    // 代码分割配置
    rollupOptions: {
      output: {
        manualChunks: {
          // 第三方库单独打包
          'element-plus': ['element-plus'],
          'vendor': ['vue', 'vue-router', 'axios']
        }
      }
    }
    // 使用默认的 esbuild 压缩（无需额外依赖）
  }
})