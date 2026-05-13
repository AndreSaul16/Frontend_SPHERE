# Setup & Runbook (Backend)

Este documento contiene los pasos estandarizados para levantar, configurar y mantener el entorno de desarrollo y producción del Backend de SPHERE.

## 📋 Requisitos Previos

- Docker y Docker Compose instalados.
- Python 3.11+
- Acceso a credenciales de Firebase (`firebase.json`).

## 🛠 Entorno de Desarrollo (Local)

La forma más sencilla de levantar la infraestructura de soporte (MongoDB, Redis, n8n) y la API es a través de Docker.

### 1. Configuración de Entorno

Duplica el archivo de ejemplo y configura tus claves (API Keys de OpenAI/DeepSeek, contraseñas de DB):

```bash
cp .env.example .env
```

### 2. Levantar Infraestructura

Para levantar todo el ecosistema (incluyendo contenedores de ETL y n8n):

```bash
docker-compose up -d
```

### 3. Desarrollo Nativo (Hot-Reloading)

Si prefieres desarrollar la API fuera de Docker para aprovechar el hot-reloading de FastAPI de forma más rápida:

```bash
# Crea un entorno virtual
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)

# Instala dependencias
pip install -r requirements.txt

# Ejecuta el servidor en modo dev
uvicorn app.presentation.api.main:app --reload --host 0.0.0.0 --port 8000
```

## 🚀 Despliegue en Producción (Railway / Podman)

El proyecto incluye configuraciones para despliegues modernos:
- `Dockerfile` optimizado (Multi-stage) para imágenes ligeras.
- `railway.toml` para CI/CD automático.
- `compose.yaml` ajustado para entornos de producción.
