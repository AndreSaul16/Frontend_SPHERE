"""
SPHERE Backend - FastAPI Application
Orquestador multi-tenant de agentes IA para startups.
"""

import hashlib
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.infrastructure.database import db
from app.core.logger import api_logger as logger
from app.presentation.api.v1 import (
    health,
    stream,
    sessions,
    agents,
    documents,
    auth,
    integrations,
    billing,
    webhooks,
)
from app.infrastructure.tools.n8n_client import N8NClient
import app.infrastructure.tools.n8n_client as n8n_module


async def user_or_ip_identifier(request: Request) -> str:
    """
    Identificador para rate limiting. Prefiere user (hash del Bearer token),
    cae a IP si no hay auth. Evita verificar el JWT en cada request (costoso).
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        return "user:" + hashlib.sha256(token.encode()).hexdigest()[:16]
    client_host = request.client.host if request.client else "unknown"
    return "ip:" + client_host


def _validate_env_vars():
    """
    Valida variables de entorno según ENVIRONMENT.

    - En PRODUCCIÓN: todas las críticas son obligatorias. Si falta alguna, aborta.
    - En DEV: solo MONGODB_URL es obligatoria; el resto warns.
    """
    # Siempre obligatorias
    always_critical = {
        "MONGODB_URL": settings.MONGODB_URL,
    }

    # Críticas SOLO en producción.
    # Firebase NO va aquí: se valida aparte porque acepta credenciales por archivo
    # (FIREBASE_CREDENTIALS_PATH) O por contenido JSON (FIREBASE_CREDENTIALS_JSON,
    # que es lo que se usa en Railway). Exigir solo el PATH crasheaba el arranque.
    prod_critical = {
        "OPENAI_API_KEY": settings.OPENAI_API_KEY,
        "DEEPSEEK_API_KEY": settings.DEEPSEEK_API_KEY,
        "FERNET_KEY": settings.FERNET_KEY,
        "REDIS_URL": settings.REDIS_URL,
    }

    missing_always = [k for k, v in always_critical.items() if not v]
    if missing_always:
        raise RuntimeError(
            f"Variables críticas faltantes: {', '.join(missing_always)}. "
            f"Configura tu .env antes de arrancar."
        )

    # Stripe config validation (AD5): no es bloqueante, pero loguea CRITICAL si falta
    if settings.stripe_configured:
        logger.info("Stripe configurado — pagos habilitados")
    else:
        logger.critical(
            "STRIPE_SECRET_KEY no configurada. "
            "Los pagos estarán DESHABILITADOS. "
            "El frontend usará stripe_configured=false para ocultar la UI de pagos."
        )

    missing_prod = [k for k, v in prod_critical.items() if not v]
    # Firebase: vale FIREBASE_CREDENTIALS_JSON (Railway) o FIREBASE_CREDENTIALS_PATH (archivo).
    if not (settings.FIREBASE_CREDENTIALS_JSON or settings.FIREBASE_CREDENTIALS_PATH):
        missing_prod.append("FIREBASE_CREDENTIALS_JSON|FIREBASE_CREDENTIALS_PATH")
    if missing_prod:
        if settings.is_production:
            raise RuntimeError(
                f"[PRODUCCIÓN] Variables obligatorias faltantes: {', '.join(missing_prod)}. "
                f"Configura tu .env o cambia ENVIRONMENT=development para modo local."
            )
        logger.warning(
            f"[DEV] Variables no configuradas: {', '.join(missing_prod)}. "
            f"Algunas features estarán deshabilitadas o en modo mock."
        )

    logger.info(f"Entorno: {settings.ENVIRONMENT}")


async def _ensure_indexes():
    """Crea índices críticos de MongoDB si no existen."""
    from pymongo import ASCENDING, DESCENDING
    from app.infrastructure.database import (
        get_sessions_collection,
        get_custom_agents_collection,
        get_users_collection,
        get_oauth_credentials_collection,
        get_oauth_states_collection,
        get_contacts_collection,
        get_user_agent_overrides_collection,
        get_idempotency_keys_collection,
        get_tool_audit_log_collection,
    )

    # Users
    users_col = get_users_collection()
    await users_col.create_index(
        [("firebase_uid", ASCENDING)], unique=True, background=True
    )
    await users_col.create_index([("email", ASCENDING)], unique=True, background=True)

    # Sessions
    sessions_col = get_sessions_collection()
    await sessions_col.create_index(
        [("session_id", ASCENDING)], unique=True, background=True
    )
    await sessions_col.create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)], background=True
    )

    # Custom agents
    agents_col = get_custom_agents_collection()
    await agents_col.create_index(
        [("agent_id", ASCENDING)], unique=True, background=True
    )
    await agents_col.create_index(
        [("owner_user_id", ASCENDING), ("created_at", DESCENDING)], background=True
    )

    # OAuth credentials
    creds_col = get_oauth_credentials_collection()
    await creds_col.create_index(
        [("user_id", ASCENDING), ("provider", ASCENDING)], unique=True, background=True
    )

    # Service credentials (API keys for external services)
    from app.infrastructure.database import get_service_credentials_collection

    svc_creds_col = get_service_credentials_collection()
    await svc_creds_col.create_index(
        [("user_id", ASCENDING), ("service", ASCENDING)], unique=True, background=True
    )

    # OAuth states (efímero, TTL)
    states_col = get_oauth_states_collection()
    await states_col.create_index([("state", ASCENDING)], unique=True, background=True)
    await states_col.create_index(
        [("created_at", ASCENDING)], expireAfterSeconds=600, background=True
    )  # 10 min TTL

    # Contacts whitelist
    contacts_col = get_contacts_collection()
    await contacts_col.create_index(
        [("user_id", ASCENDING), ("type", ASCENDING), ("value", ASCENDING)],
        unique=True,
        background=True,
    )

    # Agent overrides
    overrides_col = get_user_agent_overrides_collection()
    await overrides_col.create_index(
        [("user_id", ASCENDING), ("agent_role", ASCENDING)],
        unique=True,
        background=True,
    )

    # Idempotency keys (TTL 24h)
    idem_col = get_idempotency_keys_collection()
    await idem_col.create_index(
        [("user_id", ASCENDING), ("idempotency_key", ASCENDING)],
        unique=True,
        background=True,
    )
    await idem_col.create_index(
        [("created_at", ASCENDING)], expireAfterSeconds=86400, background=True
    )

    # Knowledge base
    kb_col = db.get_async_db()["knowledge_base"]
    await kb_col.create_index([("agent_target", ASCENDING)], background=True)
    await kb_col.create_index([("source_file_id", ASCENDING)], background=True)
    await kb_col.create_index(
        [("user_id", ASCENDING), ("agent_target", ASCENDING)], background=True
    )

    # Message ratings
    ratings_col = db.get_async_db()["message_ratings"]
    await ratings_col.create_index(
        [("user_id", ASCENDING), ("session_id", ASCENDING), ("message_id", ASCENDING)],
        unique=True,
        background=True,
    )

    # Agent tasks
    tasks_col = db.get_async_db()["agent_tasks"]
    await tasks_col.create_index([("task_id", ASCENDING)], unique=True, background=True)
    await tasks_col.create_index(
        [("assigned_to", ASCENDING), ("status", ASCENDING)], background=True
    )
    await tasks_col.create_index(
        [("owner_user_id", ASCENDING), ("status", ASCENDING), ("priority", ASCENDING)],
        background=True,
    )

    # Tool audit log
    audit_col = get_tool_audit_log_collection()
    await audit_col.create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)], background=True
    )

    logger.info("Índices de MongoDB verificados/creados")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación multi-tenant."""
    # Startup
    logger.info("Iniciando SPHERE Backend (multi-tenant)...")
    _validate_env_vars()

    try:
        db.connect()
        logger.info("Conexión a MongoDB establecida")
        await _ensure_indexes()
    except Exception as e:
        logger.critical(f"No se pudo conectar a MongoDB: {e}")
        raise

    # Firebase Auth
    from app.core.auth import init_firebase

    init_firebase()

    # Redis + FastAPI Limiter
    from app.infrastructure.redis_client import get_redis

    redis_client = await get_redis()
    if redis_client:
        try:
            from fastapi_limiter.callback import default_callback
            from fastapi_limiter.identifier import default_identifier

            # Store redis client globally for rate limiter dependencies
            import app.infrastructure.redis_client as rc_module

            rc_module._redis_client = redis_client
            logger.info("FastAPILimiter inicializado (rate limiting activo)")
        except Exception as e:
            logger.warning(f"No se pudo inicializar rate limiter: {e}")
    else:
        logger.warning("Redis no disponible - rate limiting DESACTIVADO")

    # N8N Client
    client = N8NClient(
        base_url=settings.N8N_BASE_URL,
        webhook_secret=settings.N8N_WEBHOOK_SECRET,
    )
    await client.start()
    n8n_module.n8n_client = client
    logger.info("N8N Client inicializado")

    # Deploy n8n workflows automatically
    from app.infrastructure.n8n_deployer import deploy_all_workflows

    await deploy_all_workflows()

    # Cargar herramientas
    from app.infrastructure.tools.registry import load_all_tools

    load_all_tools()
    logger.info("Tool registry cargado")

    yield  # La aplicación corre aquí

    # Shutdown
    logger.info("Cerrando SPHERE Backend...")
    await client.close()

    # Cerrar Redis si existe
    from app.infrastructure.redis_client import close_redis

    await close_redis()

    db.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS — orígenes explícitos
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)


