# Guía de Arquitectura para Agentes de IA

> **Lee esto ANTES de trabajar en el backend de SPHERE.**
> Esto es tu mapa. No te pierdas.

---

## Stack

| Componente | Tecnología | Notas |
|------------|-----------|-------|
| **Framework** | FastAPI | Async, OpenAPI automático |
| **Base de datos** | MongoDB Atlas (Motor + PyMongo) | Dual client: async para FastAPI, sync para LangGraph |
| **Orquestador** | LangGraph | StateGraph, multi-agente, checkpoint persistente |
| **LLM** | DeepSeek Chat + OpenAI embeddings | DeepSeek para chat (barato), OpenAI para vectores |
| **Autenticación** | Firebase Auth | JWT verification, auto-provisioning |
| **Credenciales** | Fernet (cifrado simétrico) | Tokens OAuth en reposo |
| **Cache/Locks** | Redis | Rate limiting, distributed locks, embedding cache |
| **Rate limiting** | fastapi-limiter + token budget | 2 capas: req/min + daily token budget |
| **Webhooks** | n8n | Calendar, WhatsApp, LinkedIn, GitHub, Jules |
| **Testing** | pytest + httpx + fakeredis | Async, fixtures compartidas, MSW para frontend |
| **Frontend** | React + Vite + Zustand | Puerto 3000, Tailwind v4, Firebase SDK |

---

## Arquitectura General

```
Frontend (React)          Backend (FastAPI)           Servicios Externos
┌───────────────┐         ┌──────────────────┐       ┌─────────────────┐
│               │  SSE    │  API (routes)    │       │ MongoDB Atlas   │
│  ChatPanel    │────────▶│       │          │──────▶│ (DB + VectorS.) │
│  useChatStore │         │  Core Layer      │       │                 │
│  AuthContext  │◀────────│  (orchestrator,  │       │ DeepSeek API    │
│               │  JSON   │   auth, RAG,     │       │ OpenAI API      │
└───────────────┘         │   tenant, tools) │       │ Firebase Auth   │
                          │       │          │       │ Redis           │
                          │  Tools Layer     │       │ n8n webhooks    │
                          │  (21 tools)      │       └─────────────────┘
                          └──────────────────┘
```

---

## Principios Fundamentales

### 1. Multi-tenancy por defecto
Cada query se filtra por `user_id` (viene del JWT de Firebase). Sin `user_id`, no hay acceso. El módulo `tenant.py` provee helpers: `scoped_find()`, `scoped_insert()`, `scoped_update()`, `scoped_delete()`, `require_owner()`.

### 2. 404 > 403
Cuando un usuario intenta acceder a un recurso que no es suyo, devolvemos **404** (no 403). Así no revelamos la existencia de recursos ajenos.

### 3. Graceful degradation
Redis es opcional. Si no está disponible, rate limiting, distributed locks, y embedding cache se desactivan silenciosamente. El sistema funciona sin Redis (solo menos protegido).

### 4. Overlay pattern (agentes)
El prompt final de un agente se construye así:
```
BASE_PROMPT (core o custom) + USER_OVERRIDE + USER_CONTEXT = PROMPT FINAL
```
Nunca se reemplaza el base — se agrega encima. Así las mejoras al base se propagan a todos.

### 5. Confirmación de tools
Las herramientas destructivas (enviar WhatsApp, postear en LinkedIn) requieren confirmación del usuario. El flujo: tool devuelve error estructurado → LLM pregunta al usuario → usuario confirma → LLM reintenta con `confirmed=True`.

---

## Estructura del Backend

