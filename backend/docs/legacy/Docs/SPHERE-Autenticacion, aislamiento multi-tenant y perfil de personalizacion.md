Ready for review
Select text to add comments on the plan
SPHERE — Autenticación, aislamiento multi-tenant y perfil de personalización
Context
Hoy SPHERE es un sistema single-tenant: todas las sesiones, agentes, documentos y credenciales están hardcodeados a user_id = "default_user". Para llevarlo a producción multi-usuario necesitamos cuatro capas que hoy no existen o son inseguras:

Auth de la app: quién es el usuario que habla con SPHERE.
Credentials store por usuario: cuando el CTO crea un repo, el CMO publica en LinkedIn, o el CFO consulta una API externa, el backend debe usar los tokens OAuth del usuario concreto, no tokens globales.
Aislamiento multi-tenant: los custom agents, documentos subidos, embeddings vectoriales y sesiones de un usuario nunca pueden filtrarse a otro. Esto incluye un fallo de seguridad actual crítico en el RAG (ver abajo).
Perfil de usuario para personalización: un schema rico que habilita, desde el día 1, que los agentes adapten tono, idioma, moneda, contexto profesional y preferencias de UI — inyectando un bloque USER_CONTEXT en el system prompt.
Estado actual verificado en el código:

No hay modelo User, ni JWT, ni endpoint de login, ni middleware de auth.
Sessions backend/app/models/session.py:31, Agents backend/app/models/agent.py:31: user_id existe como campo pero por defecto es "default_user".
n8n_client.py firma payloads con HMAC global; no hay scoping por usuario.
Frontend no tiene login UI ni token storage (solo avatar en localStorage).
Tools (cto_tools.py, cmo_tools.py, etc.) llaman a n8n sin recibir user_id.
Vulnerabilidad RAG backend/app/core/rag.py:42-50: el $vectorSearch filtra solo por agent_target (CEO/CTO/...), NO por user_id. En cuanto haya dos usuarios, uno puede recuperar fragmentos de los documentos del otro en sus chats. Es un bug de seguridad de RAG multi-tenant clásico; hay que corregirlo en esta iteración.
Decisiones confirmadas con el usuario:

Auth de app: Firebase Auth (email/password + Google/GitHub social). Google gestiona el stack crítico de seguridad (hashing, reset, MFA, refresh).
Alcance de integraciones: GitHub + Notion + Slack en la primera iteración, con infraestructura genérica para añadir más.
Ejecución de API calls: híbrido — backend como credentials broker, n8n como workflow engine. Justificación abajo.
Aislamiento: row-level scoping (un campo user_id en cada documento, filtros obligatorios en toda query). Estándar SaaS.
Agentes sistema personalizables: overlay pattern — prompts base compartidos + delta privado por usuario. Si mejoramos el prompt base, se propaga a todos salvo en los campos donde el usuario hizo override.
Alcance de perfil de personalización: core + UI + context personal + agent overrides desde el día 1. El orchestrator inyectará un bloque USER_CONTEXT en los system prompts.
Vector DB: MongoDB Atlas Vector Search (confirmado por inspección de rag.py). Hay que añadir user_id al filter compound del $vectorSearch.
Hardening adicional: Tier 1 + Tier 2 + Tier 3 completo (ver Fase 8+). Incluye rate limiting dos capas (req/min + token budget diario), whitelist de contactos por usuario para tool inputs sensibles, lock distribuido con Redis para checkpoints, circuit breaker para n8n, caché semántico de embeddings y migración de RAG a async.
Rate limiting: req/min (ventana corta, Redis) + token budget diario por usuario (MongoDB counter). Al superarlo, chat responde con error claro.
Tool input validation: whitelist de contactos por usuario (emails, teléfonos, canales). Los tools rechazan cualquier destinatario no autorizado; el agente tiene que pedir al usuario añadirlo explícitamente al perfil.
Recomendación arquitectónica: híbrido backend + n8n
El backend es la única fuente de verdad para credenciales. La decisión de dónde se ejecuta la llamada al provider se toma por tool, no por provider:

Tipo de operación	Ejemplo	Ejecuta
Atómica (1 API call)	github.create_repo, notion.create_page, slack.post_message	Backend directo vía httpx
Workflow multi-paso	"Crear repo + README + invitar equipo + anunciar en Slack + crear Notion doc"	n8n (backend pasa token del usuario en payload firmado)
Por qué preserva clean architecture:

Backend = Domain. Posee identidad + credenciales + reglas de autorización.
n8n = Infrastructure adapter opcional. Si mañana se sustituye por Temporal/Prefect, las ops atómicas siguen funcionando.
Cada tool decide su estrategia individualmente.
Evita el anti-pattern de "todo pasa por n8n" que acopla el dominio a un runtime externo.
Evolución a futuro (fuera de scope ahora): sustituir el paso de tokens a n8n por un "delegation token" efímero (5 min TTL) que n8n canjea contra el backend en runtime — patrón zero-trust. Arrancamos con HMAC + TLS, que ya existe.

