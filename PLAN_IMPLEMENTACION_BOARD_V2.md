# Plan de implementación — Board V2 "frontera" + war-room UI + bugs + onboarding

> **Entregable inmediato tras aprobar:** guardar este plan como `PLAN_IMPLEMENTACION_BOARD_V2.md` en la **raíz del repo** (petición explícita del usuario). La implementación de código se hará después, siguiendo el paso a paso, en el orden de fases indicado.

## Contexto

QA real en producción (2026-06-11, `docs/BOARD_FRONTERA_Y_QA_2026-06-11.md`) midió el board actual: **193 s**, secuencial CEO→CTO→CFO→CMO→síntesis, 43,7 s de primer token en CFO, 0 eventos `thinking`, evento de conclusión duplicado, y sin debate real (1 iteración forzada: nadie rebate a nadie). Además: el board nace apagado tras un toggle en Configuración, el registro email/password está roto en producción (proveedor Firebase deshabilitado + sin flujo de verificación), y hay copy desalineado (Free = 30 créditos, no 50).

El SOTA en multi-agent debate (citas en el doc de QA) respalda: rondas paralelas con topología dispersa (−40 % tokens), réplicas con disenso explícito (anti-sycophancy), voto estructurado + early-exit por consenso, devil's advocate (mejor evidencia coste/beneficio), y síntesis por juez separado.

**Alcance aprobado por el usuario:**
1. Board V2: triage flash → CEO abre → ronda paralela CTO/CFO/CMO → réplicas cortas con voto + early-exit → devil's advocate opcional → síntesis como acta-artefacto exportable → intervención del usuario mid-debate.
2. SSE: eventos nuevos + tokens etiquetados por rol (streaming paralelo).
3. Frontend war-room: burbujas simultáneas, cabecera "en sesión", chips de voto (sustituyen `FREQ: XXXMHz`), modal de activación con coste ("5 ⚡ de tus 30"), aurora reactiva, export del acta, reveal animado.
4. Bugs: evento conclusión duplicado, login email (proveedor + verificación), copy 30 créditos, `thinking` ausente en board.
5. Onboarding first-run (checklist 3 pasos sobre el Welcome Screen existente).

**Excluido explícitamente:** analytics/PostHog, tiers RAG, feedback de test-connection.

## Decisiones de arquitectura (con el porqué)

