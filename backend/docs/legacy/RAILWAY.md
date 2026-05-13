# SPHERE - Railway Deployment Guide

## Quick Deploy

1. **Push to GitHub** (ya tenés el repo)
2. **Conectar Railway a GitHub**:
   - Ir a [railway.app](https://railway.app)
   - "New Project" → "Deploy from GitHub repo"
   - Seleccionar el repo de SPHERE
3. **Railway detecta automáticamente** el `docker-compose.railway.yaml` y deploya todos los servicios

## Variables de Entorno (Configurar en Railway UI)

Railway te pedirá configurar estas variables. **Solo necesitás las marcadas como ⚡ obligatorias**:

### ⚡ Obligatorias (sin estas no funciona)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | API key de DeepSeek para el LLM | *(vacío)* |
| `FERNET_KEY` | Clave de cifrado para credenciales | *(vacío)* |

### 🔧 Opcionales (tienen defaults)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `MONGO_ROOT_USER` | Usuario MongoDB | `sphere` |
| `MONGO_ROOT_PASSWORD` | Password MongoDB | `sphere_password` |
| `N8N_BASIC_AUTH_USER` | Usuario n8n | `admin` |
| `N8N_BASIC_AUTH_PASSWORD` | Password n8n | `n8n_password` |
| `N8N_WEBHOOK_SECRET` | Secret para webhooks | *(vacío)* |
| `N8N_API_KEY` | API key de n8n (obtener después de levantar) | *(vacío)* |
| `OPENAI_API_KEY` | API key de OpenAI (opcional) | *(vacío)* |
| `ALLOWED_ORIGINS` | URLs permitidas para CORS | `https://*.railway.app,http://localhost:3000` |

## Después del Deploy

1. **Obtener API key de n8n**:
   - Ir a `https://tu-app-n8n.railway.app`
   - Login con las credenciales configuradas
   - Settings → API → Create API Key
   - Copiar la key y agregarla como `N8N_API_KEY` en Railway

2. **Verificar que todo funciona**:
   - Backend: `https://tu-app-backend.railway.app/api/v1/health/live`
   - Frontend: `https://tu-app-frontend.railway.app`
   - n8n: `https://tu-app-n8n.railway.app`

## Arquitectura en Railway

```
┌─────────────────────────────────────────────────────────┐
│                    Railway Project                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Frontend   │  │   Backend   │  │     n8n     │     │
│  │  (React)    │  │  (FastAPI)  │  │ (Workflows) │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │             │
│         └────────────────┼────────────────┘             │
│                          │                              │
│         ┌────────────────┴────────────────┐             │
│         │        Internal Network         │             │
│         └────────────────┬────────────────┘             │
│                          │                              │
│         ┌────────────────┴────────────────┐             │
│         │                                 │             │
│  ┌──────┴──────┐                   ┌──────┴──────┐     │
│  │   MongoDB   │                   │    Redis    │     │
│  │  (Database) │                   │   (Cache)   │     │
│  └─────────────┘                   └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Costos Estimados (Railway)

| Servicio | Plan | Precio |
|----------|------|--------|
| MongoDB | Free tier | $0/mes (512MB) |
| Redis | Free tier | $0/mes (256MB) |
| Backend | Starter | ~$5/mes |
| Frontend | Starter | ~$5/mes |
| n8n | Starter | ~$5/mes |
| **Total** | | **~$15/mes** |

## Troubleshooting

### El deploy falla
- Verificar que `DEEPSEEK_API_KEY` esté configurado
- Revisar logs en Railway UI

### n8n no responde
- Esperar 30-60 segundos después del deploy
- Verificar que `N8N_BASIC_AUTH_USER` y `N8N_BASIC_AUTH_PASSWORD` estén configurados

### Backend no conecta a MongoDB
- Verificar que `MONGO_ROOT_USER` y `MONGO_ROOT_PASSWORD` coincidan en todos los servicios

### Frontend no carga
- Verificar que `VITE_API_URL` apunte al backend correcto
- Revisar CORS en `ALLOWED_ORIGINS`