Aislamiento multi-tenant: reglas de scope por colección
Colección	Scope	Clave de filtro	Nota
users	1 por usuario	firebase_uid PK	Nueva colección
oauth_credentials	Privado	(user_id, provider)	Nueva, cifrada
sessions_metadata	Privado	user_id	Ya tiene el campo; quitar default
checkpoints (LangGraph)	Privado	thread_id incluye user_id:session_id	Cambiar formato de thread_id
custom_agents	Privado	owner_user_id	Ya tiene el campo
agent_files (GridFS)	Privado	metadata.user_id	Añadir campo + índice
knowledge_base	Privado	user_id + agent_target	Crítico: también filter en $vectorSearch
message_ratings	Privado	user_id	Añadir si no existe
agent_tasks	Privado	owner_user_id	Ya tiene el campo
tool_audit_log	Privado	user_id	Añadir si no existe
user_agent_overrides	Privado	(user_id, agent_role)	Nueva — overlay pattern
oauth_states	Efímero (TTL)	state	Nueva — flujo OAuth CSRF
Regla de oro (DAO): crear un módulo backend/app/core/tenant.py con helpers:

scoped_find(collection, user_id, filter={}) — inyecta user_id automáticamente.
scoped_insert(collection, user_id, doc) — añade user_id antes de insertar.
require_owner(doc, user_id) — lanza 403 si el documento no pertenece al usuario.
Todo endpoint y tool debe usar estos helpers. Code review bloquea cualquier query que no los use.

Vector search seguro: la definición del índice vector_index en MongoDB Atlas debe declarar user_id y agent_target como filter fields. En el pipeline:

"$vectorSearch": {
    "index": "vector_index",
    "path": "embedding",
    "queryVector": query_vector,
    "numCandidates": 100,
    "limit": limit,
    "filter": {
        "$and": [
            {"user_id": {"$eq": user_id}},
            {"agent_target": {"$in": [role, "all"]}}
        ]
    }
}
Hay que actualizar el índice en Atlas (operación manual o vía script) y retroactivamente añadir user_id a los documentos existentes (migración).

Arquitectura objetivo
Frontend (React + Firebase SDK)
  │
  ├── Firebase Auth → ID token (JWT)
  │
  ▼
Backend FastAPI
  │
  ├── app/core/auth.py        ← Depends(get_current_user), verifica Firebase ID token
  ├── app/core/credentials.py ← CredentialsService (fetch/store/refresh/encrypt)
  ├── app/api/v1/auth.py      ← /me (fetch or auto-provision user)
  ├── app/api/v1/integrations.py ← /:provider/connect, /callback, DELETE, GET list
  │
  ├── MongoDB
  │   ├── users               ← firebase_uid PK, email, profile, created_at
  │   └── oauth_credentials   ← (user_id, provider) PK, tokens cifrados con Fernet
  │
  ├── Tools (cto/cmo/cfo/ceo)
  │   ├── Atomic ops → github_client.py, notion_client.py, slack_client.py
  │   └── Workflows  → n8n_client.py (con user token en payload firmado)
  │
  └── LangGraph orchestrator
      └── Inyecta user_id en el AgentState; tools lo leen vía InjectedState
Plan de implementación por fases
Fase 1 — Capa de auth (Firebase + middleware)
Añadir a backend/requirements.txt: firebase-admin, cryptography, authlib.
Ampliar backend/app/core/config.py:
FIREBASE_CREDENTIALS_PATH (service account JSON)
FERNET_KEY (para cifrar tokens en reposo)
GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, NOTION_CLIENT_ID, NOTION_CLIENT_SECRET, SLACK_CLIENT_ID, SLACK_CLIENT_SECRET
OAUTH_REDIRECT_BASE_URL (callback base)
Crear backend/app/core/auth.py:
Inicializar firebase_admin en lifespan.
get_current_user(request) -> User como FastAPI dependency: lee header Authorization: Bearer <id_token>, verifica con firebase_admin.auth.verify_id_token, auto-provisiona el documento users si no existe.
Crear backend/app/api/v1/auth.py: GET /me, PATCH /me (editar perfil).
Fase 2 — Modelo User con perfil rico de personalización
Crear backend/app/models/user.py con el schema completo (todo opcional salvo core, se rellena gradualmente):

# Core (MVP, creado en el primer login)
firebase_uid: str              # PK
email: EmailStr
display_name: str
avatar_url: Optional[str]
created_at: datetime
last_login_at: datetime
onboarding_completed: bool = False

# UI preferences
ui_preferences: {
    theme: Literal["dark", "light", "system"] = "system",
    accent_color: str = "#7c3aed",
    locale: str = "es-ES",
    timezone: str = "Europe/Madrid",
    artifact_default_open: bool = True,
    tool_confirmation_level: Literal["always", "destructive_only", "never"] = "destructive_only",
}

# Context personal (se inyecta en system prompts como USER_CONTEXT)
professional_profile: {
    role: Optional[str],              # "Founder", "PM", "Dev", ...
    industry: Optional[str],          # "SaaS B2B", "e-commerce", ...
    company_name: Optional[str],
    company_stage: Optional[str],     # "idea", "seed", "series-A", ...
    team_size: Optional[int],
}
communication_style: {
    tone: Literal["formal", "casual"] = "casual",
    verbosity: Literal["concise", "detailed"] = "concise",
    language_register: Optional[str], # texto libre, ej: "usa tuteo"
}
financial_preferences: {
    base_currency: str = "EUR",
    fiscal_year_start_month: int = 1,
}
personal_kb_enabled: bool = True    # ¿Todos los agentes leen el KB personal?

# Agent overrides (overlay pattern)
# No vive aquí: se guarda en colección user_agent_overrides por (user_id, agent_role)
# para que sea editable de forma granular y versionable.

# Flags
feature_flags: List[str] = []
connected_providers: List[str] = []  # denormalizado para UI rápida

