# Auditoría de producción SPHERE — Bugs + Roadmap de mejoras

**Fecha:** 2026-06-10 · **Alcance:** backend, frontend, persistencia, billing, RAG, board, integraciones n8n, infra/deploy · **Método:** 6 agentes de exploración + verificación manual de cada hallazgo crítico contra el código (todo lo listado en P0/P1 cita `archivo:línea` comprobado en esta sesión).

> **Rev. 2 (mismo día):** tras revisar los descartes con Saúl se reabrieron y re-verificaron 9 ítems → nuevos A28-A36 y B32. Los descartes confirmados quedan documentados al final de la Parte A.

---

## Resumen ejecutivo

El producto tiene una base sólida (multi-tenant bien planteado, circuit breakers en n8n, idempotencia parcial en Stripe, créditos con refund), pero hay **7 bugs P0 que tocan dinero o datos de usuarios** y que pueden quemar la confianza de los testers en una sola mala experiencia: una fuga multi-tenant latente en el RAG, créditos que se pierden sin compensación cuando algo falla, un webhook de Stripe que puede duplicar o perder compras, y una UI de créditos que muestra saldos incorrectos en cada mensaje.

En mejoras, las 3 palancas con mejor ratio impacto/esfuerzo para que alguien **pague** son:
1. **Hacer visible el valor del board** — hoy un debate de 4 ejecutivos no deja ningún artefacto exportable ni muestra su coste antes de lanzarlo.
2. **Onboarding + analytics** — el usuario nuevo aterriza en una interfaz vacía y tú no tienes ningún dato de qué hace (no hay PostHog/GA: vas a ciegas para iterar).
3. **Citas y control en el RAG** — sin fuentes clicables ni feedback de fallos de procesado, el usuario no confía en las respuestas "basadas en sus documentos".

---

# PARTE A — BUGS

## P0 — Rompen confianza YA (dinero / datos)

### A1. Fuga multi-tenant en el fallback del RAG 🔴 CRÍTICO
**Dónde:** [backend/app/application/rag.py:138-156](../backend/app/application/rag.py)
**Qué pasa:** si `$vectorSearch` falla con "needs to be indexed as filter" (índice mal configurado tras un re-create, migración o cambio de cluster), el código reintenta la búsqueda **eliminando el filtro `user_id`** y devuelve los resultados al LLM. Es la misma clase de bug que el leak resuelto en abril — el path principal filtra, este fallback quita el filtro a propósito.
**Historia de usuario:** María pregunta a su agente por "el contrato" y la respuesta incluye fragmentos del contrato de otro cliente. Game over para ese tester.
**Fix:** eliminar el reintento sin filtro. Si el índice no soporta el filtro, **fail closed**: devolver "Error recuperando contexto" y loguear con nivel CRITICAL (es un problema de infraestructura que debes ver tú, no parchearse solo leakeando datos).
**Test:** mockear `collection.aggregate` para lanzar `Exception("needs to be indexed as filter")` → assert que el resultado es el mensaje de error y que **nunca** se ejecuta un pipeline sin `filter.user_id`.
**Esfuerzo:** S (borrar ~25 líneas + test).

### A2. Webhook de Stripe: créditos duplicados o compras perdidas 🔴 CRÍTICO
**Dónde:** [backend/app/presentation/api/v1/webhooks.py:85-140](../backend/app/presentation/api/v1/webhooks.py)
**Qué pasa (2 modos de fallo):**
1. El check de idempotencia (L85) y el registro del evento procesado no son atómicos con el grant. Si el proceso muere entre `_grant_topup()` y el insert del evento procesado, Stripe reintenta y **vuelve a otorgar los créditos** (usuario paga 39€, recibe 300 créditos en vez de 150 — pérdida directa de ingresos).
2. Si la metadata viene malformada (`user_id`/`plan_id` ausentes, L99-100) solo se hace `logger.error` y se sigue: **el usuario pagó y no recibe nada**, sin registro en ninguna colección para que soporte pueda compensarle.
**Fix:**
- Insertar el registro de idempotencia **primero** con `{"_id": event_id, "status": "processing"}` (el `_id` único hace de lock natural — un retry concurrente falla el insert y devuelve "already processed"); hacer el grant; actualizar a `"done"`. Si el proceso muere a mitad, un retry encuentra `processing` → reintenta el grant de forma segura si el grant también es idempotente (usar `stripe_event_id` como clave única en `credit_transactions`).
- Para metadata malformada: insertar en una colección `failed_payments` con el objeto completo + devolver 200 (que Stripe no reintente infinito) + log CRITICAL.
**Test:** procesar el mismo `event_id` dos veces → un solo grant en wallet y una sola transaction. Evento con metadata rota → documento en `failed_payments`, respuesta 200.
**Esfuerzo:** M.

