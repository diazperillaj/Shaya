import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Chatbot (microservicio en Docker). nginx hace lo mismo en prod:
      // /chat/api/v1/... → chatbot:8005/api/v1/...
      '/chat': {
        target: 'http://localhost:8005',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/chat/, ''),
      },
    },
  },
})