# Rate limiting / uso (persistido aquí para visibilidad del usuario)
usage: {
    token_budget_daily: int = 100_000,      # override-able por admin
    tokens_used_today: int = 0,
    tokens_reset_at: datetime,
    requests_in_current_window: int = 0,    # denormalizado desde Redis
}
2b. Colección contacts (whitelist por usuario): separada del documento User para que sea editable de forma granular:

Contact {
    user_id: str,                           # FK al owner
    type: Literal["email", "phone", "slack_channel", "github_user", "linkedin_handle"],
    value: str,                             # normalizado (E.164 para tel, lowercase para email)
    display_name: Optional[str],
    authorized_for: List[str],              # tools permitidos: ["whatsapp_send_message", "calendar_create_event", ...]
    added_at: datetime,
}
Índice único compuesto (user_id, type, value). Los tools que envían mensajes/invitaciones externas consultan esta colección antes de ejecutar.

Añadir colección users con índice único en firebase_uid y email en backend/app/core/database.py.
Refactor de endpoints para inyectar user: User = Depends(get_current_user):
backend/app/api/v1/sessions.py
backend/app/api/v1/agents.py
backend/app/api/v1/chat.py
backend/app/api/v1/stream.py
Todos usan scoped_find/scoped_insert del módulo tenant.py.
Eliminar user_id = "default_user" por defecto en backend/app/models/session.py:31 y backend/app/models/agent.py:31: el campo pasa a ser requerido, siempre poblado desde el JWT.
Endpoints del perfil en backend/app/api/v1/auth.py:
GET /me — devuelve el perfil completo.
PATCH /me — actualización parcial de UI preferences, professional_profile, communication_style, financial_preferences.
POST /me/onboarding/complete — marca onboarding_completed.
Fase 3 — Credentials store cifrado
Crear backend/app/models/oauth_credential.py:
OAuthCredential { user_id, provider, access_token_enc, refresh_token_enc,
                  scopes, expires_at, connected_at, revoked_at }
Añadir colección oauth_credentials con índice compuesto (user_id, provider) único.
Crear backend/app/core/credentials.py con CredentialsService:
get_token(user_id, provider) -> str (refresca automáticamente si expires_at está cerca).
store_token(user_id, provider, token_data) (cifra con Fernet antes de escribir).
revoke(user_id, provider) (soft-delete + llamada al revoke endpoint del provider).
Cifrado: cryptography.fernet.Fernet(settings.FERNET_KEY). La clave vive en .env, nunca en código.
Fase 4 — OAuth flows (GitHub, Notion, Slack)
Crear backend/app/integrations/providers/ con un módulo por provider:
github.py, notion.py, slack.py, cada uno expone authorize_url(state), exchange_code(code), refresh(refresh_token), revoke(token).
Scopes iniciales: GitHub repo,read:user; Notion read,update; Slack chat:write,channels:read.
Crear backend/app/api/v1/integrations.py:
GET /:provider/connect → genera state (nonce CSRF + user_id firmado con HMAC), guarda en Redis o colección temporal oauth_states, redirige a authorize_url.
GET /:provider/callback → valida state, intercambia code por tokens, llama a CredentialsService.store_token, redirige al frontend /settings/integrations?connected=github.
GET /integrations → lista providers conectados del usuario (sin exponer tokens).
DELETE /:provider → revoca.
Ruteo: GET /login/:provider como alias público no es necesario aquí; todo requiere get_current_user.
Fase 5 — Tools con acceso a credenciales
Crear clientes atómicos en backend/app/tools/clients/:
github_client.py (create_repo, create_issue, create_pr_comment).
notion_client.py (create_page, update_page).
slack_client.py (post_message, list_channels).
Todos reciben access_token y usan httpx.AsyncClient.
Refactor de tools existentes para recibir user_id vía LangGraph InjectedState:
backend/app/tools/cto_tools.py: las funciones _create_jules_task, etc. pasan a aceptar user_id: Annotated[str, InjectedState("user_id")]. Internamente llaman CredentialsService.get_token(user_id, "github") y deciden: si es una op atómica (crear repo simple), llaman a github_client directo; si es "delega a Jules" (workflow multi-paso), siguen pasando por n8n_client incluyendo el token en el payload firmado.
Hacer lo mismo en cmo_tools.py, cfo_tools.py, ceo_tools.py, shared_tools.py.
Modificar backend/app/core/orchestrator.py:46 — añadir user_id: str al AgentState y propagarlo desde backend/app/api/v1/stream.py / chat.py al construir el grafo.
Actualizar backend/app/tools/n8n_client.py: método call_webhook(path, payload, user_id=None, required_providers=None) que, si required_providers está presente, adjunta user_tokens: {provider: encrypted_token} al payload (cifrado con clave compartida con n8n, TTL corto).
Fase 6 — Frontend
Instalar firebase en frontend/package.json.
Crear frontend/src/lib/firebase.ts con init del SDK (config desde env públicos VITE_FIREBASE_*).
Crear frontend/src/contexts/AuthContext.tsx: provider con user, idToken, signIn, signOut, listeners de onIdTokenChanged.
Crear frontend/src/pages/Login.tsx: email/password + botones Google/GitHub social.
Wrapper RequireAuth en frontend/src/App.tsx que redirige a /login si no hay sesión.
Modificar el cliente HTTP (p.ej. frontend/src/lib/api.ts o similar) para inyectar Authorization: Bearer ${idToken} automáticamente.
Crear frontend/src/pages/settings/Integrations.tsx: lista de providers con estado (Connected/Not connected) y botones Connect/Disconnect que llaman a /api/v1/integrations/:provider/connect y manejan el redirect.
Eliminar toda referencia hardcodeada a "default_user" (si la hay en frontend).
Fase 6.5 — Aislamiento multi-tenant (core + RAG fix)
Crear backend/app/core/tenant.py con los helpers scoped_find, scoped_insert, require_owner, scoped_update, scoped_delete. Firma ejemplo:
async def scoped_find(collection, user_id: str, filter: dict = None) -> Cursor:
    return collection.find({**(filter or {}), "user_id": user_id})
