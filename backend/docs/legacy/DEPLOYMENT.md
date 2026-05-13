# SPHERE Deployment Guide

## Arquitectura de producción

```
┌─────────────────────────────────────────────────────────┐
│                    Podman Compose                        │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Frontend │  │ Backend  │  │   n8n    │  │ MongoDB  │ │
│  │  :3000   │  │  :8000   │  │  :5678   │  │ :27017   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┘ │
│       │              │              │                     │
│       └──────────────┴──────────────┘                     │
│                      │                                    │
│                   Redis                                   │
│                   :6379                                   │
└─────────────────────────────────────────────────────────┘
```

## Quick Start (Local)

```bash
# 1. Clonar el repo
git clone <repo-url>
cd SPHERE

# 2. Copiar y configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys

# 3. Crear directorio de credenciales
mkdir -p credentials
# Colocar firebase.json en credentials/

# 4. Arrancar con Podman
podman-compose up -d

# 5. Verificar que todo funciona
podman-compose ps
curl http://localhost:8000/api/v1/health

# 6. Abrir frontend
open http://localhost:3000
```

## Variables de entorno obligatorias

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `MONGODB_URL` | URL de MongoDB | `mongodb://user:pass@host:27017/db` |
| `FERNET_KEY` | Clave de cifrado | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `DEEPSEEK_API_KEY` | API key de DeepSeek | `sk-...` |
| `N8N_WEBHOOK_SECRET` | Secret para HMAC | `openssl rand -hex 32` |

## Generar Fernet Key

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Generar HMAC Secret

```bash
openssl rand -hex 32
```

## Opciones de Deployment

### 1. Railway (RECOMENDADO para empezar)

**Pros:**
- Deploy directo desde GitHub
- MongoDB y Redis managed
- Precio razonable (~$5-20/mes)
- SSL automático

**Contras:**
- Vendor lock-in
- Limitaciones en free tier

**Pasos:**
1. Conectar repo de GitHub
2. Agregar servicio de MongoDB
3. Agregar servicio de Redis
4. Configurar variables de entorno
5. Deploy automático

### 2. Google Cloud Run + Cloud SQL

**Pros:**
- Escalado automático
- Pago por uso
- MongoDB Atlas como alternativa

**Contras:**
- Más complejo de configurar
- Costos variables

### 3. AWS (ECS + DocumentDB)

**Pros:**
- Más flexible
- DocumentDB compatible con MongoDB

**Contras:**
- Más caro
- Más complejo

### 4. Vercel + PlanetScale

**Pros:**
- Frontend en Vercel (gratis)
- PlanetScale para MySQL

**Contras:**
- No es MongoDB (necesitaríamos cambiar ORM)
- No soporta n8n directamente

### 5. DigitalOcean App Platform

**Pros:**
- Simple como Railway
- MongoDB managed
- Precio fijo

**Contras:**
- Menos features que AWS/GCP

## Recomendación

**Para empezar:** Railway
- Simple, rápido, barato
- MongoDB y Redis managed
- Deploy desde GitHub

**Para escalar:** Google Cloud Run + MongoDB Atlas
- Escalado automático
- Pago por uso
- MongoDB Atlas es el mejor managed MongoDB

## Estructura de Directorios

```
SPHERE/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints
│   │   ├── core/            # Config, DB, Auth
│   │   ├── models/          # Pydantic models
│   │   └── tools/           # Agent tools
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── store/
│   ├── Dockerfile
│   └── package.json
├── n8n-workflows/           # Auto-deployed
├── credentials/             # Firebase, etc.
├── podman-compose.yaml
├── .env.example
└── README.md
```

## Monitoreo

```bash
# Logs de todos los servicios
podman-compose logs -f

# Logs de un servicio específico
podman-compose logs -f backend

# Estado de los servicios
podman-compose ps

# Uso de recursos
podman stats
```

## Backup

```bash
# Backup de MongoDB
podman exec sphere-mongodb mongodump --out /backup

# Copiar backup del contenedor
podman cp sphere-mongodb:/backup ./backup

# Restore
podman exec sphere-mongodb mongorestore /backup
```

## Troubleshooting

**n8n no arranca:**
```bash
podman-compose logs n8n
# Verificar que N8N_BASIC_AUTH_PASSWORD esté seteado
```

**Backend no conecta a MongoDB:**
```bash
# Verificar que MongoDB esté healthy
podman-compose ps
# Ver logs del backend
podman-compose logs backend
```

**Workflows no se deployan:**
```bash
# Verificar N8N_API_KEY en .env
# Ver logs del backend al arrancar
podman-compose logs backend | grep n8n
```