```
backend/
├── app/
│   ├── core/           # Lógica central (NO depende de FastAPI)
│   │   ├── orchestrator.py    # LangGraph StateGraph (el cerebro)
│   │   ├── rag.py             # MongoDB Atlas Vector Search
│   │   ├── auth.py            # Firebase Auth + auto-provisioning
│   │   ├── tenant.py          # Multi-tenant query helpers
│   │   ├── credentials.py     # OAuth token broker (Fernet)
│   │   ├── agent_resolver.py  # Overlay pattern
│   │   ├── user_context.py    # USER_CONTEXT builder
│   │   ├── contacts_service.py # Contact whitelist
│   │   ├── token_budget.py    # Daily token limits
│   │   ├── redis_client.py    # Redis singleton (graceful degradation)
│   │   ├── distributed_lock.py # Redis SET NX EX
│   │   ├── circuit_breaker.py # State machine (closed/open/half_open)
│   │   ├── error_handling.py  # Sanitización de errores
│   │   ├── embedding_cache.py # Redis cache para embeddings
│   │   ├── tool_context.py    # Contextvars para tools
│   │   ├── document_processor.py # Pipeline RAG (parse→chunk→embed→store)
│   │   ├── templates.py       # 10 templates de agentes
│   │   ├── database.py        # Dual MongoDB client (async + sync)
│   │   ├── config.py          # Pydantic Settings
│   │   └── logger.py          # Structured logging
│   │
│   ├── api/v1/         # Endpoints REST
│   │   ├── stream.py          # POST /stream/ (SSE streaming)
│   │   ├── chat.py            # POST /chat/ (no streaming)
│   │   ├── sessions.py        # CRUD sesiones + pins + ratings
│   │   ├── agents.py          # CRUD agentes custom + templates
│   │   ├── documents.py       # Upload/manage documentos RAG
│   │   ├── auth.py            # /me + agent-overrides + contacts
│   │   ├── integrations.py    # OAuth flows (GitHub, Notion, Slack)
│   │   └── health.py          # Liveness + readiness probes
│   │
│   ├── tools/          # Herramientas por rol
│   │   ├── registry.py        # Registro role→tools
│   │   ├── shared_tools.py    # Calendar + WhatsApp (8 tools)
│   │   ├── ceo_tools.py       # Delegación de tareas
│   │   ├── cfo_tools.py       # Datos financieros
│   │   ├── cmo_tools.py       # Social media
│   │   ├── cto_tools.py       # Jules (Google coding agent)
│   │   ├── n8n_client.py      # HTTP client con HMAC + retry + circuit breaker
│   │   └── clients/           # API clients directos (GitHub, Notion, Slack)
│   │
│   ├── models/         # Modelos Pydantic
│   │   ├── session.py         # SessionType, VisualConfig, etc.
│   │   ├── agent.py           # AgentIdentity, BrainConfig, etc.
│   │   ├── user.py            # UIPreferences, ProfessionalProfile, etc.
│   │   └── oauth_credential.py
│   │
│   └── integrations/   # OAuth providers
│       └── providers/
│           ├── github.py
│           ├── notion.py
│           └── slack.py
│
├── tests/              # ~80 tests, 15 archivos
├── scripts/            # Migraciones
│   ├── backfill_user_id.py          # Añade user_id a docs existentes
│   └── vector_index_definition.json # Definición del índice vectorial
├── main.py             # Entry point (lifespan, routers, indexes)
├── run_local.py        # CLI para desarrollo local
├── phantom_front.py    # CLI de stress testing y auditoría
└── Dockerfile          # Multi-stage, 4 workers
```

---

## Flujos Principales

### Chat con streaming (POST /api/v1/stream/)

```
1. Verificar Firebase JWT
2. Verificar ownership de la sesión
3. Tomar distributed lock (Redis SET NX EX)
4. Determinar target_role (de la sesión o del request)
5. LangGraph astream_events():
   a. router_node: clasifica query (CEO/CTO/CFO/CMO/custom)
   b. agent_node: carga config (overlay), busca RAG, llama LLM
   c. tool_node (opcional): ejecuta tools vía n8n
   d. loop hasta END (max 3 iteraciones de tools)
6. Emitir SSE events: meta, token, tool_start, tool_result, artifact_*
7. Liberar lock
```

### Creación de agente custom

```
1. POST /api/v1/agents/ con identity + brain_config
2. MongoDB insert con owner_user_id
3. Frontend sube documentos via POST /agents/{id}/documents
4. Backend guarda en GridFS, lanza background task:
   a. parse_document() → detecta extensión, extrae texto
   b. chunk_text() → 512 tokens, 64 overlap
   c. embed_chunks_sync() → OpenAI text-embedding-3-small
   d. store en knowledge_base con user_id + agent_target
```

### OAuth flow (GitHub, Notion, Slack)