Refactorizar todas las queries actuales en endpoints y tools para usar estos helpers. Barrida sistemática:
backend/app/api/v1/sessions.py, agents.py, chat.py, stream.py
Cualquier lugar donde se haga collection.find(...) o find_one(...) directo.
Fix de seguridad en RAG — modificar backend/app/core/rag.py:
retrieve_context(query, role, user_id, limit) — añadir parámetro obligatorio user_id.
Filter del $vectorSearch pasa a ser {"$and": [{"user_id": user_id}, {"agent_target": {"$in": [role, "all"]}}]}.
Propagar user_id desde orchestrator.py (leyéndolo de AgentState) hasta retrieve_context.
Actualizar definición del índice vector_index en MongoDB Atlas:
Declarar user_id y agent_target como filter fields.
Documentar el cambio en backend/scripts/vector_index_definition.json para que sea reproducible.
GridFS agent_files: añadir metadata.user_id en upload y filtrar en descarga.
Checkpoints LangGraph: usar thread_id = f"{user_id}:{session_id}" para que el MongoDBSaver aísle por usuario de forma natural. Actualizar backend/app/api/v1/stream.py y chat.py al construir el config={"configurable": {"thread_id": ...}}.
Migración retroactiva (backend/scripts/backfill_user_id.py):
Añadir user_id = "<owner_dev_uid>" a todos los documentos existentes en knowledge_base, custom_agents, sessions_metadata, agent_files.files, message_ratings, agent_tasks, checkpoints (o borrarlos si es entorno limpio — confirmar con el usuario antes de ejecutar).
Fase 6.75 — Overlay de agentes sistema + inyección de USER_CONTEXT
Nueva colección user_agent_overrides con índice único (user_id, agent_role):
UserAgentOverride {
    user_id: str,
    agent_role: str,              # "CEO", "CTO", "CFO", "CMO", o el id de un custom agent
    system_prompt_addition: Optional[str],  # se concatena al prompt base
    temperature_override: Optional[float],
    model_override: Optional[str],
    updated_at: datetime,
}
Crear backend/app/core/agent_resolver.py:
resolve_agent_config(user_id, agent_role) -> ResolvedAgent — lee el prompt base (de DEFAULT_CORE_PROMPTS o custom_agents), hace merge con el override del usuario si existe, devuelve {system_prompt, temperature, model}.
Modificar backend/app/core/orchestrator.py: el nodo de agente llama a resolve_agent_config(state["user_id"], state["target_role"]) antes de invocar al LLM, en lugar de leer directamente DEFAULT_CORE_PROMPTS.
Crear backend/app/core/user_context.py con build_user_context_block(user: User) -> str:
USER_CONTEXT:
- Nombre: {display_name}
- Rol: {role} en {company_name} ({industry}, {company_stage}, equipo de {team_size})
- Estilo preferido: {tone}, {verbosity}
- Idioma: {locale}
- Moneda base: {base_currency}
Solo incluye los campos poblados (si professional_profile.role está vacío, se omite la línea).
El orchestrator prepend este bloque al system prompt resuelto. Resultado: los agentes adaptan respuestas automáticamente sin que el usuario tenga que configurar nada explícito en el chat.
Endpoints en backend/app/api/v1/auth.py:
GET /me/agent-overrides — lista overrides del usuario.
PUT /me/agent-overrides/:agent_role — crea/actualiza override.
DELETE /me/agent-overrides/:agent_role — elimina (vuelve al default del sistema).
Fase 7 — Tests y migración
Fixtures nuevas en backend/tests/conftest.py:
mock_firebase_user — stubea firebase_admin.auth.verify_id_token.
authed_client — async_client con header Bearer ya inyectado.
user_with_github_token — crea documento en oauth_credentials.
user_with_contact — precarga un contacto en whitelist.
redis_test_client — instancia de Redis de test (fakeredis o contenedor).
Nuevos tests:
test_auth.py — verificación de token, auto-provisioning, 401 sin header.
test_integrations.py — OAuth flow, state validation, encryption en reposo.
test_credentials_service.py — refresh automático, revoke, cifrado.
test_tools_with_auth.py — un tool falla si el usuario no tiene el provider conectado.
test_tenant_isolation.py — user A no ve sessions/agents/docs/tasks de user B.
test_rag_isolation.py — crítico: retrieve_context como user B no devuelve embeddings de user A.
test_agent_overrides.py — overlay pattern funciona, borrar override vuelve al default.
test_user_context.py — USER_CONTEXT se inyecta en system prompt con los campos poblados.
test_rate_limit.py — req/min y token budget funcionan; user queda rate-limited con mensaje claro.
test_tool_input_validation.py — whatsapp_send_message rechaza un to que no está en contacts; calendar_create_event rechaza attendees no autorizados.
test_transactions.py — crear session + checkpoint es atómico; si falla el segundo, no queda session huérfana.
test_idempotency.py — POST /sessions con mismo idempotency_key no duplica.
test_checkpoint_concurrency.py — 2 mensajes rápidos a la misma sesión no corrompen el checkpoint (con distributed lock).
test_circuit_breaker.py — n8n caído → tras N fallos el circuito abre y responde rápido con error sin llamar a n8n.
Migración one-shot de dev data: script backend/scripts/migrate_default_user.py que reasigne todos los documentos con user_id="default_user" al UID del owner de dev (o los borre en entornos limpios). Confirmar con el usuario qué estrategia aplicar antes de ejecutar.
Fase 8 — Hardening de tool inputs y prompt injection
Problema: shared_tools.py:57-144 y otros tools aceptan attendees, to, group, channel directamente desde el LLM. Un prompt injection puede hacer que el agente mande mensajes a contactos arbitrarios o cree eventos con emails inventados.

