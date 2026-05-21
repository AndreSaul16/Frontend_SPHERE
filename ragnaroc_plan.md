# 🔱 Plan Ragnarök v3.0 — Auditoría Final de Producción SPHERE

> **Última revisión:** Pasada profunda #3 — Análisis completo Backend + Frontend  
> **Estado:** Pre-producción | Bloqueadores activos: **4 CRÍTICOS**, 6 altos, 8 medios  
> **Stack:** FastAPI · Next.js/Vite · MongoDB Atlas · Redis · Firebase Auth · Stripe · n8n · LangGraph

---

## 🚨 PRIORIDAD 1 — BLOQUEADORES DE PRODUCCIÓN (CRÍTICOS)

### CRIT-01: 🔓 Fallo Total del Distributed Lock en Streaming
- **Archivo:** [`stream.py` L496-498](backend/app/presentation/api/v1/stream.py)
- **Problema:** El `lock.release()` está en el bloque `finally` de la función que **retorna** el `StreamingResponse`. En FastAPI, `StreamingResponse` devuelve control inmediatamente al cliente — el generador corre en background. Esto significa que el lock se libera en el **milisegundo** que empieza el stream.
- **Impacto:** Un usuario puede enviar 10 mensajes paralelos al mismo chat, corrompiendo el grafo de LangGraph (race conditions en checkpoints de MongoDB). **Destruye la integridad del historial de conversación.**
- **Fix requerido:** Mover `lock.release()` dentro del generador `generate_chat_events()`, como última instrucción del `finally` interno del generador.

### CRIT-02: 👻 "Ghost Users" por Colisión de Email (Autenticación)
- **Archivo:** [`auth.py` L299-326](backend/app/core/auth.py)
- **Problema:** Cuando hay un `DuplicateKeyError` por email (ej: usuario se registra con Google y luego con email/password usando el mismo correo), el catch asume que el usuario existe bajo el nuevo `firebase_uid`. Ejecuta `update_one({"firebase_uid": uid}, ...)` contra un UID que **no existe en la DB**.
- **Impacto:** `_auto_provision_user` retorna un dict en memoria (`new_user`) que nunca se persistió. El usuario navega como "fantasma" — puede chatear pero sus sesiones, agentes y pagos quedan huérfanos. **Cualquier operación de escritura vinculada a su user_id fallará silenciosamente.**
- **Fix requerido:** Detectar si el conflicto es por email y, si el `firebase_uid` difiere, hacer merge de cuentas o rechazar el login con un error explicativo.

### CRIT-03: 💸 Fuga de Créditos en Streams Interrumpidos
- **Archivo:** [`stream.py` L390-399](backend/app/presentation/api/v1/stream.py)
- **Problema:** `areserve_and_charge()` descuenta el crédito **antes** de empezar el stream. Si el cliente cierra la conexión (desconexión, pestaña cerrada, error de red), el `GeneratorExit` del generador puede no ejecutar la lógica de reembolso, especialmente si el worker de FastAPI/Uvicorn mata el task.
- **Impacto:** Los usuarios pierden créditos sin recibir respuesta. En un plan Starter con 200 mensajes, cada fuga es directamente dinero perdido.
- **Fix requerido:** Implementar patrón de "cobro optimista con reconciliación" — reservar el crédito, ejecutar el stream, y confirmar/revertir en un `finally` robusto dentro del generador.

### CRIT-04: 🔒 Bypass SSL en ETL Spider (Producción)
- **Archivo:** `backend/infrastructure/etl/core/base_spider.py` (L52)
- **Problema:** `tlsAllowInvalidCertificates=True` con comentario `# ⚠️ Bypass SSL para desarrollo`.
- **Impacto:** Cualquier operación de scraping del ETL en producción es vulnerable a ataques MITM.
- **Fix requerido:** Reemplazar con `tlsCAFile=certifi.where()` y `tlsAllowInvalidCertificates=False`.

---

## ⚠️ PRIORIDAD 2 — PROBLEMAS ALTOS (Funcionalidad rota o degradada)

