import { defineConfig } from 'vite'

export default defineConfig({
  preview: {
    host: '0.0.0.0',
    allowedHosts: ['llf-dashboard.onrender.com'],
  },
})
