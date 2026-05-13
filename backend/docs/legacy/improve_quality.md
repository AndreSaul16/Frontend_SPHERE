# 🔧 Plan de Mejora de Calidad — Proyecto SPHERE

**Fecha de creación**: 01 de Abril, 2026
**Estado actual**: 6.5/10 — Buen proyecto estudiantil/early-career
**Objetivo**: 8-9/10 — Nivel producción / Silicon Valley

---

## 📋 Índice

1. [Auditoría Actual](#auditoría-actual)
2. [Problemas Detectados](#problemas-detectados)
3. [Plan de Mejora (Priorizado)](#plan-de-mejora-priorizado)
4. [Gaps de Documentación](#gaps-de-documentación)
5. [Gaps de Fechas](#gaps-de-fechas)
6. [Métricas de Éxito](#métricas-de-éxito)

---

## 📊 Auditoría Actual

### Puntuación por Área

| Área | Nota | Objetivo | Prioridad |
|------|------|----------|-----------|
| Clean Architecture | 5/10 | 8/10 | 🔴 Alta |
| SOLID Principles | 6/10 | 8/10 | 🔴 Alta |
| Clean Code | 7/10 | 9/10 | 🟡 Media |
| Testing | 4/10 | 8/10 | 🔴 Alta |
| Security | 2/10 | 7/10 | 🔴 Alta |
| DevOps / CI/CD | 1/10 | 7/10 | 🟡 Media |
| Documentation | 7/10 | 9/10 | 🟢 Baja |

### Lo que está BIEN ✅

- Logging estructurado con iconos y niveles por módulo (`logger.py`)
- Pydantic v2 para validación de requests con `field_validator` y `Field` constraints
- Tool Registry pattern bien implementado (`registry.py` — SHARED_TOOLS + ROLE_TOOLS)
- N8NClient con HMAC-SHA256, timeout configurable, lifecycle (start/close)
- Document Processor pipeline completo: parse → chunk (tiktoken) → embed (OpenAI batch) → store (MongoDB Vector Search)
- Prompts enriquecidos con identidad (Oberon, Nexus, Vortex, Ledger), directiva anti-imitación
- LLM dinámico para custom agents (modelo y temperatura propios)
- RAG per-agent con `agent_target` filtering
- Agent CRUD con PATCH `exclude_unset`, DELETE que limpia KB + GridFS
- SSE streaming con parser de artefactos de baja latencia
- TypeScript estricto en frontend
- Separación de tipos (`types/index.ts`, `types/artifact.ts`)
- Error handling custom (`errors.ts` — NetworkError, SessionError)

---

## 🚨 Problemas Detectados

### BACKEND

#### B1: Sin capa de Servicios (Clean Architecture rota)
**Gravedad**: 🔴 Crítica
**Archivos afectados**: `api/v1/sessions.py`, `api/v1/agents.py`, `api/v1/stream.py`

Los routes importan `get_sessions_collection()` y hacen queries MongoDB directamente. No hay separación entre controller, service y repository.

```
❌ ACTUAL:
  api/v1/sessions.py  → define MODELOS + accede a MongoDB DIRECTO
  api/v1/agents.py    → define MODELOS + accede a MongoDB DIRECTO

✅ OBJETIVO:
  api/v1/sessions.py       → solo rutas (controller)
  services/session_service.py  → lógica de negocio
  repositories/session_repo.py → acceso a datos
  models/session.py            → modelos Pydantic (ya empezó, no se usa)
```

**Ejemplo concreto** (sessions.py línea 96):
```python
result = await sessions_collection.insert_one(new_session)  # ← Route accede a DB
```

#### B2: Orchestrator conecta DB al importar el módulo
**Gravedad**: 🔴 Crítica
**Archivos afectados**: `core/orchestrator.py` (líneas 408-419)

```python
# Se ejecuta al IMPORTAR el módulo — testing imposible
db.connect()
sync_client = db.get_sync_client()
checkpointer = MongoDBSaver(sync_client)
app = workflow.compile(checkpointer=checkpointer)
```

Esto impide:
- Importar el módulo sin conexión a MongoDB (tests, scripts)
- Usar mocks de base de datos
- Hacer hot-reload en desarrollo

#### B3: Orchestrator hace 5 cosas (SRP violado)
**Gravedad**: 🟡 Media
**Archivos afectados**: `core/orchestrator.py` (433 líneas)

El archivo configura LMs, define prompts, implementa router, implementa agente, compila grafo, y ejecuta DB. Debería separarse en:
- `orchestrator/prompts.py` — todos los prompts
- `orchestrator/nodes.py` — router_node, agent_node, final_node
- `orchestrator/graph.py` — compilación del grafo
- `orchestrator/llm_factory.py` — creación de instancias LLM

#### B4: `user_id = "default_user"` hardcodeado en 5+ archivos
**Gravedad**: 🔴 Crítica (Security)
**Archivos afectados**: `sessions.py`, `agents.py`, `useChatStore.ts`, `api.ts`

No hay autenticación. Cualquier request es tratada como el mismo usuario.

#### B5: Sin inyección de dependencias (DIP violado)
**Gravedad**: 🟡 Media
**Archivos afectados**: Todos los que importan `db`, `get_*_collection()`

Los módulos de alto nivel importan implementaciones concretas directamente:
```python
from app.core.database import db, get_custom_agents_collection  # ← Acoplamiento directo
```

#### B6: `BrainConfig.model` default inconsistente
**Gravedad**: 🟢 Baja
**Archivos afectados**: `agents.py` (deepseek-r1) vs `orchestrator.py` (deepseek-chat)

---

### FRONTEND

#### F1: `useChatStore.ts` — God Object (723 líneas)
**Gravedad**: 🔴 Crítica
**Archivos afectados**: `frontend/src/store/useChatStore.ts`

Un solo store maneja: agentes, sesiones, mensajes, artefactos, streaming, UI state. Debería dividirse en:
- `useSessionStore.ts` — sesiones, mensajes por sesión
- `useAgentStore.ts` — agentes core + custom
- `useArtifactStore.ts` — artefactos, panel state
- `useUIStore.ts` — sidebar, modal, layout

#### F2: `window[]` globals para streaming de artefactos
**Gravedad**: 🔴 Crítica
**Archivos afectados**: `useChatStore.ts` (líneas 590, 594, 605, 644, 663)

```typescript
// @ts-ignore
window[`__streamingArtifact_${targetSessionId}`] = artifactId;  // ← GLOBAL MUTATION
```

Esto rompe SSR, concurrent rendering, y es un memory leak potencial. Debe moverse al Zustand state.

#### F3: Múltiples `any` y `@ts-ignore`
**Gravedad**: 🟡 Media
**Archivos afectados**: `useChatStore.ts`, `api.ts`, `ChatPanel.tsx`

TypeScript estricto pierde valor si hay `any` y `@ts-ignore` sueltos.

#### F4: Comentarios TODO/code review en código de producción
**Gravedad**: 🟢 Baja
**Archivos afectados**: `useChatStore.ts` (líneas 263-272)

Comentarios como "I should update api.ts first ideally" quedaron en código.

---

### DEVOPS

#### D1: Sin CI/CD
**Gravedad**: 🟡 Media

Tests existen (6 backend + 10 frontend) pero no hay GitHub Actions para correrlos automáticamente.

#### D2: Sin auth/JWT
**Gravedad**: 🔴 Crítica

Endpoint de usuarios, tokens de sesión, middleware de autenticación — todo ausente.

#### D3: CORS abierto
**Gravedad**: 🟡 Media

No se verificó `main.py` en detalle pero el patrón general de la app sugiere CORS sin restricciones.

---

## 📈 Plan de Mejora (Priorizado)

### Fase 0: Fundación 🔴 (Semana 1)
> Bloquea todo lo demás si no se resuelve

| # | Tarea | Archivos | Impacto |
|---|-------|----------|---------|
| 0.1 | **Auth básica JWT** — endpoint login, middleware auth, reemplazar `default_user` | `backend/app/api/v1/auth.py`, `backend/app/middleware/auth.py`, todos los endpoints | Security crítico |
| 0.2 | **Fix orchestrator DB at import** — mover DB connect a lifespan de FastAPI | `orchestrator.py`, `main.py` | Testing habilitado |
| 0.3 | **Matar window[] globals** — mover streaming artifact state a Zustand | `useChatStore.ts` | Clean Code |

### Fase 1: Separación de Capas 🔴 (Semana 2)
> Clean Architecture real

| # | Tarea | Archivos | Impacto |
|---|-------|----------|---------|
| 1.1 | **Crear `services/`** — `session_service.py`, `agent_service.py` | Nuevo directorio | Clean Arch |
| 1.2 | **Crear `repositories/`** — `session_repo.py`, `agent_repo.py` | Nuevo directorio | Clean Arch |
| 1.3 | **Refactor routes** — sessions.py y agents.py solo llaman a services | Modificar existentes | Clean Arch |
| 1.4 | **Usar `app/models/`** — mover Pydantic models de routes a models/ | `models/session.py`, `models/agent.py` | SRP |
| 1.5 | **Split orchestrator** — prompts, nodes, graph, llm_factory | `core/orchestrator/` como paquete | SRP |

### Fase 2: Frontend Modular 🟡 (Semana 3)
> Matar el God Store

| # | Tarea | Archivos | Impacto |
|---|-------|----------|---------|
| 2.1 | **Split useChatStore** — session, agent, artifact, UI stores | `store/use*Store.ts` | SRP |
| 2.2 | **Eliminar todos los `any`** — tipos estrictos en api.ts y store | Múltiples | Clean Code |
| 2.3 | **Eliminar `@ts-ignore`** — reemplazar con proper typing | Múltiples | Clean Code |
| 2.4 | **Limpiar TODOs/code review comments** | `useChatStore.ts` | Clean Code |

### Fase 3: Testing & CI 🟡 (Semana 4)
> Que los tests corran solos

| # | Tarea | Archivos | Impacto |
|---|-------|----------|---------|
| 3.1 | **GitHub Actions** — pipeline de tests en PR | `.github/workflows/ci.yml` | DevOps |
| 3.2 | **Test coverage** — mínimo 70% en módulos críticos | `tests/` | Calidad |
| 3.3 | **Integration tests** — test de endpoints con DB mock | `tests/integration/` | Confianza |
| 3.4 | **Frontend tests** — vitest para stores y components | `frontend/tests/` | Confianza |

### Fase 4: Hardening 🟢 (Semana 5)
> Producción-ready

| # | Tarea | Archivos | Impacto |
|---|-------|----------|---------|
| 4.1 | **Rate limiting** — middleware para endpoints de streaming | `middleware/rate_limit.py` | Security |
| 4.2 | **Input sanitization** — XSS en mensajes, path traversal en uploads | Varios | Security |
| 4.3 | **Pagination** — list endpoints con skip/limit | `sessions.py`, `agents.py` | Performance |
| 4.4 | **Error responses estandarizadas** — formato JSON consistente | `middleware/error_handler.py` | API Design |
| 4.5 | **Structured logging JSON** — para producción (no colores) | `logger.py` | Observabilidad |

---

## 📝 Gaps de Documentación (Archivos en .md de raíz)

Cosas que existen en código pero NO están documentadas en ningún .md de raíz:

| Cosa | Ubicación | Dónde debería documentarse |
|------|-----------|---------------------------|
| `phantom_front.py` — stress test SSE | `backend/` | `Resumen_Backend.md` o nuevo `Docs/TESTING.md` |
| `logger.py` — sistema de logging | `backend/app/core/` | `Resumen_Backend.md` |
| `errors.ts` — errores custom | `frontend/src/lib/` | `Resumen_Frontend.md` |
| `artifactDetector.ts` | `frontend/src/utils/` | `Resumen_Frontend.md` |
| Tests (6 backend + 10 frontend) | `*/tests/` | Nuevo `Docs/TESTING.md` |
| `app/tools/` — 21 herramientas | `backend/app/tools/` | `Resumen_Backend.md` (actualizar) |
| `app/core/document_processor.py` | `backend/app/core/` | `Resumen_Backend.md` (actualizar) |

---

## 📅 Gaps de Fechas (Commits sin documentar)

| Fecha | Commits | ¿Qué falta documentar? |
|-------|---------|------------------------|
| 16 Mar 2026 | `Sync to work on another computer` (×3), `Migrate project documentation` | ¿Qué se migró? ¿Qué se sincronizó? |
| 17 Mar 2026 | `Cambios en backend configuracion y api endpoints` | ¿Qué endpoints cambiaron? |
| 17 Mar 2026 | `Cambios en componentes artifacts y dependencias` | ¿Qué dependencias? ¿Qué artifacts? |

**Acción**: Investigar `git diff` de esos commits vs el anterior y documentar en la Bitácora.

---

## 🎯 Métricas de Éxito

Cuando el plan esté completo, deberíamos poder decir:

- [ ] **Clean Architecture**: Routes → Services → Repositories en todos los endpoints
- [ ] **SOLID**: 0 imports directos de `db` en routes. Inyección de dependencias en services.
- [ ] **Clean Code**: 0 `any`, 0 `@ts-ignore`, 0 `window[]` globals
- [ ] **Testing**: 70%+ cobertura, CI corriendo en cada PR
- [ ] **Security**: JWT auth, rate limiting, input sanitization
- [ ] **useChatStore**: < 200 líneas, dividido en 3-4 stores
- [ ] **orchestrator.py**: < 150 líneas, dividido en paquete
- [ ] **Documentación**: Todos los módulos con sección en .md de raíz
- [ ] **Fechas**: Bitácora actualizada con commits del 16-17 marzo

---

## 🔗 Referencias

- Clean Architecture: Robert C. Martin — [cleanarchitecture.com](https://cleanarchitecture.com)
- SOLID: [en.wikipedia.org/wiki/SOLID](https://en.wikipedia.org/wiki/SOLID)
- FastAPI Project Structure: [fastapi.tiangolo.com/best-practices](https://fastapi.tiangolo.com/best-practices/)
- Zustand Best Practices: [github.com/pmndrs/zustand](https://github.com/pmndrs/zustand)

---

*Documento generado por auditoría del 01 de Abril, 2026*
*Próxima revisión: al completar Fase 0*