### A3. Créditos perdidos en silencio cuando el refund falla 🔴 CRÍTICO
**Dónde:** [backend/app/presentation/api/v1/stream.py:376-398](../backend/app/presentation/api/v1/stream.py) y [stream.py:580-587](../backend/app/presentation/api/v1/stream.py)
**Qué pasa:**
- En `GeneratorExit` (usuario pulsa stop / pierde conexión) y en error de inferencia, si `arefund()` lanza excepción solo se loguea → el usuario pagó 1-5 créditos por nada.
- Peor: en L583 el refund por `lock_not_acquired` **no está envuelto en try/except** — si falla, en vez del 409 amigable el usuario recibe un 500 **y además pierde el crédito**.
**Historia de usuario:** Pedro manda un mensaje justo cuando Mongo tiene un blip. Pierde el crédito, ve un error feo y su saldo no cuadra. Con 50 créditos gratis, cada uno cuenta.
**Fix:** (1) envolver el refund de L583 en try/except para que el 409 siempre llegue; (2) cuando un refund falle, insertar en colección `pending_refunds {user_id, charge_ctx, reason, created_at}` y reintentarlo de forma lazy (al siguiente request del usuario o un job al arrancar) — el usuario nunca debe perder créditos por un fallo transitorio.
**Test:** mockear `arefund` para lanzar → assert respuesta 409 (no 500) y documento en `pending_refunds`.
**Esfuerzo:** M.

### A4. La UI resta créditos dos veces por mensaje (y solo 1 en boards que cuestan 5) 🔴
**Dónde:** [frontend/src/components/chat/ChatPanel.tsx:177-183](../frontend/src/components/chat/ChatPanel.tsx) + [frontend/src/services/api.ts:93-96](../frontend/src/services/api.ts)
**Qué pasa:** `handleSendMessage` llama a `decrementOptimistic()` (L182) **y** `streamChat` vuelve a llamarlo cuando el stream abre (api.ts L93-96). Resultado: cada mensaje resta 2 en pantalla hasta que `[DONE]` dispara `refresh()`. Si el stream falla antes de `[DONE]`, no hay reconciliación hasta el polling de 60s del `CreditsIndicator`. Y en board mode resta 1 cuando el coste real es 5 (`BOARD_MEETING_COST`, [stream.py:537](../backend/app/presentation/api/v1/stream.py)).
**Historia de usuario:** el tester con 10 créditos manda 3 mensajes y ve "4" en el contador. Concluye que le estás cobrando de más. Es exactamente el tipo de desconfianza que mata un producto de créditos.
**Fix:** quitar la llamada de `ChatPanel` (dejar solo la de `api.ts`, que ya está bien situada tras `response.ok`); pasar el coste real (1 o 5 según board) a `decrementOptimistic(cost)`; llamar a `refresh()` también en el path de error del stream.
**Test:** vitest sobre el store — enviar mensaje normal → -1; board → -5; stream con error → refresh llamado.
**Esfuerzo:** S.

### A5. Pins y ratings se "pierden" en silencio 🔴
**Dónde:** [frontend/src/services/api.ts:375-405](../frontend/src/services/api.ts)
**Qué pasa:** `pinMessage`, `unpinMessage` y `rateMessage` no comprueban `response.ok` (un 401/500 pasa desapercibido) y `getPins` hace `response.json()` sin validar el status. La UI cambia optimista, el backend nunca lo guardó, y al refrescar el pin/rating "desaparece".
**Fix:** mismo patrón que el resto del archivo (`if (!response.ok) throw new Error(...)`) + en los componentes que los usan, revertir el estado optimista y mostrar toast en el catch.
**Test:** vitest mockeando fetch 500 → la promesa rechaza.
**Esfuerzo:** S (30 min).

### A6. Token expirado: redirect sin limpiar estado → datos de otra cuenta 🔴
**Dónde:** [frontend/src/services/errorHandler.ts:149-154](../frontend/src/services/errorHandler.ts)
**Qué pasa:** en `auth.invalid_token`/`auth.expired_token` se hace `window.location.href = '/'` sin limpiar los stores de Zustand ni caches. En un navegador compartido, el usuario B puede ver flashear mensajes/saldo del usuario A.
**Fix:** crear un helper `clearAllStores()` (chat, billing, deploy, etc. — y reutilizarlo también en logout) y llamarlo antes del redirect. Revisar que el logout actual también lo haga.
**Test:** unit test del helper → todos los stores vuelven a su estado inicial.
**Esfuerzo:** S.

### A7. Documentos RAG atascados en "pending" para siempre 🔴
**Dónde:** [backend/app/application/document_processor.py:236-237 y 273-288](../backend/app/application/document_processor.py)
**Qué pasa:** si el documento se parsea a texto vacío (PDF escaneado, archivo corrupto), el early-return de L236-237 devuelve `failed` **sin actualizar GridFS** → el frontend (que hace polling del status) muestra "procesando…" eternamente. En el path de excepción sí se marca `failed` (L283) pero sin motivo, y un fallo del propio update se traga (`except Exception: pass`, L285-286).
**Historia de usuario:** sube el PDF de su negocio, espera, recarga, sigue "pendiente". Concluye que el RAG no funciona.
**Fix:** marcar `processing_status: "failed"` + `processing_error: <motivo>` en **ambos** paths; exponer `processing_error` en el endpoint de listado; en `KnowledgeBasePanel` mostrar el motivo y un botón "Reintentar" (endpoint nuevo de re-proceso, ~20 líneas reutilizando `process_document`).
**Test:** pytest con bytes vacíos → status `failed` con error en metadata.
**Esfuerzo:** M (S sin el botón retry).

