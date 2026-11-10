import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Compilación web (Vercel / Capacitor). La app de escritorio sigue usando electron.vite.config.ts.
export default defineConfig({
  root: resolve(__dirname),
  base: './',
  build: { outDir: 'dist-web', emptyOutDir: true },
  resolve: { alias: { '@': resolve(__dirname, 'src') } },
  plugins: [react(), tailwindcss()],
})