```
1. GET /api/v1/integrations/{provider}/connect
2. Backend genera state HMAC-signed, guarda en DB (TTL 10min)
3. Redirect a provider OAuth URL
4. Usuario autoriza en provider
5. Provider redirect a callback URL
6. Backend verifica state, intercambia code por token
7. Cifra token con Fernet, guarda en oauth_credentials
8. Redirect a frontend con ?connected=provider
```

---

## MongoDB Collections (14)

| Collection | Propósito | Multi-tenant |
|------------|-----------|:------------:|
| `users` | Perfiles de usuario | firebase_uid |
| `sessions_metadata` | Metadatos de sesiones | user_id |
| `checkpoints` | Estado LangGraph | thread_id (user_id:session_id) |
| `checkpoint_writes` | Writes LangGraph | thread_id |
| `custom_agents` | Agentes personalizados | owner_user_id |
| `knowledge_base` | Vectores RAG | user_id + agent_target |
| `oauth_credentials` | Tokens cifrados | user_id |
| `oauth_states` | CSRF states | TTL 10min |
| `contacts` | Whitelist de contactos | user_id |
| `user_agent_overrides` | Overrides de prompts | user_id |
| `idempotency_keys` | Idempotencia | user_id, TTL 24h |
| `message_ratings` | Ratings de mensajes | user_id |
| `agent_tasks` | Tareas delegadas | assigned_to |
| `tool_audit_log` | Auditoría de tools | user_id |

---

## Variables de Entorno

```bash
# Requeridas (fail-fast en producción)
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true
DB_NAME=sphere
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
FIREBASE_CREDENTIALS_PATH=./firebase-adminsdk.json
FERNET_KEY=your-fernet-key
REDIS_URL=redis://redis:6379/0

# Opcionales (features específicas)
N8N_BASE_URL=http://n8n:5678
N8N_WEBHOOK_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
NOTION_CLIENT_ID=...
NOTION_CLIENT_SECRET=...
SLACK_CLIENT_ID=...
SLACK_CLIENT_SECRET=...
OAUTH_REDIRECT_BASE_URL=http://localhost:8000/api/v1/integrations

# Frontend (VITE_)
VITE_API_URL=http://localhost:8000/api/v1
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
```

---

## Comandos de Desarrollo

```bash
# Backend local
cd backend && python run_local.py --port 8000 --reload

# Tests backend
cd backend && python -m pytest tests/ -v

# Frontend local
cd frontend && npm run dev

# Tests frontend
cd frontend && npm test

# Docker completo
docker compose up -d redis backend frontend

# Phantom Front (stress test)
cd backend && python phantom_front.py

# ETL
cd etl && python run_etl.py --agent all
```

---

## Convenciones

- **Imports absolutos** desde `app.` (no relativos)
- **Type hints** en todas las funciones
- **Docstrings** en endpoints
- **Logging** con `get_logger(__name__)` (no `print()`)
- **Errors**: usar `safe_error_response()` para respuestas al cliente
- **Multi-tenant**: TODAS las queries deben incluir `user_id`
- **Tests**: fixtures en `conftest.py`, `asyncio_mode = auto`

---

## Documentación Completa

| Documento | Contenido | Líneas |
|-----------|-----------|:------:|
| [README.md](../README.md) | Guía maestra del ecosistema | ~400 |
| [backend/README.md](../backend/README.md) | Arquitectura del backend | ~350 |
| [frontend/README.md](../frontend/README.md) | Arquitectura del frontend | ~350 |
| [etl/README.md](../etl/README.md) | Pipeline ETL | ~350 |
| [Bitacora_SPHERE.md](../Bitacora_SPHERE.md) | Historial de desarrollo (NO TOCAR) | 666 |
| [PLAN_AUTH_MULTITENANT.md](../PLAN_AUTH_MULTITENANT.md) | Plan de multi-tenancy (NO TOCAR) | 572 |
| [auditoria.md](../auditoria.md) | Auditoría de calidad 6.5/10 (NO TOCAR) | 441 |
| [improve_quality.md](../improve_quality.md) | Plan de mejora (NO TOCAR) | 292 |
| [Resumen_Backend.md](../Resumen_Backend.md) | Cronología backend (NO TOCAR) | 752 |
| [Resumen_Frontend.md](../Resumen_Frontend.md) | Cronología frontend (NO TOCAR) | 452 |
| [Reporte_Arquitectura.md](../Reporte_Arquitectura.md) | Topología del sistema (NO TOCAR) | 29 |
