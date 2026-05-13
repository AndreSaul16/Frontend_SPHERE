# SPHERE Frontend — Railway Deployment

## Arquitectura en Railway

```
┌─────────────────────────────────────────────────────────┐
│                    RAILWAY PROJECT                       │
│                                                         │
│  ┌──────────────┐                                       │
│  │   Frontend   │                                       │
│  │  React+Vite  │                                       │
│  │  nginx       │                                       │
│  │  Puerto $PORT│                                       │
│  └──────┬───────┘                                       │
│         │                                               │
│         │    ┌─────────────────────────┐                │
│         │    │     BACKEND (Railway)    │                │
│         └───▶│  https://backend.up.railway.app │         │
│              └─────────────────────────┘                │
└─────────────────────────────────────────────────────────┘
```

## Variables de entorno

### Obligatorias (configurar en Railway UI)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `VITE_FIREBASE_API_KEY` | Firebase API key | `AIza...` |
| `VITE_FIREBASE_AUTH_DOMAIN` | Firebase Auth domain | `sphere-2a4cf.firebaseapp.com` |
| `VITE_FIREBASE_PROJECT_ID` | Firebase project ID | `sphere-2a4cf` |
| `VITE_FIREBASE_STORAGE_BUCKET` | Firebase storage bucket | `sphere-2a4cf.appspot.com` |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Firebase sender ID | `123456789` |
| `VITE_FIREBASE_APP_ID` | Firebase app ID | `1:123:web:abc` |
| `VITE_API_URL` | Backend API URL | `https://backend.up.railway.app/api/v1` |

### Build Args (opcionales)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000/api/v1` | URL del backend (se bakea en el build) |

## Deploy

1. Conectar el repo `Frontend_SPHERE` a Railway
2. Railway detecta `railway.toml` automáticamente
3. Configurar variables de entorno obligatorias
4. Deploy automático

## Health Check

```
GET /
```

## Costos estimados

- Frontend: ~$5/mes (Railway Hobby)
- **Total: ~$5/mes**

## Troubleshooting

### Error: "VITE_FIREBASE_API_KEY is required"
- Verificar que todas las variables de Firebase estén configuradas
- Obtener valores de Firebase Console → Project Settings → Your apps

### Error: "API URL not configured"
- Configurar `VITE_API_URL` con la URL del backend en Railway
- Formato: `https://backend.up.railway.app/api/v1`

### Error: nginx no arranca
- Verificar que `nginx.conf.template` existe
- Verificar que el build de Vite fue exitoso

## Notas importantes

- Las variables `VITE_*` se bakean en el build (no son runtime)
- Si cambiás variables de Firebase, necesitás hacer rebuild
- El frontend es estático (nginx) — no consume CPU en runtime