### HIGH-01: Datos Hardcodeados del Desarrollador en ProfilePage
- **Archivo:** [`ProfilePage.tsx` L92, L113](frontend/src/pages/ProfilePage.tsx)
- **Problema:** El nombre "Saúl" está hardcodeado en la UI del perfil (`<h2>Saúl</h2>` y `<input defaultValue="Saúl">`).
- **Impacto:** **Cualquier usuario** que acceda a su perfil verá "Saúl" como nombre predeterminado en vez de sus datos reales de Firebase/MongoDB.
- **Fix:** Reemplazar con `user.display_name` dinámico del store/API.

### HIGH-02: AgentDetailPage No Envía Token de Autenticación
- **Archivo:** [`AgentDetailPage.tsx` L250, L301, L336](frontend/src/pages/AgentDetailPage.tsx)
- **Problema:** Las peticiones `fetch()` para GET, PATCH y DELETE del agente **no incluyen headers de autenticación** (`Authorization: Bearer`).
- **Impacto:** Todas las operaciones CRUD de agentes desde la página de detalle fallarán con **401 Unauthorized** en producción. El usuario verá errores al intentar ver, editar o eliminar sus agentes.
- **Fix:** Usar `authHeaders()` en todas las peticiones como se hace en `api.ts`.

### HIGH-03: MOCK_AGENTS Hardcodeados en el Frontend
- **Archivo:** [`useChatStore.ts` L63+](frontend/src/store/useChatStore.ts)
- **Problema:** Los agentes Core (CEO, CTO, CMO, CFO) están completamente hardcodeados como constantes locales, no se cargan desde el backend.
- **Impacto:** Si se cambian nombres, colores o prompts de agentes core en el backend, el frontend no reflejará los cambios sin re-deploy. Además, la lista de IDs hardcodeados (`ceo-1`, `cto-1`, etc.) en `createNewSession` (L254) es frágil.
- **Fix:** Crear un endpoint `/api/v1/agents/core` que sirva los agentes del sistema y consumirlo en `fetchCoreAgents()`.

### HIGH-04: Fallos Silenciosos en Webhooks de Stripe
- **Archivo:** [`webhooks.py` L156](backend/app/presentation/api/v1/webhooks.py)
- **Problema:** Si `stripe.Subscription.retrieve()` falla en `invoice.payment_succeeded`, se hace `pass` silencioso.
- **Impacto:** `current_period_end` queda como `None`, rompiendo la lógica de expiración de subscripción. El usuario podría mantener acceso indefinido o perderlo inmediatamente.

### HIGH-05: Fallos Silenciosos en GridFS (Agentes)
- **Archivo:** [`agents.py` L315](backend/app/presentation/api/v1/agents.py)
- **Problema:** Al eliminar un agente custom, si la eliminación de archivos en GridFS falla, se silencia con `except Exception: pass`.
- **Impacto:** Archivos huérfanos en MongoDB. Fuga de almacenamiento gradual sin registro.

### HIGH-06: Modelo Frontend ≠ Modelo Backend (ALLOWED_MODELS)
- **Archivo:** [`AgentDetailPage.tsx` L28](frontend/src/pages/AgentDetailPage.tsx) vs [`agents.py` L20](backend/app/presentation/api/v1/agents.py)
- **Problema:** El frontend solo muestra `["deepseek-chat", "deepseek-r1"]` (2 modelos). El backend acepta `{"deepseek-chat", "deepseek-r1", "gpt-4o", "gpt-4o-mini"}` (4 modelos).
- **Impacto:** Los usuarios no pueden seleccionar GPT-4o/4o-mini desde la UI aunque el backend lo soporte. Y si un agente fue creado con GPT-4o vía API, la UI lo mostrará como "deepseek-chat" por el fallback (L264).

---

## 🔧 PRIORIDAD 3 — PROBLEMAS MEDIOS (Deuda técnica y UX)

### MED-01: Console.logs de Debug en Producción
- **Archivos:** `useChatStore.ts` (8 ocurrencias), `api.ts` (1 ocurrencia)
- **Problema:** Logs de debug con emojis (`📦`, `🌐`, `🔌`, `🛑`, `🗑️`) quedan en producción.
- **Impacto:** Exposición de datos internos (session IDs, agent IDs) en la consola del navegador del usuario. No es un riesgo de seguridad directo pero es unprofessional y facilita ingeniería inversa.
- **Fix:** Wrappear en `if (import.meta.env.DEV)` o eliminar.