- **Mantener LangGraph para el board** (no motor imperativo): el historial se reconstruye desde el checkpoint (`orchestrator_app.aget_state` en [sessions.py:284-286](backend/app/presentation/api/v1/sessions.py#L284-L286)) y la regeneración depende de `board_agents_done` persistido. Un motor imperativo rompería ambos. LangGraph soporta fan-out paralelo (conditional edge que devuelve lista de nodos) y `astream_events` expone `metadata.langgraph_node` para etiquetar tokens por rol.
- **Reducer custom para `board_agents_done`**: hoy es `list[str]` sin reducer ([orchestrator.py:71-73](backend/app/application/orchestrator.py#L71-L73)); escrituras paralelas colisionarían. Se cambia a `Annotated[list[str], _done_reducer]` donde el reducer concatena, y un valor sentinel `["__RESET__"]` vacía la lista (necesario porque el checkpoint persiste entre debates de la misma sesión y con un reducer puro no se puede resetear).
- **Cobro 5 → refund parcial 2**: el cobro ocurre antes del grafo ([stream.py:600-621](backend/app/presentation/api/v1/stream.py#L600-L621)). El triage corre dentro del grafo; si reduce a ≤2 directores, stream.py emite `board_plan` y ejecuta un **refund parcial** nuevo (`CreditManager.partial_refund`). El pre-check sigue exigiendo 5 (limitación v1 documentada).
- **Feature flag de rollout**: `BOARD_V2_ENABLED` (env, default `true` en dev / decidir en prod). El grafo viejo queda compilado como fallback (`board_workflow_legacy`) y `stream.py` elige por flag. Rollback = flip de env var en Railway.
- **Intervención sin romper SSE**: no se pausa el stream; se encola en Mongo (`board_interventions`) vía endpoint nuevo y el grafo la inyecta como `HumanMessage` en los puntos de sincronización (antes de réplicas y antes de síntesis).

## Protocolo SSE V2 (contrato backend↔frontend)

| Evento | Campos | Cuándo |
|---|---|---|
| `token` | `content`, **`role`** (nuevo, solo board) | streaming de cada agente (paralelo) |
| `thinking` | `content`, `role` | ya existe; debe funcionar en board |
| `board_start` | `agents`, `iterations` | sin cambios |
| `board_plan` *(nuevo)* | `participants: string[]`, `cost: 3\|5`, `reason` | tras triage |
| `board_phase` *(nuevo)* | `phase: opening\|analysis\|rebuttal\|devil\|synthesis` | al entrar en cada fase |
| `board_agent` | `role`, `is_conclusion`, **`phase`** (nuevo) | al abrir burbuja de un agente (pueden llegar 3 seguidos al iniciar fase paralela) |
| `board_vote` *(nuevo)* | `role`, `vote: SI\|NO\|CONDICIONAL`, `confidence: 0-100` | al parsear el voto de cada director |
| `board_consensus` *(nuevo)* | `unanimous: bool`, `tally: {SI,NO,CONDICIONAL}`, `early_exit: bool` | tras cada ronda |
| `board_intervention` *(nuevo)* | `text` | cuando el grafo inyecta una intervención |
| resto (`artifact_*`, `tool_*`, `meta`, `error`, `[DONE]`) | sin cambios | |

---

## FASE 1 — Backend: grafo Board V2 (`orchestrator.py` + módulo nuevo `app/application/board_v2.py`)

Para no inflar `orchestrator.py` (~1100 líneas), los nodos nuevos viven en `board_v2.py` e importan `agent_node`, prompts y `AgentState` desde orchestrator.

1.1. **AgentState**: añadir campos `board_participants: Optional[list[str]]`, `board_votes: Annotated[dict, _votes_reducer]` (merge de dicts; sentinel reset igual que agents_done), `board_phase: str`, `board_devil: bool`; cambiar `board_agents_done` a `Annotated[list[str], _done_reducer]`. Definir ambos reducers arriba del TypedDict.

1.2. **Nodo `triage`** (reemplaza a `board_classifier_node` en V2): 1 llamada a `llm_router` (`DEEPSEEK_FAST = deepseek-v4-flash`, [llm_models.py:17](backend/app/core/llm_models.py#L17)) con prompt que devuelve JSON `{"participants": ["CTO","CFO"], "reason": "..."}` (siempre ≥2 directores de CTO/CFO/CMO; CEO siempre abre y cierra). Parse defensivo: si falla el JSON → full board. En `regenerate=True`: skip triage, leer `board_participants` del checkpoint. Devuelve también `board_agents_done: ["__RESET__"]` y `board_votes: reset`.

1.3. **Nodo `ceo_open`**: el actual `board_agent_node_factory("CEO")` con `BOARD_CEO_OPENER`, ajustando el prompt para delegar SOLO a los participantes del triage.

1.4. **Fan-out paralelo de análisis**: `add_conditional_edges("ceo_open", route_analysis, [...])` donde `route_analysis` devuelve la **lista** `[f"{r.lower()}_analysis" for r in participants]` → LangGraph ejecuta los nodos en el mismo superstep (paralelo real). Cada nodo es `board_agent_node_factory(role, phase="analysis")` con prompt actualizado: ronda 1 lee SOLO apertura del CEO + pregunta (topología dispersa — los directores NO se leen entre sí en esta ronda; el prompt deja de decir "el CTO ya habló"), y **termina obligatoriamente con la línea de voto**: `[VOTO] decision=SI|NO|CONDICIONAL confianza=NN`.

1.5. **Post-proceso de voto en el nodo**: regex `\[VOTO\]\s*decision=(SI|NO|CONDICIONAL)\s*confianza=(\d{1,3})` sobre `response.content`; *strip* de la línea del content, guardar en `response.additional_kwargs["board_vote"]={vote,confidence}` (así sobrevive en historial) y devolver `board_votes: {role: {...}}`.

1.6. **Nodo `consensus_gate`** (join tras análisis): calcula tally; si unánime con confianza media ≥70 → `early_exit=True` y salta réplicas. Inyecta intervención pendiente si existe (lee `board_interventions` por `user_id:session_id`, marca consumida, añade `HumanMessage("[INTERVENCIÓN DEL FUNDADOR] …")`). Las salidas: `rebuttal` (lista paralela de `{role}_rebuttal` solo de participantes) o directo a `devil`/`synthesis`.

1.7. **Nodos `{role}_rebuttal`**: mismo factory con `phase="rebuttal"`; prompt: lee los análisis de los demás, responde SOLO disensos/ajustes en ≤150 palabras, "sin objeciones" permitido, re-vota con la misma línea `[VOTO]` (puede cambiar). Anti-sycophancy explícito: "tu valor está en lo que los demás no vieron".

1.8. **Nodo `devil`** (condicional por `board_devil`): persona fija Devil's Advocate (rol `DEVIL`, sin RAG propio — `effective_role` mapeado a prompt inline), ataca la opción ganadora del tally en ≤200 palabras. Se añade a `BOARD_NODE_ROLES` como `"devil": "DEVIL"`.

1.9. **Nodo `synthesis`**: el actual `board_conclusion_node` con prompt extendido: emite el **acta dentro de `<sphere_artifact type="markdown" title="Acta de la Junta — {fecha}">`** con secciones fijas (Contexto y pregunta / Votación con tabla de votos+confianza / Decisión ejecutiva / Riesgos / Próximos pasos con dueño) + 2-3 líneas de resumen FUERA del artefacto para el chat. El pipeline de artifacts ya parsea el tag ([stream.py:76, 326-365](backend/app/presentation/api/v1/stream.py#L76)). Antes de sintetizar: segunda ventana de intervención (mismo mecanismo que 1.6).

1.10. **Compilar `board_workflow_v2`** con el mismo `MongoDBSaver` ([orchestrator.py:1038-1061](backend/app/application/orchestrator.py#L1038-L1061)); mantener el grafo viejo como `board_app_legacy`. Lazy proxy igual que el existente.

1.11. **Regeneración V2**: `regenerate=True` → triage lee participantes del checkpoint; los nodos de análisis/réplica se saltan por membership en `board_agents_done` (igual que hoy, [orchestrator.py:766-777](backend/app/application/orchestrator.py#L766-L777)); síntesis se re-ejecuta siempre.

## FASE 2 — Backend: stream.py, créditos, intervención, settings

2.1. **Tokens con rol**: en `on_chat_model_stream`, leer `event["metadata"].get("langgraph_node")` → mapear con `BOARD_NODE_ROLES_V2` (`cto_analysis`→CTO, `cto_rebuttal`→CTO, `devil`→DEVIL, `synthesis`→CEO…) → emitir `{'type':'token','content':…,'role':…}` solo en board_mode. Mismo mapeo para `thinking`.

2.2. **Fix evento duplicado de conclusión**: dedup por **node_name** con un `set` de nodos ya anunciados (no por rol), y eliminar la excepción "conclusión siempre se emite" del fallback `on_chain_end` ([stream.py:184-216](backend/app/presentation/api/v1/stream.py#L184-L216)). `board_agent` se emite una sola vez por nodo, con `phase`.

2.3. **Eventos nuevos**: `board_plan` (al cerrar el nodo triage, leyendo su output en `on_chain_end`), `board_phase`, `board_vote` (al cerrar cada nodo director, leyendo `board_votes` del output), `board_consensus` (al cerrar `consensus_gate`), `board_intervention`.

2.4. **`CreditManager.partial_refund(ctx, amount, reason)`**: como `refund()` ([credit_manager.py:144-163](backend/app/application/credit_manager.py#L144-L163)) pero con `$inc` de `amount` y transacción `delta=+amount, reason="board_triage_reduced"`. En stream.py: si `board_plan.cost==3` → `partial_refund(ctx, 2)`. Añadir constante `BOARD_REDUCED_COST = 3` junto a `BOARD_MEETING_COST` ([credit_manager.py:38](backend/app/application/credit_manager.py#L38)).

2.5. **Endpoint `POST /stream/intervene`** (stream.py router): body `{session_id, text (≤1000)}`; valida owner (`require_owner`) y que exista lock activo `lock:checkpoint:{user}:{session}` en Redis (si no hay debate en curso → 409); inserta `{user_id, session_id, text, consumed:false, created_at}` en `board_interventions` (índice TTL 10 min). Sin coste de créditos.

2.6. **Board settings**: añadir `board_devils_advocate: bool=False` a `BoardSettingsResponse` y al PATCH ([auth.py:608-669](backend/app/core/auth.py#L608-L669) según explorador — verificar archivo exacto al implementar); `stream.py` lo lee junto a `board_meeting_enabled` ([stream.py:517-529](backend/app/presentation/api/v1/stream.py#L517-L529)) y lo pasa como `board_devil` al estado inicial.

2.7. **`thinking` en board**: causa probable: `langchain-openai` descarta `delta.reasoning_content` de la API DeepSeek. Paso 1: log de diagnóstico de `chunk.additional_kwargs` en dev. Paso 2: migrar `llm_expert`/factory a `ChatDeepSeek` (`langchain-deepseek`, ya soporta `reasoning_content` en streaming) manteniendo la interfaz; si el paquete no entra limpio, fallback documentado: status sintético por rol en frontend (4.6) y se cierra como limitación.

2.8. **Bug menor preexistente**: el ajuste post-stream usa pricing hardcodeado `0.27/1.10` ([stream.py:398](backend/app/presentation/api/v1/stream.py#L398)) → usar `pricing_for(DEEPSEEK_REASONING)`.

## FASE 3 — Frontend: protocolo y store

3.1. **api.ts** (`StreamCallbacks`, [api.ts:37-55](frontend/src/services/api.ts#L37-L55)): `onToken(content, role?)`; nuevos `onBoardPlan`, `onBoardPhase`, `onBoardVote`, `onBoardConsensus`, `onBoardIntervention`. Parseo de los eventos nuevos en el switch ([api.ts:115-184](frontend/src/services/api.ts#L115-L184)). Nuevo `api.intervene(sessionId, text)`.

3.2. **useChatStore.sendMessage**: sustituir el `activeBotMsgId` único por `bubbleByRole: Record<string,string>` durante board. `onBoardAgent` crea/etiqueta burbuja del rol (la lógica actual de "reetiquetar si vacía" se conserva para el primer agente, [useChatStore.ts:635-680](frontend/src/store/useChatStore.ts#L635-L680)); `onToken(content, role)` enruta a `bubbleByRole[role]` (fallback: burbuja activa para modo normal). `onThinking` igual con rol. Guardar en el mensaje: `vote?: {decision, confidence}`, `phase?`, vía `onBoardVote`.

3.3. **Estado de sesión del debate** (para la cabecera war-room): slice `boardSession: {phase, participants, statusByRole: idle|thinking|speaking|done, votes, tally, earlyExit, cost}` alimentado por los eventos; se limpia en `[DONE]`.

3.4. **Historial**: al recargar sesión, derivar chips de voto desde `additional_kwargs.board_vote` de los AIMessages (sessions.py ya devuelve los mensajes crudos; verificar cómo el parser de historial del store mapea `additional_kwargs`, [useChatStore.ts:366-398](frontend/src/store/useChatStore.ts#L366-L398) zona de parsing).

3.5. **Tipos**: `Role` += `'DEVIL'`; agente visual DEVIL en MOCK_AGENTS (avatar ⚔️, hexColor `#FF4D6D`).

## FASE 4 — Frontend: war-room UI y visual

4.1. **`BoardWarRoom.tsx`** (nuevo, cabecera bajo el header del chat, solo cuando `boardSession` activo): fila de avatares de `getGroupMembers` + DEVIL si aplica; estados: dimmed (idle), anillo pulsante del color del agente (`speaking` — framer-motion `animate={{scale,boxShadow}}`), shimmer (thinking), check + chip de voto (done). Barra de fases: Apertura ▸ Análisis ▸ Réplicas ▸ Síntesis con la fase activa iluminada. Texto "La junta votó 3-1" cuando llegue `board_consensus`.

4.2. **Chips de voto en MessageBubble**: sustituir `FREQ: XXXMHz` ([MessageBubble.tsx:456-459](frontend/src/components/chat/MessageBubble.tsx#L456-L459)) por chip `✓ SÍ · 85%` / `✗ NO` / `~ COND` con el color del agente cuando `message.vote` exista; si no, sin chip (adiós decoración aleatoria).

4.3. **Modal de activación** (`BoardActivationModal.tsx`): en `handleSelectAgent` del AgentSelectorModal ([AgentSelectorModal.tsx:60-70](frontend/src/components/modals/AgentSelectorModal.tsx#L60-L70)), si `agentId==='group-chat'` y `board_meeting_enabled===false` (GET ya existente) → modal: "¿Activar el debate de la junta? Cada sesión de debate cuesta **5 ⚡** (tienes **{pro+topup}**). Preguntas simples pueden costar 3 ⚡." Botones: "Activar debate" (PATCH + crear sesión) / "Solo router" (crear sesión sin activar). Persistir elección.

4.4. **Chip de coste junto a Send** ([ChatPanel.tsx:537-549](frontend/src/components/chat/ChatPanel.tsx#L537-L549)): `⚡5` en sesión grupal con board on, `⚡1` resto; tooltip explicativo.

4.5. **Botón/modo "Intervenir"**: durante board streaming, el input deja de estar bloqueado: placeholder "Intervenir en el debate…", botón Send → `api.intervene` (sin coste); banner pequeño "Tu intervención entrará antes de la siguiente fase". Echo visual al llegar `board_intervention`.

4.6. **Status por rol mientras piensa**: en vez del "Pensando…" genérico ([MessageBubble.tsx:52-63](frontend/src/components/chat/MessageBubble.tsx#L52-L63)), mensaje por rol+fase ("Ledger está modelando los números…", "Vortex prepara su réplica…") — tabla estática rol→frases.

4.7. **Aurora reactiva**: `AuroraBackground` acepta `accentColor` (color del agente hablando, desde `boardSession`); el blob principal interpola color/escala con framer-motion. Respetar `prefers-reduced-motion`.

4.8. **Reveal del acta**: cuando llega `artifact_open` con título "Acta…": borde `conic-gradient` animado en el ArtifactCard, contador de votos animado (count-up) y micro-partículas cyan one-shot. El Download ya existe en ArtifactCard; añadir botón "Exportar acta (.md)" también en la cabecera war-room al terminar.

## FASE 5 — Bugs login email + copy

5.1. **Habilitar proveedor Email/Password**: intentar por API Admin (`PATCH https://identitytoolkit.googleapis.com/admin/v2/projects/sphere-2a4cf/config` con token OAuth del service account local `backend/firebase-adminsdk.json`, body `{"signIn":{"email":{"enabled":true,"passwordRequired":true}}}`). Si la cuenta de servicio no tiene permiso → fallback: instrucción manual de 1 clic en Firebase Console (documentada en el PR) y mientras tanto **ocultar el form email** tras flag `VITE_EMAIL_AUTH_ENABLED`.

5.2. **Flujo de verificación**: en `AuthContext.signUpWithEmail` → `sendEmailVerification(user)` tras crear; nueva `VerifyEmailPage` (ruta `/verify-email`): "Revisa tu correo", botón reenviar (cooldown 60 s), botón "Ya verifiqué" → `user.reload()` + redirect. `RequireAuth`: si `user && !user.emailVerified && providerId==='password'` → redirect a `/verify-email`. Backend: en `get_current_user`/auto-provision, si doc tiene `subscription.status=="email_unverified"` pero el claim `email_verified==true` → upgrade a `active` + grant de los 30 créditos (hook en [auth.py:218-241](backend/app/core/auth.py#L218-L241)).

5.3. **Copy 30 créditos**: grep `50` en BillingPage/PaywallModal/landing copy → alinear a 30 (`plan_messages_map["free"]=30`, [config.py:107-114](backend/app/core/config.py#L107-L114)). El modal de activación (4.3) ya muestra el saldo real.

## FASE 6 — Onboarding first-run (aprobado)

6.1. **Checklist de 3 pasos** sobre el Welcome Screen existente ([ChatPanel.tsx:234-304](frontend/src/components/chat/ChatPanel.tsx#L234-L304)): "1) Convoca tu Junta Directiva → 2) Lanza tu primer debate → 3) Crea tu experto custom". Progreso derivado de datos reales (sessions de tipo grupo >0, mensajes >0, customAgents >0) — sin estado nuevo en backend. Al completar los 3 → `completeOnboarding()` ([api.ts:538](frontend/src/services/api.ts#L538), endpoint ya existe) y el checklist no vuelve a salir (`onboarding_completed` del perfil). CTA del paso 1 abre el AgentSelectorModal directamente.

## FASE 7 — Tests y verificación

- **Backend** (`pytest backend/tests`): actualizar `test_board_meeting.py` (routing nuevo: triage→fan-out→gate→síntesis; reducers reset/append; parser de votos con casos borde: sin línea, confianza >100, decision inválida); nuevo `test_board_v2_engine.py` (early-exit unánime, devil condicional, intervención inyectada 1 sola vez); `test_credit_manager.py` + `partial_refund`; `test_stream_billing.py` sigue verde (already_charged no cambia).
- **Frontend** (`npm test` / vitest): store — routing de `onToken` por rol a burbujas paralelas; chips de voto desde `board_vote`; `tests/store/streaming.test.ts` extendido con secuencia board V2 completa simulada.
- **E2E real**: re-ejecutar `%TEMP%\sphere-chrome\qa2.js` (ya parsea `board_*`; añadir los eventos nuevos al tee) contra prod tras deploy → comparar: latencia total objetivo <100 s, sin evento duplicado, votos visibles, acta descargable, cobro 5→refund 2 en pregunta simple (wallet verificable vía /me).
- **Smoke manual**: regenerar conclusión (compatibilidad regenerate), sesión vieja pre-V2 (historial carga), board con flag V2 off (fallback legacy).

## Orden de PRs sugerido

1. PR-1 (backend core): Fases 1 + 2 tras flag `BOARD_V2_ENABLED` + tests. *Sin tocar frontend: V1 sigue funcionando.*
2. PR-2 (frontend protocolo+war-room): Fases 3 + 4. Tolerante a backend V1 (eventos nuevos opcionales).
3. PR-3 (login email + copy): Fase 5.
4. PR-4 (onboarding): Fase 6.
5. Deploy Railway → QA E2E (Fase 7) → si KO, flag off.

## Riesgos conocidos

- Fan-out paralelo triplica llamadas concurrentes a DeepSeek por usuario → vigilar rate limits del proveedor; mitigación: `max_concurrency` en config del grafo si hace falta.
- `add_messages` con escrituras paralelas ordena los AIMessages de análisis de forma no determinista → el orden visual lo fija el frontend por burbujas (no por orden de llegada), y la síntesis no depende del orden.
- Sesiones board antiguas + grafo nuevo comparten checkpointer: el sentinel `__RESET__` debe ejecutarse en triage SIEMPRE para limpiar `board_agents_done` heredado.
- `ChatDeepSeek` (thinking) puede traer cambios de comportamiento en tool-calls del modo normal → migrar SOLO los LLM del board en este plan.
