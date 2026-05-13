"""
Sistema central de errores estructurados.

Toda HTTPException debería usar `app_error(code, status, message, **details)`
o uno de los helpers (`auth_error`, `billing_error`, etc.) para que el
frontend reciba un cuerpo JSON consistente:

    {
        "error": "billing.insufficient_credits",   # machine-readable
        "message": "Has agotado tus mensajes...",  # humano
        "details": { "plan_id": "free", ... }      # contexto
    }

Esto permite:
- Frontend mapea código -> acción (paywall, redirect, etc.) sin parsear strings.
- Logs/Sentry agrupan por código.
- i18n: frontend traduce según código.
- Cuando algo falla en producción, ves el código en logs y sabes dónde mirar.

Convención de códigos: `<dominio>.<accion_o_estado>` en snake_case.
"""
from enum import Enum
from typing import Any

from fastapi import HTTPException


class ErrorCode(str, Enum):
    # --- Auth (401, 403) ---
    AUTH_MISSING_TOKEN = "auth.missing_token"
    AUTH_INVALID_TOKEN = "auth.invalid_token"
    AUTH_EXPIRED_TOKEN = "auth.expired_token"
    AUTH_USER_DISABLED = "auth.user_disabled"

    # --- Permisos / tenancy (403, 404) ---
    PERM_NOT_OWNER = "perm.not_owner"
    PERM_PLAN_NOT_ALLOWED = "perm.plan_not_allowed"

    # --- Billing (402, 403, 404, 409) ---
    BILLING_INSUFFICIENT_CREDITS = "billing.insufficient_credits"
    BILLING_INVALID_PLAN = "billing.invalid_plan"
    BILLING_STRIPE_ERROR = "billing.stripe_error"
    BILLING_NO_CUSTOMER = "billing.no_customer"
    BILLING_WEBHOOK_INVALID_SIGNATURE = "billing.webhook_invalid_signature"
    BILLING_WEBHOOK_INVALID_PAYLOAD = "billing.webhook_invalid_payload"
    BILLING_TOPUP_NOT_ALLOWED = "billing.topup_not_allowed"

    # --- RAG / documentos (400, 403, 413) ---
    RAG_QUOTA_EXCEEDED = "rag.quota_exceeded"
    RAG_FILE_TOO_LARGE = "rag.file_too_large"
    RAG_FILE_TYPE_UNSUPPORTED = "rag.file_type_unsupported"
    RAG_FILE_EMPTY = "rag.file_empty"
    RAG_AGENT_FILES_LIMIT = "rag.agent_files_limit"
    RAG_DOC_NOT_FOUND = "rag.doc_not_found"

    # --- Agentes (403, 404) ---
    AGENTS_QUOTA_EXCEEDED = "agents.quota_exceeded"
    AGENTS_NOT_FOUND = "agents.not_found"
    AGENTS_INVALID_MODEL = "agents.invalid_model"

    # --- LLM / orquestador (502, 504) ---
    LLM_UPSTREAM_ERROR = "llm.upstream_error"
    LLM_TIMEOUT = "llm.timeout"
    LLM_CONTEXT_TOO_LONG = "llm.context_too_long"

    # --- Sessions (404, 409) ---
    SESSION_NOT_FOUND = "session.not_found"
    SESSION_LOCKED = "session.locked"

    # --- Tools (400, 403, 502) ---
    TOOL_NOT_AUTHORIZED = "tool.not_authorized"
    TOOL_INVALID_ARGS = "tool.invalid_args"
    TOOL_UPSTREAM_ERROR = "tool.upstream_error"

    # --- Genéricos (400, 500) ---
    BAD_REQUEST = "common.bad_request"
    INTERNAL_ERROR = "common.internal_error"
    RATE_LIMITED = "common.rate_limited"


def app_error(
    code: ErrorCode | str,
    status_code: int,
    message: str,
    **details: Any,
) -> HTTPException:
    """
    Construye HTTPException con detail estructurado.

    Uso:
        raise app_error(
            ErrorCode.BILLING_INSUFFICIENT_CREDITS,
            402,
            "Has agotado tus mensajes.",
            plan_id="free",
        )
    """
    code_str = code.value if isinstance(code, ErrorCode) else str(code)
    return HTTPException(
        status_code=status_code,
        detail={
            "error": code_str,
            "message": message,
            "details": details,
        },
    )


# --- Helpers por dominio (azúcar sintáctico) ---

def billing_error(code: ErrorCode, status: int, message: str, **details) -> HTTPException:
    return app_error(code, status, message, **details)


def rag_error(code: ErrorCode, status: int, message: str, **details) -> HTTPException:
    return app_error(code, status, message, **details)


def agents_error(code: ErrorCode, status: int, message: str, **details) -> HTTPException:
    return app_error(code, status, message, **details)


def auth_error(code: ErrorCode, status: int, message: str, **details) -> HTTPException:
    return app_error(code, status, message, **details)