### MED-02: Comentarios de "Inseguridad Arquitectónica" en createNewSession
- **Archivo:** [`useChatStore.ts` L274-282](frontend/src/store/useChatStore.ts)
- **Problema:** Hay 8 líneas de comentarios del desarrollador expresando duda sobre la firma de `chatService.createSession`: *"I should update api.ts too"*, *"Let's assume I need to update api.ts too, but for now let's pass loosely"*.
- **Impacto:** Indica que la integración Front↔Back puede estar desalineada. El payload de `createSession` actual (`api.ts` L190-218) parece correcto, pero estos comentarios generan desconfianza y deben limpiarse.

### MED-03: Revocación OAuth de Notion No Implementada
- **Archivo:** [`notion.py` L44](backend/app/infrastructure/integrations/providers/notion.py)
- **Problema:** `revoke(token)` es `pass`. El token de Notion sigue activo tras "desconectar".
- **Impacto:** Riesgo de privacidad — un token activo puede seguir leyendo datos del workspace del usuario.

### MED-04: N8N Deploy No Compara Contenido de Workflows
- **Archivo:** [`n8n_deployer.py` L213](backend/app/infrastructure/n8n_deployer.py)
- **Problema:** `# TODO: Verificar si el contenido difiere y actualizar`. Workflows existentes se marcan como `skipped` sin verificar si su contenido cambió.
- **Impacto:** Cambios en los JSONs de workflow no se propagarán a n8n hasta que se elimine manualmente el workflow existente.

### MED-05: Fallback de Scraping CMO Ausente
- **Archivo:** `backend/infrastructure/etl/agents/cmo/blogs_spider.py` (L76)
- **Problema:** `# TODO: Implementar fallback con BeautifulSoup`.
- **Impacto:** Scraping de blogs falla silenciosamente sin plan B.

### MED-06: Aliases Muertos en database.py
- **Archivo:** [`database.py` L275-277](backend/app/infrastructure/database.py)
- **Problema:** `sessions_collection`, `checkpoints_collection`, `custom_agents_collection` están definidos como `property()` en el scope del módulo, no dentro de una clase. Son código muerto.
- **Impacto:** No causa bugs pero indica refactorización incompleta. Confunde a nuevos desarrolladores.

### MED-07: Rate Limiter Custom Potencialmente Incompatible
- **Archivo:** [`main.py` L337-355](backend/main.py)
- **Problema:** `_optional_rate_limiter` importa `pyrate_limiter.Limiter` y `fastapi_limiter.depends.RateLimiter` pero los mezcla de forma no estándar. La instanciación de `RateLimiter` con un `limiter` de `pyrate_limiter` puede no ser compatible con `fastapi-limiter`.
- **Impacto:** El rate limiting puede no funcionar correctamente, permitiendo abuso de la API sin throttling.

### MED-08: BillingPage Duplica authHeaders() 
- **Archivo:** [`BillingPage.tsx` L6-18](frontend/src/pages/BillingPage.tsx)
- **Problema:** Define su propia función `authHeaders()` idéntica a la de `api.ts`. Duplicación de código.
- **Impacto:** Si se cambia la lógica de auth en un lugar, el otro queda desactualizado. Debe importar desde `api.ts`.

---

## 📋 PRIORIDAD 4 — COSMÉTICOS Y POLISH

### LOW-01: getCustomAgents() No Valida Response
- **Archivo:** [`api.ts` L250-255](frontend/src/services/api.ts)
- **Problema:** `chatService.getCustomAgents()` no verifica `response.ok` antes de parsear JSON.
- **Impacto:** Si el servidor retorna un error HTTP, se intentará parsear el body de error como JSON de agentes, causando una excepción críptica o datos corruptos en el store.

### LOW-02: createCustomAgent() No Valida Response
- **Archivo:** [`api.ts` L257-264](frontend/src/services/api.ts)
- **Problema:** Mismo problema que LOW-01. `response.json()` sin verificar `response.ok`.

### LOW-03: deleteCustomAgent() Silencia Errores
- **Archivo:** [`api.ts` L276-281](frontend/src/services/api.ts)
- **Problema:** El `await fetch(...)` no verifica status. Si la eliminación falla en el servidor, el frontend procede como si hubiera tenido éxito.