## P1 — Fiabilidad percibida

### A8. Mensaje perdido si el stream falla: input vacío y sin retry
**Dónde:** [ChatPanel.tsx:177-183](../frontend/src/components/chat/ChatPanel.tsx)
El input se vacía de forma síncrona antes de saber si el envío funcionó. Si el stream falla, el texto ya no está y no hay botón de reintentar — hay que reescribir de memoria.
**Fix:** guardar el texto enviado; en `onError`, ofrecer "Reintentar" sobre el mensaje fallido (o restaurar el input). **Esfuerzo:** S.

### A9. Toggle de Board Meeting falla en silencio
**Dónde:** [frontend/src/pages/ChatSettingsPage.tsx:46-75](../frontend/src/pages/ChatSettingsPage.tsx)
`if (resp.ok)` sin `else` y `catch` que solo hace `console.error` (el fetch inicial directamente `catch { /* ignore */ }`). Si falla, el switch revierte sin explicación → el usuario reintenta 3 veces y concluye que la feature está rota.
**Fix:** toast de error + estado visual. Auditar este patrón (`catch` vacío o solo console.error) en el resto de settings — aparece también en updates de nombre/color de sesión (~L158-195 del mismo archivo). **Esfuerzo:** S.

### A10. Upload de documentos sin timeout ni cancelación
**Dónde:** [frontend/src/services/api.ts:326-356](../frontend/src/services/api.ts)
El XHR no tiene `timeout`, ni handler de `timeout`/`abort`, ni botón de cancelar. En una red lenta se queda al 60% para siempre; la única salida es F5.
**Fix:** `xhr.timeout = 120_000` + listener + exponer un método de cancelación al componente. **Esfuerzo:** S.

### A11. Secretos con default vacío arrancan en prod sin avisar
**Dónde:** [backend/app/core/config.py:26-36](../backend/app/core/config.py)
`N8N_WEBHOOK_SECRET: str = ""` y `FERNET_KEY: str = ""`. Si en Railway falta alguna, el backend arranca igual: HMAC firmando con secreto vacío (firma trivialmente falsificable) y cifrado de credenciales de usuarios comprometido o roto.
**Fix:** validación al startup: en `ENVIRONMENT=production`, si `FERNET_KEY` o `N8N_WEBHOOK_SECRET` están vacíos → `RuntimeError` y el contenedor no levanta (mismo patrón que ya usáis con Firebase 503). En la misma validación, assert de que Firebase quedó inicializado (hoy `init_firebase` solo hace `logger.warning` si faltan credenciales, [auth.py:50-53](../backend/app/core/auth.py) — el fail-closed llega después, por request, como 503). Documentar ambas en `RAILWAY.md`. **Esfuerzo:** S.

### A12. Cobro antes del lock distribuido
**Dónde:** [stream.py:555-587](../backend/app/presentation/api/v1/stream.py)
Se cobra (L559) y después se intenta el lock (L579). Dos envíos concurrentes a la misma sesión → ambos cobrados, uno reembolsado (ciclo cobro/refund innecesario que depende de que el refund no falle — ver A3). Invertir el orden (lock → cobro → stream) elimina la ventana. **Esfuerzo:** S-M (cuidado con liberar el lock en todos los paths de error del cobro).