# Security headers middleware — Pure ASGI (evita BaseHTTPMiddleware + Motor event loop issues)
class SecurityHeadersMiddleware:
    """Inyecta headers de seguridad en todas las respuestas."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-content-type-options", b"nosniff"))
                headers.append((b"x-frame-options", b"DENY"))
                headers.append((b"referrer-policy", b"strict-origin-when-cross-origin"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)


app.add_middleware(SecurityHeadersMiddleware)


# Rate limiters — se activan solo si Redis está disponible.
# Si Redis no está disponible al arranque, estos dependencies no bloquean.
def _optional_rate_limiter(times: int, seconds: int):
    """Construye un Depends(RateLimiter) que solo rate-limitea si Redis
    está disponible. En modo dev sin Redis, pasa transparentemente."""
    from fastapi import Response as FastAPIResponse

    async def _dep(request: Request, response: FastAPIResponse):
        from app.infrastructure.redis_client import _redis_client

        if _redis_client is None:
            return
        from pyrate_limiter import Limiter, Rate, Duration
        from fastapi_limiter.depends import RateLimiter

        rate = Rate(times, Duration.SECOND * seconds)
        limiter = Limiter(rate)
        rl = RateLimiter(limiter=limiter, identifier=user_or_ip_identifier)
        await rl(request, response)

    return Depends(_dep)


# Rutas
app.include_router(
    health.router, prefix=f"{settings.API_V1_STR}/health", tags=["Health"]
)
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}", tags=["Auth"])

# Stream: sin rate limiter a nivel router — se aplica per-plan dentro del handler
# después de resolver el usuario (única forma de saber el plan).
app.include_router(
    stream.router,
    prefix=f"{settings.API_V1_STR}/stream",
    tags=["Stream"],
)

# Otros routers: rate limit general por usuario
_general_limit = _optional_rate_limiter(settings.RATE_LIMIT_REQUESTS_PER_MINUTE, 60)
app.include_router(
    sessions.router,
    prefix=f"{settings.API_V1_STR}/sessions",
    tags=["Sessions"],
    dependencies=[_general_limit],
)
app.include_router(
    agents.router,
    prefix=f"{settings.API_V1_STR}/agents",
    tags=["Agents"],
    dependencies=[_general_limit],
)
app.include_router(
    documents.router,
    prefix=f"{settings.API_V1_STR}/agents",
    tags=["Documents"],
    dependencies=[_general_limit],
)
app.include_router(
    integrations.router,
    prefix=f"{settings.API_V1_STR}/integrations",
    tags=["Integrations"],
    dependencies=[_general_limit],
)
app.include_router(
    billing.router,
    prefix=f"{settings.API_V1_STR}/billing",
    tags=["Billing"],
    dependencies=[_general_limit],
)
# Webhooks publicos, sin rate limit general ni prefijo de /v1 por defecto si no lo deseas, 
# pero mantendremos el patrón.
app.include_router(
    webhooks.router,
    prefix=f"{settings.API_V1_STR}/webhooks",
    tags=["Webhooks"],
)


@app.get("/")
async def root():
    """Endpoint raíz."""
    return {
        "service": "SPHERE Backend",
        "version": "3.0-multi-tenant",
        "docs": f"{settings.API_V1_STR}/openapi.json",
    }
