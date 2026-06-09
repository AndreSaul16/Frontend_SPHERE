import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

import path from "path"

// Build-time metadata for deploy status page.
// Injected as global constants available at runtime.
const GIT_COMMIT_SHA = process.env.GIT_COMMIT_SHA
    || process.env.RAILWAY_GIT_COMMIT_SHA
    || 'unknown';
const BUILD_TIMESTAMP = new Date().toISOString();
const VERSION = '1.0.0';
const RAILWAY_SERVICE_NAME = process.env.RAILWAY_SERVICE_NAME || 'Frontend_SPHERE';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    '__GIT_COMMIT_SHA__': JSON.stringify(GIT_COMMIT_SHA),
    '__BUILD_TIMESTAMP__': JSON.stringify(BUILD_TIMESTAMP),
    '__VERSION__': JSON.stringify(VERSION),
    '__RAILWAY_SERVICE_NAME__': JSON.stringify(RAILWAY_SERVICE_NAME),
  },
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
  preview: {
    host: true,
    port: 3000,
    strictPort: true,
    allowedHosts: ['.railway.app'],
  },
})