Contacts service (backend/app/core/contacts_service.py):
is_authorized(user_id, tool_name, contact_value, contact_type) -> bool
list_contacts(user_id) -> List[Contact]
add_contact(user_id, contact) con normalización (E.164, lowercase email).
remove_contact(user_id, contact_id).
Validación en todas las tools de envío externo (barrido sistemático):
whatsapp_send_message: valida to contra contacts con type=phone y authorized_for incluye whatsapp_send_message.
whatsapp_send_notification: valida group.
whatsapp_read_messages: solo lectura, no requiere whitelist pero sí log.
calendar_create_event: cada attendee validado contra contacts type=email.
post_to_linkedin, post_to_instagram: validan handle/cuenta contra contacts y además exigen tool_confirmation_level != "never" para confirmar antes de publicar.
slack.post_message: valida channel.
github.create_repo: valida owner (solo puede ser la cuenta del usuario autenticado; rechaza si es una org que no está en contacts).
Formato estricto via Pydantic: EmailStr para emails, validator custom para E.164 en teléfonos, regex para slack channels.
UI de gestión: nueva página frontend/src/pages/settings/Contacts.tsx con CRUD de contactos y toggles de authorized_for.
Experiencia cuando falla la validación: el tool devuelve un error estructurado {"error": "contact_not_authorized", "contact": "...", "hint": "add it at Settings → Contacts"} que el agente sabe interpretar y pedir al usuario que autorice el contacto.
Confirmación para acciones destructivas independientemente de whitelist: el orchestrator lee ui_preferences.tool_confirmation_level y, si vale "always" o "destructive_only", inserta un nodo confirm_before_execute en el grafo para tools marcados como destructivos (post_to_linkedin, calendar_create_event con attendees, whatsapp_send_message, github.delete_repo).
Fase 9 — Rate limiting y presupuesto de tokens
Estrategia: dos capas — ventana corta (req/min) con Redis y presupuesto diario (tokens) en MongoDB.

