# SPHERE — QA en producción + diseño de frontera del Meeting Board
**Fecha:** 2026-06-11 · **Método:** Chrome headless (Puppeteer/CDP) contra `frontendsphere-production.up.railway.app` con cuenta QA real verificada (`claude.qa.sphere@example.com`, uid `TZOcIMgr1QRmVDLUA95TN5egklQ2`) + verificación de código + revisión del estado del arte en debate multi-agente.

---

## 1. Verificación del plan de auditoría (2026-06-10)

| Ítem | Estado |
|---|---|
| A1 Fuga RAG fallback sin `user_id` | ✅ Arreglado — fallback eliminado, fail-closed con log CRITICAL ([rag.py:137-153](../backend/app/application/rag.py#L137-L153)) |
| A2 Idempotencia webhook Stripe | ✅ Arreglado — lock por `_id` + índice único + dead-letter para metadata malformada |
| A3 Refunds tragados | ✅ Arreglado — `_safe_refund` + colección `pending_refunds` ([stream.py:31-65](../backend/app/presentation/api/v1/stream.py#L31-L65)) |
| A4 Pins/ratings sin `response.ok` | ✅ Arreglado ([api.ts:384-405](../frontend/src/services/api.ts#L384-L405)) |
| A5 Fuga de stores entre cuentas | ✅ Arreglado — `clearUserStores()` ([clearStores.ts](../frontend/src/lib/clearStores.ts)) |
| B "Regenerar agente del board" | ✅ Backend + frontend |
| B Coste visible antes de enviar | ❌ Pendiente |
| B Onboarding first-run | ❌ Pendiente (existe empty-state estático, sin checklist ni CTA de board) |
| B Analytics producto (PostHog) | ❌ Pendiente — sigues a ciegas en el funnel |
| B Upsell contextual | ⚠️ Parcial — PaywallModal solo salta en error 402/cuotas, sin trigger preventivo |
| B Storage RAG por tiers | ❌ Pendiente — 20 MB uniforme ([plan_limits.py:20-24](../backend/app/core/plan_limits.py#L20-L24)) |
| B Test-connection con feedback | ❌ Pendiente |

**Conclusión:** los 5 P0 de dinero/seguridad están cerrados y verificados. Todo el bloque de conversión sigue sin empezar.

---

## 2. QA real en producción (Chrome)

### 2.1 🔴 P0 NUEVO: el registro por email está roto en producción
- El formulario Email/Contraseña es el CTA principal de [LoginPage.tsx](../frontend/src/pages/LoginPage.tsx), pero el proveedor **Email/Password está deshabilitado en el proyecto Firebase** (`sphere-2a4cf`). La API devuelve `OPERATION_NOT_ALLOWED`; el usuario ve "Error de autenticación. Intenta de nuevo." y no hay nada que pueda hacer. **Todo registro/login por email falla hoy.** Solo Google/GitHub funcionan.
- Aunque se habilite el proveedor, hay un segundo muro: el backend deja con 0 créditos y bloquea `/stream` (403) a cuentas con email sin verificar ([auth.py:240-241](../backend/app/core/auth.py#L240-L241), [stream.py:469-476](../backend/app/presentation/api/v1/stream.py#L469-L476)), pero el frontend **nunca llama a `sendEmailVerification`** ni tiene pantalla/reenvío de verificación. Un registro por email quedaría muerto sin salida.
- **Fix recomendado (elige uno):**
  - *Rápido (30 min):* quitar el formulario email de LoginPage y dejar solo Google/GitHub ("Continúa con Google"). Cero mantenimiento, cero spam.
  - *Completo (medio día):* habilitar el proveedor en Firebase Console + `sendEmailVerification()` tras `signUpWithEmail` + pantalla "Revisa tu correo" con reenvío + recuperación de contraseña.

### 2.2 Lo que funciona bien (medido)
- **Rendimiento de carga excelente:** TTFB 211 ms, FCP/LCP 1,46 s, CLS ≈ 0,0004, transferencia inicial mínima, 0 long tasks relevantes. Hay margen de sobra para animaciones ricas.
- **Consola limpia** durante todo el flujo (solo un hint de `autocomplete`), **0 requests fallidas**.
- **Board E2E correcto:** `board_start` → CEO→CTO→CFO→CMO→síntesis → fin; cobro exacto de 5 créditos (30→25); burbujas por agente estilo WhatsApp; vista móvil correcta.
- La calidad del debate es razonable: los directores se leen entre sí, el CFO aporta números (LTV con churn 8%, umbral de retención 23%), el CEO cierra con decisión y próximos pasos.

### 2.3 Medición del board (el problema es la latencia, no la calidad)
Pregunta de negocio real, 2026-06-10 22:30 UTC:

| Turno | Inicio | Duración | Latencia 1er token |
|---|---|---|---|
| CEO apertura | 0 s | 12,3 s | 5,7 s |
| CTO | 12,3 s | 36,5 s | 11,2 s |
| CFO | 48,9 s | 65,4 s | **43,7 s** |
| CMO | 114,3 s | 38,2 s | 10,2 s |
| CEO síntesis | 152,5 s | 35,2 s | 14,0 s |
| **Total** | | **193 s** | |

Hallazgos derivados:
1. **43,7 s de aire muerto** en el turno del CFO con solo "Pensando…" genérico. No llegó **ni un evento `thinking`** en todo el debate (el `reasoning_content` de DeepSeek no está llegando en modo board, o el modelo no lo emite con estos prompts) — verificar [stream.py:248-264](../backend/app/presentation/api/v1/stream.py#L248-L264).
2. **Evento `board_agent CEO` duplicado al final** (202,4 s, turno de 0,2 s y 0 tokens): la excepción "conclusión siempre se emite" de [stream.py:184-216](../backend/app/presentation/api/v1/stream.py#L184-L216) dispara `on_chain_start` *y* el fallback de `on_chain_end`. En el store, como la burbuja activa ya tiene contenido, esto puede crear una burbuja vacía huérfana ([useChatStore.ts:657-676](../frontend/src/store/useChatStore.ts#L657-L676)). Fix: dedup por `node_name`+`run_id`, no por rol.
3. Usuario nuevo Free recibe **30 créditos** (`plan_messages_map["free"]`), no 50 — alinear cualquier copy/pricing que diga otra cosa. Un board = 5 créditos ⇒ **6 debates gratis**.
4. Sin indicador de progreso de la reunión: el usuario no sabe cuántos turnos faltan ni cuánto tardará (3+ min sin expectativa = abandono).

---

## 3. Estado del arte en debate multi-agente → qué adoptar

Lo relevante de la literatura 2023-2026, filtrado por aplicabilidad a SPHERE:

- **El debate no mejora por defecto.** MAD homogéneo y sin estructura no supera de forma consistente a un solo agente con self-correction; la sycophancy colapsa el debate en consenso prematuro ([Talk Isn't Always Cheap](https://arxiv.org/pdf/2509.05396), [The Cost of Consensus](https://arxiv.org/html/2605.00914v1), [Peacemaker or Troublemaker](https://arxiv.org/html/2509.23055v1)). Lo que SÍ aporta valor medible: **roles heterogéneos, disenso estructurado y un juez/síntesis separado** — exactamente la dirección correcta del board de SPHERE.
- **Heterogeneidad gana:** roles distintos + un agente "devil's advocate" mejora la factualidad (single 60% → MAD 74% → A-HMAD heterogéneo 80,6% en [A-HMAD, Springer 2025](https://link.springer.com/article/10.1007/s44443-025-00353-3)); mezclar modelos distintos sube GSM-8K de 82%→91% ([Demystifying MAD: Confidence & Diversity](https://arxiv.org/pdf/2601.19921)).
- **Topología dispersa = -40% tokens sin perder calidad:** no hace falta que todos lean todo en cada ronda ([Sparse Communication Topology](https://arxiv.org/html/2406.11776v1), [DySCo](https://arxiv.org/html/2606.01828)).
- **Parada adaptativa:** detectar estabilidad/consenso y cortar rondas sobrantes ahorra coste sin perder precisión ([Adaptive Stability Detection](https://arxiv.org/html/2510.12697v1)).
- **Señales de fiabilidad:** alta varianza de opiniones y cambios de postura correlacionan con respuestas incorrectas — útil para mostrar "confianza de la junta" y para decidir rondas extra ([Can LLM Agents Really Debate?](https://arxiv.org/pdf/2511.07784)).
- **UX de productos comparables** (MIT Sloan "[Personal Board of Directors with GenAI](https://sloanreview.mit.edu/article/how-i-built-a-personal-board-of-directors-with-genai/)", AI Boardroom): seleccionan 2-4 miembros relevantes por pregunta (no siempre todos) y entregan **secciones por miembro + consenso + action items** como artefacto.

---

## 4. Rediseño de frontera del Meeting Board

Hoy el board es un *pipeline de informes* (1 iteración forzada, [orchestrator.py:726](../backend/app/application/orchestrator.py#L726)): nadie rebate a nadie. Y es secuencial puro con modelo reasoning en los 5 turnos. El rediseño ataca latencia, coste, calidad de decisión y espectáculo a la vez:

### 4.1 Arquitectura del debate (backend)
1. **Triage previo con `v4-flash` (1 llamada barata):** clasifica la consulta → qué directores aportan (2-4), cuántas rondas, y si amerita devil's advocate. Pregunta simple = 2 directores = 3 créditos; full board solo cuando aporta. Base: sparse topology + routing dinámico. *Gancho:* `board_classifier_node` ya existe; hoy es un stub que fuerza 1 iteración.
2. **Ronda 1 en paralelo:** CEO abre (igual que hoy) → CTO/CFO/CMO generan **simultáneamente** (cada uno lee solo apertura + pregunta; en LangGraph: fan-out desde `ceo_board` y `asyncio.gather` de los tres nodos). Tiempo estimado: `12s + max(turno) ≈ 78s` en vez de 152s hasta la síntesis. La UI gana el efecto "war room": tres burbujas creciendo a la vez.
3. **Ronda 2 de réplicas (el debate real, lo que hoy NO existe):** cada director lee a los otros dos y responde SOLO disensos/ajustes con tope de tokens (réplicas cortas). Prompt anti-sycophancy explícito: "tu valor está en lo que los demás no vieron; si no tienes disenso real, di 'sin objeciones' en una línea" — esto habilita early-exit.
4. **Voto estructurado + early-exit:** cada director cierra su réplica con `DECISIÓN: SÍ/NO/CONDICIONAL + confianza 0-100` (JSON al final del mensaje, parseable). Consenso unánime y estable → se salta lo que quede y va a síntesis (adaptive stopping); alta varianza → el CEO puede pedir UNA ronda extra automática. La UI muestra "La junta votó 3-1".
5. **Devil's Advocate como 5º asiento opcional** (toggle "modo estrés" en settings del grupo, candidato a feature premium): su único trabajo es atacar la opción ganadora antes de la síntesis. Es la intervención con mejor evidencia coste/beneficio de la literatura.
6. **Mezcla de modelos:** directores ronda 1 con `v4-flash` o reasoning con límite, síntesis del CEO siempre `v4-pro`. Baja latencia y coste, y la heterogeneidad de modelos tiene evidencia de mejora de calidad. Mientras tanto, arreglar que `reasoning_content` llegue al frontend en board (hoy 0 eventos `thinking`).
7. **Acta de la Junta como artefacto:** la síntesis del CEO se emite envuelta en `<sphere_artifact>` (¡el pipeline de artifacts ya existe y funciona!) → panel lateral con "Acta: decisión, votos, riesgos, próximos pasos, responsable" + export MD/PDF. Esto convierte el board de chat curioso a **herramienta de decisión que se comparte** (= growth orgánico).
8. **Usuario en el loop:** botón "Intervenir" entre turnos (LangGraph `interrupt` + resume con `HumanMessage`; el checkpointer ya está) y "Preguntar a Ledger" sobre el acta a 1 crédito (no 5). El follow-up barato es el upsell natural del board.
9. **Agentes custom en la mesa:** sustituir `BOARD_AGENTS_ORDER` hardcodeado ([orchestrator.py:621](../backend/app/application/orchestrator.py#L621)) por los `members` de la sesión (el frontend ya gestiona miembros del grupo). Tu abogada custom + CFO core debatiendo tu contrato = momento "esto no lo hace ChatGPT".

### 4.2 Orden de implementación sugerido del board
| PR | Qué | Esfuerzo | Impacto |
|---|---|---|---|
| 1 | Indicador de progreso de turnos + "X está analizando…" por rol + fix evento duplicado + fix `thinking` en board | S | Percepción de velocidad inmediata |
| 2 | Acta artefacto + export MD | M | Retención/compartibilidad |
| 3 | Ronda 1 paralela + réplicas con tope + voto/early-exit | M/L | Latencia −50%, debate real |
| 4 | Triage de participantes + cobro dinámico 3/5 créditos | M | Coste honesto, más debates por wallet |
| 5 | Devil's advocate + intervención del usuario | M | Diferenciación premium |
| 6 | Custom agents en el board | M | Moat de producto |

---

## 5. Fricción de nuevos usuarios (orden de ataque)

1. **🔴 Arreglar el login email** (§2.1) — hoy pierde a *todos* los que no quieren OAuth.
2. **El board está escondido:** es el servicio estrella y nace apagado tras un toggle en Configuración. El propio selector dice "Activa Board Meeting en Configuración…" — fricción máxima en el punto de máxima intención. Fix S: al crear una Junta Directiva por primera vez, modal de 1 clic: "¿Quieres que debatan entre sí? Cuesta 5 ⚡ por sesión (tienes 30)" → activa `board_meeting_enabled` ahí mismo. Sin viaje a settings.
3. **Coste visible antes de enviar:** chip "⚡5" junto al botón de enviar en sesiones board (y "⚡1" en directas). El [CreditsIndicator](../frontend/src/components/CreditsIndicator.tsx) ya muestra saldo; falta el coste de la acción.
4. **Demo sin coste:** una "junta de muestra" pre-grabada (replay con efecto typewriter de un debate real bueno) como primer ítem del historial para cuentas nuevas — vende el wow sin gastar créditos ni API, y enseña el formato del acta. Esfuerzo S/M, cero coste marginal.
5. **Checklist first-run de 3 pasos** (Convoca tu junta → Lanza tu primer debate → Crea tu experto custom) sobre el empty-state actual, con `onboarding_completed` que ya existe en el modelo de usuario ([api.ts:431](../frontend/src/services/api.ts#L431)) y nunca se usa.
6. **PostHog** (signup → primera junta → primer debate → paywall → pago): sin esto, todo lo anterior es fe. 1-2 h de integración.
7. Copy: unificar ES (hay "Transmite tu consulta…" junto a "FREQ: 771MHZ" y mensajes EN); explicar los 30 créditos del Free en el primer paywall y en billing.

---

## 6. Visual: efecto "IA de frontera"

La base (Midnight Protocol + aurora blobs + framer-motion) es sólida y la carga es rapidísima (LCP 1,4 s) — hay presupuesto de rendimiento para subir el nivel. Propuestas en orden de wow/esfuerzo (todas con `prefers-reduced-motion`):

1. **Cabecera "sala de juntas" durante el debate:** los 4 avatares en fila con estado vivo — anillo pulsante del color del agente que habla (`agent_ceo #8A63D2`, etc.), dimmed los que esperan, check al terminar. Con la ronda paralela, varios anillos laten a la vez (efecto enjambre). Es EL plano que la gente grabará en demos.
2. **Aurora reactiva:** [AuroraBackground](../frontend/src/components/AuroraBackground.tsx) ya anima 3 blobs; modular color/intensidad según el agente activo (el blob "se inclina" hacia el color de quien habla). Cambio de ~20 líneas, efecto ambiental enorme.
3. **Razonamiento como actividad neuronal:** cuando llegue `thinking` real, render con shimmer de gradiente animado sobre el texto (en vez del bloque itálico plano) + línea de estado específica por rol ("Ledger está modelando el cash-flow…"). Mata los 40 s de aire muerto.
4. **Reveal del acta:** la síntesis aparece como carta con borde `conic-gradient` rotando + contador de votos animado (3-1) + micro-partículas cyan en el momento de la decisión. Un solo momento de fuegos artificiales, donde importa.
5. **Stagger de entrada de burbujas** (spring suave, 40 ms entre elementos) y sustituir el decorado sin significado ("FREQ: 771MHZ") por chips con dato real: voto y confianza del director — mismo look sci-fi, ahora con información.
6. **First-run "constelación":** los 4 nodos orbitando una esfera que se conectan con líneas al hover, CTA "Convoca tu primera junta". Reemplaza las 4 cards estáticas actuales.

---

## 7. Artefactos de la sesión de QA
- Screenshots y logs: `%TEMP%\sphere-chrome\artifacts2\` (flujo completo, timing-analysis.txt, stream-log.json, console.json)
- Scripts reutilizables: `%TEMP%\sphere-chrome\qa1.js` (signup/perf), `qa2.js` (board E2E autenticado), `create-test-user.js` (usuario QA verificado vía Admin SDK)
- Cuenta QA creada: `claude.qa.sphere@example.com` (borrable desde Firebase Console cuando quieras)
- Plugin `chrome-devtools-mcp` instalado (scope user) — disponible al reiniciar Claude Code
