import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    watch: {
      ignored: [
        /\\bAppData\\b/i,
        /\\bLocalLow\\b/i,
        /\\bNVIDIA\\b/i,
        '**/.git/**',
        '**/node_modules/**',
      ],
    },
  },
})