Dependencias nuevas: redis[hiredis], slowapi (o fastapi-limiter).
Config nuevo en backend/app/core/config.py:
REDIS_URL
RATE_LIMIT_REQUESTS_PER_MINUTE: int = 30
RATE_LIMIT_CHAT_PER_MINUTE: int = 10 (más restrictivo para el endpoint de chat)
TOKEN_BUDGET_DAILY_DEFAULT: int = 100_000
TOKEN_BUDGET_RESET_HOUR_UTC: int = 0
Middleware en backend/main.py: fastapi-limiter con Redis, rate limit REQUESTS_PER_MINUTE global por user_id (extraído del JWT). Endpoints de chat llevan un decorator adicional más restrictivo.
Token budget (backend/app/core/token_budget.py):
consume(user_id, tokens) -> bool — atómico con $inc sobre users.usage.tokens_used_today.
check_available(user_id, estimated_tokens) -> bool.
Reset diario: job TTL de MongoDB o tarea al arranque.
Integración en orchestrator: antes de cada invocación al LLM, llamar check_available. Tras cada invocación, consume con los tokens reales (leídos del response de OpenAI/DeepSeek). Si check_available devuelve False, abortar turn con mensaje "Has alcanzado tu límite diario de tokens. Se resetea a las 00:00 UTC.".
UI: en Settings o header de la app, mostrar barra de uso tokens_used_today / token_budget_daily.
Admin override (fuera de scope end-user por ahora): endpoint interno PATCH /admin/users/:uid/usage para ampliar el budget de un usuario. Proteger con feature flag/role.
Fase 10 — Concurrencia, transacciones y resilience
Transacciones Mongo en creates multi-colección. Motor soporta async with client.start_session() + start_transaction(). Afectar:
backend/app/api/v1/sessions.py — crear session + checkpoint inicial atómico.
backend/app/api/v1/agents.py — crear agent + inicializar documentos relacionados.
backend/app/api/v1/integrations.py — callback OAuth: store_token + update users.connected_providers atómico.
Idempotency keys: backend/app/api/v1/sessions.py POST / acepta header Idempotency-Key. Guardar (user_id, idempotency_key) -> session_id en colección idempotency_keys con TTL de 24h. Si se repite, devolver el session_id original.
Fix del bug tool_calls_remaining orchestrator.py:332: resetear al inicio de cada turn (cuando entra un nuevo HumanMessage), no dejar que persista en el checkpoint como estado permanente.
Distributed lock por thread_id (Tier 3): backend/app/core/distributed_lock.py con Redis SET NX EX. Wrap del nodo de ejecución del grafo: lock checkpoint:{user_id}:{session_id} con TTL 60s, liberar al terminar. Si otro request intenta mientras, responder 409 Conflict con "Tu mensaje anterior aún se está procesando".
Retry con exponential backoff en backend/app/tools/n8n_client.py: usar tenacity — 3 reintentos con backoff 1s/2s/4s, solo en errores 5xx o timeouts de red.
Circuit breaker (Tier 3): backend/app/core/circuit_breaker.py con estado en Redis (closed/open/half_open). Umbral: 5 fallos consecutivos → abierto por 30s. Aplicar a n8n_client.call_webhook. Si abierto, devolver error inmediato "n8n no disponible" sin llamar.
Stream cleanup: stream.py — envolver el generador en try/finally y cerrar cursores Mongo y conexiones httpx en el finally. Cancelar tareas asyncio pendientes si el cliente desconecta (GeneratorExit).
Fase 11 — Operaciones, performance y observabilidad
Paginación obligatoria:
GET /sessions/ — params limit (default 50, max 200) y cursor (next_page token basado en created_at + _id).
GET /agents/ — idem.
GET /documents/:agent_id — idem.
Helper backend/app/core/pagination.py con paginate(cursor, limit) reutilizable.
Timeouts en llamadas externas:
OpenAI embeddings en rag.py:34: timeout=15.0.
DeepSeek en ChatOpenAI: request_timeout=60.0 en la construcción de llm_router y llm_expert.
httpx de github_client, notion_client, slack_client: timeout=Timeout(connect=5, read=30, write=10, pool=5).
n8n (ya tiene 30s por defecto) — verificar y explicitar.
Validación de env vars al boot [main.py lifespan]: al arranque, validar que MONGODB_URL, OPENAI_API_KEY, DEEPSEEK_API_KEY, FIREBASE_CREDENTIALS_PATH, FERNET_KEY, REDIS_URL, provider client_ids/secrets existen. Si falta alguno crítico, abortar con mensaje claro (fail-fast).
Health check enriquecido backend/app/api/v1/health.py:
GET /health/live — liveness probe, solo responde 200 si el proceso vive.
GET /health/ready — readiness probe, verifica Mongo ping + Redis ping + (opcional, timeout corto) ping a OpenAI/DeepSeek. Devuelve 503 si alguna dependencia crítica está caída.
Quota de GridFS por usuario:
Config GRIDFS_QUOTA_MB_PER_USER: int = 500.
Antes de cada upload, sumar tamaño actual en agent_files filtrando por metadata.user_id. Rechazar con 413 si se supera.
UI en Settings → Storage con barra de uso.
Duplicate detection en upload de documentos:
Calcular SHA256 del contenido antes de insertar en GridFS.
Añadir campo content_hash a agent_files.files.metadata.
Si existe (user_id, agent_id, content_hash) ya → devolver el file_id existente con flag duplicate=True, no duplicar embeddings.
Índice compuesto (metadata.user_id, metadata.agent_id, metadata.content_hash).
Caché semántico de embeddings (Tier 3):
backend/app/core/embedding_cache.py — Redis con TTL 24h.
Key: sha256(normalized_query_text + model_name).
Antes de llamar a OpenAI en retrieve_context, mirar cache.
Métrica de hit rate para verificar efectividad.
Migración RAG a async con Motor (Tier 3): reescribir rag.py para usar motor en lugar de pymongo sync. Elimina el run_in_executor, libera el thread pool.
Índices compuestos nuevos en backend/app/core/database.py:
sessions_metadata: (user_id, created_at DESC), (user_id, updated_at DESC).
custom_agents: (owner_user_id, created_at DESC).
agent_files.files: (metadata.user_id, metadata.agent_id), (metadata.user_id, metadata.content_hash).
knowledge_base: el índice vectorial Atlas con user_id y agent_target como filter fields.
message_ratings: (user_id, session_id, message_id) único.
agent_tasks: (owner_user_id, status, priority).
tool_audit_log: (user_id, created_at DESC).
oauth_credentials: (user_id, provider) único.
oauth_states: (state) único + TTL index en expires_at.
contacts: (user_id, type, value) único.
idempotency_keys: (user_id, idempotency_key) único + TTL 24h.
user_agent_overrides: (user_id, agent_role) único.
Correlation IDs en logs (Tier 3): middleware FastAPI genera request_id por request, lo propaga como context var y todos los logs lo incluyen. Facilita rastrear una request end-to-end en producción.
Response error sanitization: helper safe_error_response(exc) -> dict que nunca incluye str(e) directo. Log completo en server, cliente recibe solo {"error_code": "...", "message": "..."}. Modificar stream.py:236 y cualquier otro sitio que exponga str(e).
CORS más estricto main.py:98-104: allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"], allow_headers=["Authorization", "Content-Type", "Idempotency-Key"]. Quitar ["*"].
CSP y security headers: middleware que añade X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Strict-Transport-Security (en producción), Referrer-Policy: strict-origin-when-cross-origin.
Ficheros críticos (resumen)
Nuevos:

