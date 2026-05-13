# SPHERE Backend — Railway Deployment

## Arquitectura en Railway

```
┌─────────────────────────────────────────────────────────┐
│                    RAILWAY PROJECT                       │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Backend    │  │   MongoDB    │  │    Redis     │  │
│  │  FastAPI     │  │   Atlas      │  │   (Railway)  │  │
│  │  Puerto $PORT│  │  (externo)   │  │  Puerto 6379 │  │
│  └──────┬───────┘  └──────────────┘  └──────────────┘  │
│         │                                               │
│         │    ┌─────────────────────────┐                │
│         │    │     SERVICIOS EXTERNOS   │                │
│         │    │                          │                │
│         └───▶│  DeepSeek API (LLM)      │                │
│              │  OpenAI API (Embeddings) │                │
│              │  Firebase Auth           │                │
│              │  n8n (Webhooks)          │                │
│              └─────────────────────────┘                │
└─────────────────────────────────────────────────────────┘
```

## Variables de entorno

### Obligatorias (configurar en Railway UI)

| Variable | Descripción | Dónde obtenerla |
|----------|-------------|-----------------|
| `MONGODB_URL` | Connection string de MongoDB Atlas | MongoDB Atlas → Connect → Driver |
| `DEEPSEEK_API_KEY` | API key de DeepSeek | platform.deepseek.com |
| `OPENAI_API_KEY` | API key de OpenAI | platform.openai.com/api-keys |
| `FERNET_KEY` | Clave de cifrado | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `FIREBASE_CREDENTIALS_PATH` | Ruta al JSON de Firebase | Firebase Console → Service accounts |

### Opcionales (con defaults)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `ENVIRONMENT` | `production` | Entorno de ejecución |
| `DB_NAME` | `sphere_db` | Nombre de la base de datos |
| `ALLOWED_ORIGINS` | `*` | CORS origins permitidos |
| `N8N_BASE_URL` | `http://n8n:5678` | URL de n8n |
| `N8N_WEBHOOK_SECRET` | `""` | Secret para webhooks |
| `N8N_API_KEY` | `""` | API key de n8n |
| `REDIS_URL` | `redis://localhost:6379` | URL de Redis |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `30` | Rate limit global |
| `RATE_LIMIT_CHAT_PER_MINUTE` | `10` | Rate limit chat |

## Deploy

1. Conectar el repo `Backend_SHPERE` a Railway
2. Railway detecta `railway.toml` automáticamente
3. Configurar variables de entorno obligatorias
4. Deploy automático

## Health Check

```
GET /api/v1/health/live
```

## Costos estimados

- Backend: ~$5/mes (Railway Hobby)
- MongoDB Atlas: Free tier (512MB)
- Redis: ~$3/mes (Railway)
- **Total: ~$8/mes**

## Troubleshooting

### Error: "MONGODB_URL is required"
- Verificar que la variable esté configurada en Railway UI
- Verificar que el string de conexión sea correcto

### Error: "FIREBASE_CREDENTIALS_PATH not found"
- Subir el JSON de Firebase como variable de entorno (no como archivo)
- Usar `FIREBASE_CREDENTIALS_JSON` con el contenido del JSON

### Error: CORS
- Configurar `ALLOWED_ORIGINS` con la URL del frontend en Railway
