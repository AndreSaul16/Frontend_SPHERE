<p align="center">
  <img src="https://img.shields.io/badge/SPHERE-Backend-purple?style=for-the-badge&labelColor=0D0D1A&color=7C3AED" />
  <img src="https://img.shields.io/badge/Status-Production--Ready-green?style=for-the-badge&labelColor=0D0D1A&color=10B981" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge&labelColor=0D0D1A&color=3B82F6" />
</p>

<h1 align="center">SPHERE Backend</h1>
<p align="center"><b>API + Orquestador Multi-Agente + RAG</b></p>
<p align="center">
  FastAPI backend con LangGraph para orquestación multi-agente,<br/>
  RAG con MongoDB Atlas Vector Search, y tool-calling vía n8n.
</p>

---

## Stack

| Capa | Tecnología | Por qué |
|------|-----------|---------|
| **Framework** | FastAPI + Python 3.11 | Async nativo, OpenAPI automático |
| **Orquestador** | LangGraph (StateGraph) | ReAct loop, multi-agente nativo |
| **LLM** | DeepSeek Chat | Excelente relación calidad/precio |
| **Embeddings** | OpenAI `text-embedding-3-small` | 1536 dimensiones, bueno y barato |
| **Base de Datos** | MongoDB Atlas | Documental + Vector Search |
| **Cache/Locks** | Redis | Rate limiting, distributed locks |
| **Auth** | Firebase Auth | Google/GitHub social login |
| **Automatización** | n8n | Webhooks para Calendar, WhatsApp, LinkedIn |

## Quick Start

### Prerrequisitos

- Python 3.11+
- MongoDB Atlas (o local)
- Redis
- Firebase project
- DeepSeek API key
- OpenAI API key

### Paso 1: Configurar

```bash
# Clonar
git clone https://github.com/AndreSaul16/Backend_SHPERE.git
cd Backend_SHPERE

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Copiar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### Paso 2: Ejecutar

```bash
# Desarrollo local
python run_local.py --port 8000 --reload

# O con uvicorn directamente
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Paso 3: Verificar

```bash
# Health check
curl http://localhost:8000/api/v1/health/live

# API docs
open http://localhost:8000/docs
```

## Docker

```bash
# Build
docker build -t sphere-backend .

# Run
docker run -p 8000:8000 --env-file .env sphere-backend
```

## Estructura

```
backend/
├── app/
│   ├── api/v1/            # Endpoints REST
│   ├── core/              # Lógica central (orchestrator, auth, RAG)
│   ├── models/            # Modelos Pydantic
│   ├── tools/             # Tools por rol (21 herramientas)
│   └── integrations/      # OAuth providers
├── tests/                 # ~80 tests
├── scripts/               # Migraciones y vector index
├── main.py                # Entry point FastAPI
├── Dockerfile
└── requirements.txt
```

## Endpoints principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/v1/stream/` | Chat con streaming SSE |
| `POST` | `/api/v1/chat/` | Chat sin streaming |
| `GET/POST` | `/api/v1/sessions/` | CRUD de sesiones |
| `GET/POST` | `/api/v1/agents/` | CRUD de agentes custom |
| `POST` | `/api/v1/agents/{id}/documents` | Upload de documentos RAG |
| `GET/PATCH` | `/api/v1/auth/me` | Perfil de usuario |
| `GET` | `/api/v1/health/ready` | Health check |

## Tests

```bash
# Ejecutar todos los tests
python -m pytest tests/ -v

# Con cobertura
python -m pytest tests/ -v --cov=app --cov-report=html
```

## Deploy

Ver [RAILWAY.md](RAILWAY.md) para deployment en Railway.

## Licencia

MIT License