backend/app/core/auth.py — Firebase verification + get_current_user
backend/app/core/tenant.py — helpers de scoping (scoped_find/insert/update)
backend/app/core/credentials.py — CredentialsService
backend/app/core/agent_resolver.py — overlay de prompts sistema + user
backend/app/core/user_context.py — builder del bloque USER_CONTEXT
backend/app/core/contacts_service.py — whitelist de contactos
backend/app/core/token_budget.py — tracking y enforcement de presupuesto
backend/app/core/distributed_lock.py — lock Redis por thread_id
backend/app/core/circuit_breaker.py — circuit breaker genérico
backend/app/core/embedding_cache.py — caché semántico Redis
backend/app/core/pagination.py — helper de cursor pagination
backend/app/core/error_handling.py — safe_error_response
backend/app/core/redis_client.py — cliente Redis singleton
backend/app/models/user.py — perfil rico
backend/app/models/oauth_credential.py
backend/app/models/user_agent_override.py
backend/app/models/contact.py
backend/app/models/idempotency_key.py
backend/app/api/v1/auth.py — /me, /me/agent-overrides, /me/onboarding, /me/contacts, /me/usage
backend/app/api/v1/integrations.py — OAuth flows
backend/app/integrations/providers/{github,notion,slack}.py
backend/app/tools/clients/{github,notion,slack}_client.py
backend/scripts/vector_index_definition.json — para reproducir el índice de Atlas
backend/scripts/backfill_user_id.py — migración retroactiva
frontend/src/lib/firebase.ts
frontend/src/contexts/AuthContext.tsx
frontend/src/pages/Login.tsx
frontend/src/pages/settings/Integrations.tsx
frontend/src/pages/settings/Profile.tsx — editar professional_profile, communication_style, financial_preferences
frontend/src/pages/settings/AgentOverrides.tsx — personalizar prompts de CEO/CTO/CFO/CMO
frontend/src/pages/settings/Contacts.tsx — CRUD de whitelist de contactos
frontend/src/pages/settings/Storage.tsx — quota GridFS + usage de tokens
frontend/src/components/TokenUsageBar.tsx — barra de uso en header
frontend/src/components/ToolConfirmationModal.tsx — confirmación antes de acciones destructivas
Modificados:

backend/requirements.txt — añadir firebase-admin, cryptography, authlib, redis[hiredis], slowapi o fastapi-limiter, tenacity
backend/app/core/config.py — Firebase, Fernet, provider OAuth, Redis, rate limits, token budget, quotas, timeouts
backend/app/core/database.py — nuevas colecciones + todos los índices compuestos (ver Fase 11)
backend/app/core/orchestrator.py — user_id en AgentState, llamar a agent_resolver + user_context + token_budget.check_available/consume + resetear tool_calls_remaining por turn + integrar distributed_lock
backend/app/core/rag.py — fix de seguridad: filter por user_id en $vectorSearch + migración a motor async + embedding_cache + timeout OpenAI
backend/app/core/logger.py — correlation IDs
backend/app/models/session.py, backend/app/models/agent.py — quitar default "default_user"
backend/app/api/v1/sessions.py — Depends(get_current_user) + scoped_* + thread_id = user_id:session_id + transacción Mongo al crear + idempotency key + paginación
backend/app/api/v1/agents.py — idem + transacción al crear + paginación
backend/app/api/v1/chat.py, stream.py — auth + scoping + distributed lock + cleanup en GeneratorExit + safe_error_response
backend/app/api/v1/documents.py — auth + scoping + quota GridFS + duplicate detection SHA256 + paginación
backend/app/api/v1/health.py — split /live y /ready con checks de Mongo/Redis/OpenAI/DeepSeek
backend/app/tools/cto_tools.py, cmo_tools.py, cfo_tools.py, ceo_tools.py, shared_tools.py — InjectedState("user_id") + validación contra contacts_service en tools de envío
backend/app/tools/n8n_client.py — inclusión de user tokens + retry con tenacity + circuit breaker
backend/main.py — init firebase + redis en lifespan, validación fail-fast de env vars, CORS estricto, security headers middleware, rate limit middleware
backend/tests/conftest.py — fixtures firebase + redis + user + contacts
frontend/src/App.tsx — RequireAuth wrapper
frontend/src/lib/api.ts (o donde esté el cliente HTTP) — inyectar Bearer token, manejar 401 (redirect login) y 429 (mostrar mensaje rate limit)
Verificación end-to-end
Manual (flujo golden path):

Levantar backend + frontend localmente.
Registrarse con email en Firebase desde /login; verificar en MongoDB que se auto-creó el documento en users.
En Settings → Profile, completar professional_profile (rol "Founder", industria "SaaS B2B", company_name "Paintec") y communication_style (concise + casual). Guardar.
Abrir un chat nuevo con el CEO. Saludarle. Verificar en logs que el system prompt tiene inyectado el bloque USER_CONTEXT con los datos del perfil y que el agente responde adaptando tono/contexto.
Ir a Settings → Integrations → "Connect GitHub" → autorizar la app → volver al callback → verificar que aparece "Connected" y que en oauth_credentials hay un documento cifrado.
Pedirle al CTO: "crea un repo nuevo llamado sphere-test". Verificar que el repo aparece en la cuenta GitHub del usuario autenticado.
Personalizar el prompt del CTO en Settings → Agent Overrides (ej. "siempre responde con ejemplos en TypeScript"). Abrir un chat nuevo y verificar que el CTO aplica el override.
Test de aislamiento: logout, login con otro usuario (crear un segundo Firebase account). Debe:
NO ver las sesiones del primer usuario.
NO ver los agentes custom del primer usuario.
NO recuperar fragmentos del knowledge_base del primer usuario en sus chats (aunque pregunte exactamente sobre un documento que subió el otro).
Tener que conectar GitHub otra vez.
Tener su propio perfil y overrides independientes.
Desconectar GitHub y verificar que el siguiente intento de crear repo falla con un error claro "GitHub no conectado".
Automatizado:

pytest backend/tests/test_auth.py backend/tests/test_integrations.py backend/tests/test_credentials_service.py backend/tests/test_tools_with_auth.py backend/tests/test_tenant_isolation.py backend/tests/test_rag_isolation.py backend/tests/test_agent_overrides.py backend/tests/test_user_context.py
test_rag_isolation.py es crítico: inserta docs de user A y user B, ejecuta retrieve_context como user B, verifica que no aparece nada de user A.
Seguridad (checklist):