### LOW-04: Test de Jules Es Falso Positivo
- **Archivo:** [`auth.py` L504-510](backend/app/presentation/api/v1/auth.py)
- **Problema:** `test_service_credential("jules")` siempre retorna `success: True` con mensaje "test no disponible aún".
- **Impacto:** El usuario cree que su API key de Jules funciona cuando en realidad nunca se verifica.

### LOW-05: Tildes Faltantes en UI Español
- **Archivos:** `AgentDetailPage.tsx` — "Descripcion", "Configuracion", "accion", "proposito", "Rapido", "Metodo"
- **Impacto:** Errores ortográficos menores pero que reducen la percepción de calidad profesional.

### LOW-06: CircuitBreaker reset innecesario en estado CLOSED
- **Archivo:** [`circuit_breaker.py` L113-115](backend/app/core/circuit_breaker.py)
- **Problema:** `record_success()` escribe a Redis incluso cuando el circuito ya está `CLOSED` con 0 failures.
- **Impacto:** Escritura innecesaria a Redis en cada request exitoso. Desperdicio de IO.

---

## 🗺️ MAPA DE ACCIÓN PRIORIZADO

| # | Ticket | Severidad | Esfuerzo | Impacto si no se arregla |
|---|--------|-----------|----------|--------------------------|
| 1 | CRIT-01 | 🔴 Crítico | 30 min | Corrupción de datos de chat |
| 2 | CRIT-02 | 🔴 Crítico | 1 hora | Usuarios fantasma, datos huérfanos |
| 3 | CRIT-03 | 🔴 Crítico | 1 hora | Pérdida de dinero del usuario |
| 4 | CRIT-04 | 🔴 Crítico | 10 min | Vulnerabilidad de seguridad |
| 5 | HIGH-01 | 🟠 Alto | 15 min | Todo usuario ve "Saúl" |
| 6 | HIGH-02 | 🟠 Alto | 20 min | CRUD de agentes roto al 100% |
| 7 | HIGH-03 | 🟠 Alto | 2 horas | Agentes core desincronizados |
| 8 | HIGH-04 | 🟠 Alto | 30 min | Suscripciones corruptas |
| 9 | HIGH-05 | 🟠 Alto | 15 min | Fuga de almacenamiento |
| 10 | HIGH-06 | 🟠 Alto | 30 min | UI muestra modelos incorrectos |
| 11 | MED-01 | 🟡 Medio | 15 min | Datos expuestos en consola |
| 12 | MED-02 | 🟡 Medio | 5 min | Ruido en el código |
| 13 | MED-03-08 | 🟡 Medio | 2 horas | Deuda técnica acumulada |
| 14 | LOW-01-06 | 🟢 Bajo | 1 hora | Polish profesional |

### Tiempo Total Estimado: ~9 horas de desarrollo enfocado

---

## ✅ VERIFICACIÓN DE ÁREAS SANAS

Las siguientes áreas fueron auditadas y están **correctas para producción**:

- ✅ **Multi-tenant isolation** — Todas las queries usan `user_id` scope (`tenant.py` helpers)
- ✅ **MongoDB indexes** — Todos los índices críticos se crean en startup (`_ensure_indexes`)
- ✅ **CORS configuration** — Orígenes explícitos, no wildcards
- ✅ **Security headers** — `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- ✅ **Firebase Auth init** — Inicialización correcta con fallback a credenciales de archivo
- ✅ **RAG vector search** — Filtros `user_id` + `agent_target` correctos, sin data leaks
- ✅ **SSE parsing (frontend)** — Manejo robusto de chunks parciales, buffer residual, abort signal
- ✅ **Billing store** — Retry con backoff exponencial, skeleton loading, error recovery
- ✅ **Board Meeting settings** — CRUD completo con validación, warning modal, iteraciones
- ✅ **Database dual-client** — Motor (async) + PyMongo (sync) correctamente separados
- ✅ **Stripe checkout flow** — Validación de topup por tier, portal billing funcional
- ✅ **OAuth flow** — HMAC-signed state, TTL en MongoDB, verificación de firma + expiración
- ✅ **Agent CRUD** — Quota por plan, validación de modelos, response models correctos
- ✅ **Document upload** — XHR con progress tracking, GridFS multi-tenant
- ✅ **Session management** — Idempotente, con visual_config, multi-tipo (direct/group)
- ✅ **Stop Generation** — AbortController propagado correctamente hasta el SSE reader
