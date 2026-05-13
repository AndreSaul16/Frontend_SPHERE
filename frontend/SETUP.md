# Setup & Runbook (Frontend)

Este repositorio utiliza **Vite** para garantizar tiempos de compilación instantáneos y un desarrollo ágil.

## 📋 Requisitos

- Node.js 18+
- npm o pnpm

## 🛠 Desarrollo Local

Sigue estos pasos para arrancar el frontend y conectarlo al backend local.

1. **Instalar dependencias:**
   ```bash
   npm install
   ```

2. **Variables de Entorno:**
   Asegúrate de que la variable `VITE_API_URL` apunte al backend local. (Vite utiliza variables que empiezan por `VITE_` para exponerlas al cliente).
   Crea un archivo `.env.local` si necesitas sobreescribir la configuración por defecto:
   ```env
   VITE_API_URL=http://localhost:8000/api/v1
   ```

3. **Arrancar Servidor Dev:**
   ```bash
   npm run dev
   ```

El proyecto estará disponible en `http://localhost:3000` (o el puerto configurado por Vite).

## 🚀 Producción

Para construir los assets estáticos de producción:
```bash
npm run build
```

Para previsualizar la build de producción de forma local:
```bash
npm run preview
```

El despliegue en producción normalmente se hace mediante un contenedor Docker usando Nginx o directamente sirviendo la carpeta `dist/` a través de un CDN (ej. Vercel, Railway).