Tokens en reposo están cifrados (inspeccionar documento crudo en MongoDB).
Un request sin header Authorization devuelve 401 en todos los endpoints protegidos.
state del OAuth flow tiene CSRF nonce + expiración.
FERNET_KEY y secrets de providers NO aparecen en logs ni en respuestas de error.
Revocar el token en el provider (ej. desde GitHub Settings) invalida el uso en SPHERE (refresh falla → se marca como revoked).
Aislamiento multi-tenant: ningún endpoint devuelve datos con user_id distinto al del JWT. Auditar con un grep de .find( / .find_one( para detectar queries sin scoping.
Vector search seguro: el filter compound user_id + agent_target está en el índice y en el pipeline. Test explícito en test_rag_isolation.py.
Tool input validation: intentar con un LLM que genere un whatsapp_send_message con un número no autorizado — debe fallar con contact_not_authorized.
Rate limiting: enviar 50 requests/min desde un user → los últimos 20 devuelven 429 con header Retry-After.
Token budget: forzar a un user a consumir su quota diario → el siguiente mensaje devuelve mensaje claro sin invocar al LLM.
Error sanitization: provocar un error en DB (ej. query inválida) y verificar que la response NO incluye nombres de colecciones, stack traces ni str(e) crudo.
CORS: OPTIONS preflight desde origen no autorizado devuelve sin headers Access-Control-Allow-*.
Security headers: verificar presencia de X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Strict-Transport-Security (en prod).
Idempotency: reenviar POST /sessions con mismo Idempotency-Key devuelve el mismo session_id sin crear duplicado.
Transacciones: simular fallo entre insert de session e insert de checkpoint; verificar que no queda session huérfana en Mongo.
Circuit breaker: tirar n8n, enviar 6 tool calls, verificar que después del 5º el circuito abre y el 6º responde inmediato sin llamar a n8n.
GridFS quota: subir archivos hasta superar GRIDFS_QUOTA_MB_PER_USER y verificar rechazo 413.
Fuera de scope (para iteraciones posteriores)
Otros providers mencionados en los prompts actuales: Google Calendar, WhatsApp Business, LinkedIn, Instagram/Meta, APIs financieras. El patrón queda generalizado; añadirlos es copy/paste del módulo providers/<nombre>.py + botón en UI.
Delegation tokens efímeros para n8n (zero-trust). Arrancamos con token cifrado en payload firmado.
Roles/permisos internos dentro de SPHERE (admin, viewer, etc.). Por ahora todos los usuarios autenticados tienen el mismo nivel de acceso a sus propios recursos.
MFA más allá del que ofrezca Firebase por defecto.
Equipos / workspaces compartidos: por ahora cada usuario es un tenant aislado. Añadir "organizaciones" donde varios usuarios comparten custom agents y knowledge base es una extensión futura — el schema actual (owner_user_id) tendría que evolucionar a owner_org_id con membresías.
Personal Knowledge Base dedicado (más allá del knowledge_base que ya existe). El personal_kb_enabled flag queda definido pero su integración con el retriever se activa en una iteración posterior.
Theming avanzado (custom CSS por usuario, logos, branding). El ui_preferences queda listo para extenderse.
Export/import de perfil y data (GDPR right to portability).
Admin panel / dashboard para gestionar usuarios, budgets, feature flags. Los endpoints internos existirán pero sin UI todavía.
WebSocket / push notifications (reemplazo de polling para notificaciones asíncronas).
Riesgos y orden de implementación recomendado
Orden por dependencias (no por prioridad de negocio):

Semana 1: Fase 1 (auth) + Fase 2 (user model) + Fase 11 punto 3 (env vars fail-fast) + Fase 11 punto 4 (health splits). Desbloquea todo lo demás.
Semana 2: Fase 6.5 (aislamiento + RAG fix) + Fase 11 punto 9 (índices) + Fase 10 puntos 1-2 (transacciones + idempotency) + Fase 11 punto 1 (paginación). Estabiliza la base multi-tenant.
Semana 3: Fase 3 (credentials store) + Fase 4 (OAuth flows GitHub/Notion/Slack) + Fase 5 (tools con credenciales) + Fase 8 (contacts + tool input validation).
Semana 4: Fase 6 (frontend completo) + Fase 6.75 (agent overlay + USER_CONTEXT) + Fase 9 (rate limit + token budget).
Semana 5: Fase 10 puntos 3-7 (resilience avanzado: lock distribuido, circuit breaker, retries, stream cleanup) + Fase 11 puntos 5-8 (quota, dedupe, cache, async RAG).
Semana 6: Fase 7 (tests exhaustivos) + Fase 11 puntos 10-13 (correlation IDs, error sanitization, CORS, security headers) + migración retroactiva + deploy.
Riesgos principales del plan:

Cambio de thread_id de checkpoints: rompe sesiones existentes. Aceptable en dev; en prod requiere migración escrita con cuidado (o clean cut).
Redis como nueva dependencia: añade infraestructura. Si el equipo no tiene Redis todavía, es 1-2 días de setup adicional (Docker Compose local + provisioning en prod).
Volumen de cambios simultáneos: 6 semanas es optimista si solo trabajas tú. Para 1 persona, realista son 10-12 semanas. Conviene cortar releases intermedias estables en vez de una única big bang.
Compatibilidad con Firebase Auth free tier: 50K MAU es cómodo ahora; si la app explota en usuarios hay que planear migración a Blaze o a auth propio. No bloqueante hoy.
Add Comment