### A28. Texto parcial del asistente se pierde si el cliente se desconecta a mitad de stream ⚠️ (reabierto Rev.2 — confirmado)
**Dónde:** [orchestrator.py:1038-1062](../backend/app/application/orchestrator.py) (`MongoDBSaver` como checkpointer) + [stream.py:376-384](../backend/app/presentation/api/v1/stream.py)
**Qué pasa:** LangGraph persiste el checkpoint **al cerrar cada nodo**, no token a token. Si el usuario recarga/cierra a mitad de la respuesta de un agente, el `GeneratorExit` reembolsa el crédito (verificado, eso sí funciona) pero la respuesta parcial de ese nodo **no llegó a checkpointearse** → al recargar la conversación, ese turno aparece vacío o ausente. En un board (5 nodos) es peor: se pueden perder las intervenciones del agente en curso y las pendientes.
**Historia de usuario:** el CEO está dando una conclusión larga, al usuario se le va el wifi un segundo, recarga y la conclusión no está. Cree que la app "se comió" su respuesta (aunque el crédito se devolvió, eso no lo ve).
**Fix:** bufferizar el texto acumulado del nodo en curso y, en `GeneratorExit`, persistir un mensaje parcial del asistente en la colección de mensajes (marcado `interrupted: true`) antes de reembolsar; el frontend lo muestra con un sello "respuesta interrumpida — regenerar". Alternativa más simple: persistir el assistant message en cada `[DONE]`/cierre de nodo en vez de depender solo del checkpointer.
**Test:** simular `GeneratorExit` tras N tokens → assert que existe un mensaje parcial persistido para esa sesión.
**Esfuerzo:** M. *(Era el descarte #12, el menos firme; al verificar el checkpointer se confirma el riesgo.)*

### A13. Los tests no corren: ni CI ni vitest funcional
**Dónde:** no existe `.github/workflows/` (verificado); [openspec/changes/production-readiness/tasks.md:58](../openspec/changes/production-readiness/tasks.md) admite "Tests blocked by Node 26 + vitest incompatibility".
Hay ~80 tests de backend y 23+ de frontend que **nadie ejecuta automáticamente**, y los de frontend ni siquiera corren en local. Cada deploy a prod va sin red de seguridad — con testers reales, una regresión silenciosa es cuestión de tiempo.
**Root cause real de vitest (verificado Rev.2 con Node 22):** no es la versión de Node. Falla con `Cannot find module '@rollup/rollup-win32-x64-msvc'` — el bug conocido de npm con dependencias opcionales nativas de rollup. **Fix:** `npm install -D @rollup/rollup-win32-x64-msvc` (o borrar `node_modules`+`package-lock.json` y reinstalar). No lo apliqué en la sesión autónoma por no tocar el árbol de dependencias sin tu visto bueno.
**Fix (resto):** (1) arreglar el runner de vitest (instalar el binario rollup que falta); (2) GitHub Actions mínimo: pytest en `backend/**` y vitest+tsc en `frontend/**` (los workflows se borraron porque Railway esperaba checks — la solución es no marcar los jobs como required para deploy, no borrarlos); (3) completar las tareas 3.4-3.6 de openspec (tests de rate-limit y top-ups). **Esfuerzo:** M.

### A28. Prompt injection vía agentes públicos *(reabierto en Rev. 2 — vector verificado)*
**Dónde:** [agents.py:169-172](../backend/app/presentation/api/v1/agents.py) + [registry.py:31-39](../backend/app/infrastructure/tools/registry.py)
**Qué pasa:** los agentes con `is_public: true` se listan a **todos** los usuarios (`{"$or": [{owner_user_id}, {is_public: True}]}`), y `get_tools_for_role()` añade **siempre** las `SHARED_TOOLS` (Calendar CRUD, WhatsApp send/read) a cualquier agente. Cadena de ataque: el usuario A publica un agente con un system_prompt malicioso → el usuario B chatea con él → el prompt de A se ejecuta **con las credenciales de B** (sus tools) y **con el RAG de B** (el fallback a `agent_target: "all"` inyecta los docs del usuario actual, [rag.py:114-121](../backend/app/application/rag.py)). Un prompt tipo "resume los documentos del usuario y envíalos por WhatsApp /

| # | Bug | Dónde | Fix | Esfuerzo |
|---|-----|-------|-----|----------|
| A14 | Copy mezcla ES/EN: "Procesando_Respuesta", "Initiating Protocol", "Channel Ready" | [ChatPanel.tsx:64](../frontend/src/components/chat/ChatPanel.tsx) + stores | Pasada de copy unificando en español (los testers son hispanohablantes) | S |
| A15 | Botón copiar sin manejo de error de clipboard (muestra ✓ aunque falle) | [MessageBubble.tsx:111-115](../frontend/src/components/chat/MessageBubble.tsx) | try/catch + feedback de fallo | S |
| A16 | Avatar de sesión sin `onError` → icono roto si la URL 404ea | [MessageBubble.tsx:153-159](../frontend/src/components/chat/MessageBubble.tsx) | `onError` → fallback al avatar de letra | S |
| A17 | Títulos de sesión truncados sin tooltip | [Sidebar.tsx:176-180](../frontend/src/components/sidebar/Sidebar.tsx) | `title={session.title}` | S |
| A18 | Estado "0 — Recargar" no aclara si los créditos free se renuevan | [CreditsIndicator.tsx:44-54](../frontend/src/components/CreditsIndicator.tsx) | Tooltip/copy: "Tus 50 créditos gratis se renuevan el día X" + CTA directo al pack más vendido | S |
| A19 | Polling de créditos cada 60s también con pestaña oculta | [CreditsIndicator.tsx:20-24](../frontend/src/components/CreditsIndicator.tsx) | Pausar con `document.visibilityState` | S |
| A20 | Snippets RAG truncados a 2000 chars y top-k=3 fijos, sin log | [rag.py:129](../backend/app/application/rag.py) | Log de truncado + hacer configurable (enlaza con mejora B-RAG) | S |
| A29 | Recarga a mitad de stream: la respuesta reaparece completa pero el salto es brusco (parece duplicado/glitch) | api.ts streamChat + loadSession | Al recargar con un turno `interrupted` (ver A28), mostrar estado claro en vez de re-render abrupto | S |
| A30 | Input deshabilitado durante streaming sin indicador visual fuerte (solo cambia el placeholder a "Sistema ocupado…") | [ChatPanel.tsx](../frontend/src/components/chat/ChatPanel.tsx) | Estilo `disabled` visible + spinner junto al input | S |

## P3 — Deuda técnica / docs / infra

| # | Ítem | Acción |
|---|------|--------|
| A21 | `token_budget.py` + su test: **código muerto** — solo lo importan sus propios tests (verificado por grep); `auth.py` solo siembra el campo `token_budget_daily` en el user doc, nadie llama a `check_available`/`consume` | Decidir: cablearlo en `stream.py` como límite anti-abuso diario, o borrarlo (módulo + test + campos del user doc) |
| A22 | `FRONTEND_DEPLOY_STATUS.md` **obsoleto**: dice "frontend BLOQUEADO en f9cb672" pero hay ~10 commits frontend posteriores ya desplegados | Actualizar o borrar (confunde a cualquiera que entre al repo) |
| A23 | `backend/PLAN_PAGOS.md` describe suscripciones Starter/Premium; el código es solo-créditos con plan único ([plan_limits.py:13-17](../backend/app/core/plan_limits.py)) | Mover a `docs/legacy/` y escribir 10 líneas del modelo real |
| A24 | Huérfanos: `frontend/Dockerfile.bak`, `Dockerfile.tmp`, `vitest.config.ts.bak`, `nginx.conf` estático (el bueno es `nginx.conf.template`), `backend/Procfile` (Railway usa railway.toml) | Borrar |
| A25 | `frontend/.env.example` sin `VITE_FIREBASE_MEASUREMENT_ID` | Añadir si analytics lo usa |
| A26 | `railway.toml` healthcheck apunta al alias deprecado `/api/v1/health/health` | Cambiar a `/api/v1/health/ready` (cosmético, funciona) |
| A27 | Docs legacy citan modelos deprecados (deepseek-chat/r1) | Ya están en `/legacy/`, añadir banner "OBSOLETO" en el índice |

### Reabiertos en Rev.2 como deuda menor (P3)

| # | Ítem | Estado verificado | Acción |
|---|------|-------------------|--------|
| A31 | **Prompt injection vía system_prompt de agente custom** | Riesgo cross-tenant **bajo**: `get_tools_for_role` devuelve `[]` para roles custom ([registry.py:31-39](../backend/app/infrastructure/tools/registry.py)), así que un prompt malicioso no puede adquirir tools de CEO/CFO; y el RAG va scoped por `user_id` (salvo el bug A1). El daño se limita al propio agente del usuario. | Sanitizar/validar `default_tools` contra un allowlist al crear el agente; no es urgente, pero conviene dejarlo escrito antes de abrir agentes públicos (B27) |
| A32 | **Whitelist de eventos de Stripe** | Comportamiento **correcto**: eventos desconocidos caen en `else: logger.info` ([webhooks.py:217-218](../backend/app/presentation/api/v1/webhooks.py)) y se registran como procesados (no reintento infinito). | Opcional: documentar el set de eventos manejados; sin acción de código obligatoria |
| A33 | **Portal de billing confía en `stripe_customer_id` del user doc** | Riesgo **bajo**: el doc es el del propio usuario autenticado ([billing.py:56-82](../backend/app/presentation/api/v1/billing.py)), scoped. | Sin acción; anotado por completitud |
| A34 | **Password en login: validación solo HTML5** (`minLength={6}`, [LoginPage.tsx:117](../frontend/src/pages/LoginPage.tsx)) | El backend valida igual; fricción mínima en navegadores que ignoran HTML5. | Añadir validación JS antes del submit con mensaje claro |
| A35 | **Rotación de `FERNET_KEY` sin versionado** | Si algún día rotas la clave, **todas** las credenciales de servicio cifradas de todos los usuarios quedan ilegibles (no hay `key_version` en el metadata). | Añadir `encryption_key_version` al guardar credenciales — seguro operativo barato antes de que tengas muchos usuarios con integraciones |
| A36 | **Creación de sesión: rollback manual en Mongo standalone** | Confirmado ([sessions.py:189-208](../backend/app/presentation/api/v1/sessions.py)): con replica set usa transacción; en standalone hace inserción secuencial con rollback manual que puede fallar en silencio. En prod (Atlas) hay replica set, así que el path seguro está activo. | Documentar "requiere replica set en prod" en SETUP/README; sin cambio de código si Atlas ya lo cumple |
| A37 | **Selección de código en móvil** (claim del agente, **no verificado**) | No pude reproducirlo leyendo el código; los `<pre><code>` no tienen estilos que rompan la selección de forma evidente. | Verificar en dispositivo real antes de tratarlo como bug |

## Quick wins (<30 min cada uno)
A5 (pins/ratings `response.ok`) · A4 parcial (quitar el decrement duplicado) · A16 (avatar onError) · A17 (tooltip) · A24 (borrar huérfanos) · A26 (healthcheck path) · A11 (validación startup de secretos).

## Falsos positivos descartados (no re-auditar)

Estos sí quedan descartados con evidencia dura:

1. ~~"firebase-adminsdk.json commiteado"~~ — NO: está en `.gitignore` (`*firebase-adminsdk*.json`) y `git log --all` no lo registra. Higiene de secretos correcta.
2. ~~"healthcheckPath inexistente"~~ — `/api/v1/health/health` existe como alias deprecado ([health.py:67](../backend/app/presentation/api/v1/health.py)). Solo cleanup cosmético (A26).
3. ~~"errores de fetchSessions nunca se muestran"~~ — `ErrorOverlay` se renderiza en [App.tsx:133](../frontend/src/App.tsx) y muestra `errorStates`.
4. ~~"regenerar agente individual sin UI"~~ — el botón existe ([MessageBubble.tsx:423](../frontend/src/components/chat/MessageBubble.tsx)) y el commit 25e6a56 lo refinó.
5. ~~"tools disponibles en board mode"~~ — están deshabilitadas a propósito ([orchestrator.py:451-457](../backend/app/application/orchestrator.py), comentario explica el porqué: tool_calls colgantes rompen DeepSeek).
6. ~~"lock distribuido sin timeout"~~ — tiene `ttl_seconds=60` ([stream.py:576-577](../backend/app/presentation/api/v1/stream.py)), se auto-libera.
7. ~~"auth degrada silenciosamente a usuario fake en prod"~~ — al contrario: `_verify_token` lanza 503 si Firebase no está inicializado y `ENVIRONMENT=production` ([auth.py:64-75](../backend/app/core/auth.py)). El único hueco era el `init_firebase` que solo avisa → recogido en A11.

> **Reabiertos en Rev.2 tras feedback de Saúl** (ya NO son falsos positivos): #12 persistencia parcial → **A28** (confirmado, P1); #8 prompt injection → **A31**; #9 auth startup → **A11**; #10/#11 Stripe/billing → **A32/A33**; #14/#15 UX stream → **A29/A30**; #16-19 UX menores → **A34-A37**; micro-features de board → **B32**.

---

# PARTE B — ROADMAP DE MEJORAS (producto por el que pagar)

## Estado actual verificado (resumen)

- **Board:** secuencia fija CEO→CTO→CFO→CMO→conclusión del CEO, 1 iteración hardcodeada ([orchestrator.py:621](../backend/app/application/orchestrator.py) `BOARD_AGENTS_ORDER`), sin tools (deliberado), sin intervención del usuario a mitad de debate, coste 5 créditos. El debate no produce ningún artefacto exportable.
- **Agentes custom:** CRUD completo + wizard de 4 pasos + ~25 templates; validación correcta de modelo/temperatura/prompt ([agents.py:23-57](../backend/app/presentation/api/v1/agents.py)). Sin playground de prueba, sin fork, sin versionado; `is_public` existe en el schema pero no hay galería. No pueden unirse al board.
- **RAG:** PDF/DOCX/TXT/MD, 20MB para todos ([plan_limits.py:20-24](../backend/app/core/plan_limits.py)), chunks 512 tokens/64 overlap, top-k=3, dedup SHA256, vectores limpiados al borrar ✓. Sin citas estructuradas, sin preview, sin scope por conversación, sin hybrid search.
- **Integraciones:** 16 workflows n8n (Calendar×6, WhatsApp×3, LinkedIn, Instagram, Jules×3, finanzas×3), credenciales Fernet, circuit breaker + retry ✓, confirmación explícita para acciones destructivas ✓. Modelo "pega tu API key"; OAuth BYO solo GitHub/Notion/Slack. Sin catálogo visual ni logs de uso por integración.
- **Activación/negocio:** sin onboarding (usuario nuevo → interfaz vacía), **sin analytics de producto** (cero visibilidad de funnels), sin emails (ni bienvenida ni recibos), sin referidos, sin plan anual/equipos. Paywall modal existe pero con pocos triggers.

## B-P0 — Conversión y confianza (hacer ya, S/M)

| # | Mejora | Por qué alguien paga | Hooks | Esfuerzo |
|---|--------|---------------------|-------|----------|
| B1 | **Coste visible antes de enviar**: "Este mensaje: 1 crédito · Board: 5 créditos" junto al input, y aviso al activar board | La transparencia de coste es lo que hace tolerable un modelo de créditos; sin ella cada descuento parece un robo (ver bug A4) | `ChatPanel` input area + `BoardMeetingSettings` (modal de confirmación con coste) + `BOARD_MEETING_COST` expuesto en `/billing/me` | S |
| B2 | **Onboarding first-run**: checklist (crear agente → subir doc → probar board) + conversación de ejemplo pregrabada + empty states con CTA | Time-to-value: el usuario que no ve el "wow" en 5 min no vuelve; hoy aterriza en una pantalla vacía | `App.tsx` (flag `onboarding_completed` en user doc) + `OnboardingModal` nuevo + empty states en Sidebar/ChatPanel | M |
| B3 | **Analytics de producto (PostHog)**: eventos signup → primer chat → primer board → primer doc → primer pago | Sin funnel no sabes dónde se caen los testers ni qué feature retiene; cada decisión de roadmap es una apuesta a ciegas | SDK en `main.py` (backend events) + `api.ts`/`App.tsx` (front) — PostHog cloud free tier llega de sobra | M |
| B4 | **Upsell contextual**: aviso suave a <5 créditos, modal con packs al llegar a 0 a mitad de conversación, CTA tras un board exitoso ("Este debate costó 5 créditos — pack Executive = 150") | Los momentos de máximo valor percibido son los momentos de compra; hoy el usuario agotado solo ve "0 — Recargar" | `PaywallModal` ya existe — añadir triggers en `useBillingStore` (umbral) y en el handler 402 de `errorHandler.ts` | S |
| B5 | **Informe de síntesis del board exportable** (Markdown/PDF): perspectivas → desacuerdos → decisión → próximos pasos | Convierte el board de "chat curioso" en "herramienta de decisión": el artefacto se comparte con socios/jefes y vende el producto solo | `board_conclusion_node` (orchestrator.py) emite sección estructurada + botón export en `ChatPanel` (MD ya casi gratis; PDF con lib html-to-pdf) | M |
| B6 | **Feedback visible del test de credenciales** + estado por servicio | Conectar una integración es el momento de mayor fricción; un "✓ Conectado" verde reduce abandono | `ServiceCredentialsSettings.tsx` (el endpoint `/test` ya existe) | S |
| B7 | **Email transaccional mínimo**: bienvenida + recibo de compra | Un pago sin recibo por email parece una estafa; la bienvenida reactiva al 20-30% de registros que no vuelven el día 1 | Módulo `email_service.py` nuevo (Resend/SendGrid) + hook en signup y webhook Stripe | M |

## B-P1 — Diferenciación core (M/L)

### Board (tu moat — nadie más tiene un consejo de administración AI)
- **B8. Templates de debate**: "Valida mi idea de negocio", "Revisión de pricing", "¿Contrato o externalizo?" — un click rellena la query y el formato. Reduce el síndrome de página en blanco que hoy mata la activación del board. Hook: colección de templates + selector en ChatPanel al activar board. (M)
- **B9. Formatos de debate configurables**: nº de rondas (el state ya tiene `board_max_iterations`, hoy fijo a 1), modo "abogado del diablo", orden de intervención. Hook: `board_classifier_node` + UI en BoardMeetingSettings. (M)
- **B10. Dirigir el debate**: votar 👍/👎 cada intervención (infra de ratings ya existe) y que la conclusión del CEO pondere los votos; interrumpir con una aclaración entre agentes. Hook: `board_conclusion_node` lee ratings de la sesión. (M-L)
- **B11. Agentes custom en el board**: "contrata" a tu propio especialista para el consejo. Requiere generalizar `BOARD_AGENTS_ORDER` (orchestrator.py:621) a una lista por sesión + UI de selección de participantes. Es LA feature que une tus dos sistemas estrella. (L)

### Agentes custom
- **B12. Playground de prueba antes de guardar**: enviar 2-3 mensajes de prueba al agente desde el wizard (paso 2.5) sin crear sesión. Reduce el "¿habrá quedado bien el prompt?" que frena la creación. Hook: endpoint efímero de chat sin persistencia + modal. (M)
- **B13. Fork/duplicar agente** (endpoint + botón, S) e **import/export JSON** (S) — los power users iteran variantes.
- **B14. Personalidad por sliders** (asertividad/formalidad/creatividad → bloques de system_prompt). Diferencia la creación de "pegar un prompt" a "diseñar un empleado". Hook: `BrainConfig` + wizard. (S-M)
- **B15. Memoria por agente entre sesiones**: colección `agent_memories` (resumen de decisiones/preferencias del usuario inyectado al prompt). Es la feature de retención más fuerte: un agente que "te conoce" no se abandona. (L)

### RAG
- **B16. Citas clicables**: `retrieve_context` devuelve metadata estructurada (`source_file_id`, `chunk_index`) además del texto; el agente cita `[1]`, el frontend renderiza footnotes con popup del fragmento. La diferencia entre "me lo creo" y "no me lo creo". Hooks: `rag.py` (devolver dict en vez de string), `orchestrator.py` (instrucción de citado), `MessageBubble.tsx`. (M-L)
- **B17. Documentos por conversación**: `session.context_files` para elegir qué docs usa este chat. Hook: filtro extra en `retrieve_context` + picker en ChatSettingsPage. (M)
- **B18. Modo "solo mis documentos"**: el agente rehúsa responder fuera de la KB. Feature enterprise/compliance clásica de upsell. Hook: flag en BrainConfig + instrucción dura en prompt + validación. (M)
- **B19. Preview del documento** (modal con primeros chunks) + **re-indexar** (botón que reusa `process_document`). Complementa el fix A7. (S-M)
- **B20. Más fuentes de ingesta**: URLs (S — fetch+readability), CSV/XLSX (S), Google Drive/Notion sync (L). Cada formato nuevo amplía casos de uso pagables.

### Integraciones
- **B21. Catálogo visual de integraciones**: página con las 8+ integraciones, estado (conectada/error/sin configurar), último uso y último error. Hoy las integraciones están enterradas en settings y el usuario medio no descubre la feature más diferencial. Hook: página nueva + endpoint `/integrations/health` + colección `integration_usage_logs`. (M)
- **B22. OAuth real para Google Calendar** (en vez de pegar API key — fricción altísima para no-técnicos; la infra OAuth BYO ya existe para GitHub/Notion/Slack, falta el provider de Google). (M)
- **B23. Errores de tools visibles en el chat**: cuando un tool call falla, tarjeta con el motivo + botón reintentar (hoy solo lo explica el LLM en prosa). Hook: eventos `tool_result` con `is_error` + render en MessageBubble. (S-M)
- **B24. Conectores nuevos por demanda**: Gmail y Slack primero (los workflows n8n son baratos de añadir — patrón ya establecido con 16 ejemplos). (S por conector)

### Retención
- **B25. Tareas programadas de agentes**: "digest de mercado cada mañana a las 9" — scheduler (APScheduler) + colección `scheduled_tasks` + consumo de créditos pasivo. Engagement diario sin que el usuario abra la app… y quema créditos recurrente = ingresos recurrentes sin suscripción. (L)
- **B26. Referidos con créditos**: "invita y ganad 10 créditos cada uno". Growth barato para fase tester. (M)

### Board — refinamientos de producto (B32, reabierto Rev.2)
Sobre la base de B5/B8-B11, capas de profundidad que elevan el board de "demo impresionante" a "herramienta de la que dependes":
- **Disagreement scoring**: medir cuánto difieren las conclusiones de los 4 agentes (similitud semántica) y mostrar un medidor "consenso 60%". Señala al usuario dónde hace falta su criterio → percepción de rigor. Hook: post-`board_conclusion_node`.
- **Confidence por agente**: extraer el nivel de certeza del `reasoning_content` y mostrarlo en la burbuja.
- **Replay del debate**: reproducir el board a velocidad variable (los checkpoints ya están en Mongo) — útil para demos y para revisar decisiones.
- **Límite de tiempo/tokens del board**: tope configurable que corta un debate desbocado (protege saldo del usuario).
Esfuerzo conjunto: M-L. Priorizar disagreement scoring (el de mayor "wow" por línea de código).

## B-P2 — Apuestas grandes (3-6 meses)
- **B27. Marketplace de agentes públicos** (descubrir/fork/ratings — `is_public` ya está en el schema; falta galería, moderación y reputación).
- **B28. Workspaces de equipo** (sesiones/agentes compartidos, facturación por equipo — expande el TAM a agencias y consultoras).
- **B29. API pública + webhooks** (Zapier/Make; API keys por usuario).
- **B30. Hybrid search + reranking en RAG** (BM25+vector con rank fusion; gate premium de calidad de retrieval).
- **B31. PWA móvil** (manifest + service worker; el board por el móvil es un caso de uso natural).

---

# Orden de ataque sugerido (PRs)

> Regla: primero lo que **rompe confianza** (bugs de dinero/datos), después lo que **convierte** (valor visible + onboarding), después diferenciación.

| PR | Contenido | Por qué este orden |
|----|-----------|--------------------|
| **PR 1** | A1 (leak RAG) + A11 (secretos + Firebase startup) + A35 (versionar FERNET_KEY) | Los riesgos de seguridad/operativos reales; juntos ~120 líneas |
| **PR 2** | A3 + A12 (refunds robustos + lock antes de cobro) + A2 (webhook Stripe idempotente) | Todo el dinero del backend en un PR coherente con sus tests |
| **PR 3** | A4 + A5 + A6 + A8 + A28 (créditos UI, pins/ratings, limpieza de stores, retry de mensaje, persistencia parcial) | El frontend/persistencia dejan de "perder" datos y saldos |
| **PR 4** | A7 + B19-parcial (status failed con motivo + retry de documento) + A10 (timeout upload) | El RAG deja de tener callejones sin salida |
| **PR 5** | A13 (vitest funcionando + CI mínimo) | Red de seguridad antes de empezar con features |
| **PR 6** | B1 + B4 + B6 (coste visible, upsells, test de credenciales) + quick wins P2 | Primera tanda de conversión, todo S |
| **PR 7** | B2 + B3 (onboarding + PostHog) | Activación + empiezas a medir todo lo anterior |
| **PR 8** | B5 (síntesis de board exportable) → después B8/B9 (templates y formatos de debate) | Empieza la diferenciación del board con datos de uso reales en la mano |

---

*Generado por auditoría autónoma (Claude Code) el 2026-06-10. Todos los P0/P1 verificados línea a línea; las mejoras B# citan los hooks de código reales donde engancharían.*
