import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/tasks': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/process_task': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/update_task': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/delete_task': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  }
})
