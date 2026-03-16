import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

import path from "path"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // IMPORTANTE PARA DOCKER/PODMAN
  server: {
    host: true, // Escuchar en todas las direcciones (0.0.0.0)
    strictPort: true,
    port: 3000, // Puerto fijo alineado con compose.yaml
    watch: {
      usePolling: true, // Necesario en Windows/WSL2 para que el hot-reload funcione bien
    },
  },
})

