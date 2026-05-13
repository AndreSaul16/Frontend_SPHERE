"""
API de integraciones OAuth (GitHub, Notion, Slack).
Maneja el flujo OAuth completo: authorize → callback → list → revoke.
"""
import hmac
import hashlib
import time
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.credentials import credentials_service
from app.infrastructure.database import get_oauth_states_collection
from app.core.logger import api_logger as logger

router = APIRouter()

# Providers soportados
PROVIDERS = {
    "github": __import__("app.infrastructure.integrations.providers.github", fromlist=["github"]),
    "notion": __import__("app.infrastructure.integrations.providers.notion", fromlist=["notion"]),
    "slack": __import__("app.infrastructure.integrations.providers.slack", fromlist=["slack"]),
}


def _generate_state(user_id: str) -> str:
    """Genera un state CSRF firmado con HMAC + user_id."""
    nonce = secrets.token_urlsafe(32)
    timestamp = str(int(time.time()))
    payload = f"{user_id}:{nonce}:{timestamp}"
    signature = hmac.new(
        settings.N8N_WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    return f"{nonce}:{timestamp}:{signature}"


def _verify_state(state: str, user_id: str) -> bool:
    """Verifica que el state no fue manipulado."""
    try:
        parts = state.split(":")
        if len(parts) != 3:
            return False
        nonce, timestamp, received_sig = parts
        payload = f"{user_id}:{nonce}:{timestamp}"
        expected_sig = hmac.new(
            settings.N8N_WEBHOOK_SECRET.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
        # Verificar firma + expiración (10 min)
        if not hmac.compare_digest(received_sig, expected_sig):
            return False
        if int(time.time()) - int(timestamp) > 600:
            return False
        return True
    except (ValueError, IndexError):
        return False


@router.get("/{provider}/connect")
async def connect_provider(
    provider: str,
    user: dict = Depends(get_current_user),
):
    """
    Inicia el flujo OAuth para un provider.
    Redirige al usuario a la página de autorización del provider.
    """
    if provider not in PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' no soportado. Usa: {', '.join(PROVIDERS.keys())}"
        )

    user_id = user["firebase_uid"]
    state = _generate_state(user_id)

    # Guardar state en DB para verificación en callback
    states_col = get_oauth_states_collection()
    await states_col.insert_one({
        "state": state,
        "user_id": user_id,
        "provider": provider,
        "created_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
    })

    provider_module = PROVIDERS[provider]
    auth_url = provider_module.authorize_url(state)

    logger.info(f"Iniciando OAuth {provider} para user {user_id}")
    return {"authorize_url": auth_url}


@router.get("/{provider}/callback")
async def provider_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
):
    """
    Callback del provider OAuth.
    Intercambia el code por tokens y los almacena cifrados.
    """
    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail="Provider no soportado")

    # Verificar state en DB
    states_col = get_oauth_states_collection()
    state_doc = await states_col.find_one_and_delete({"state": state})

    if not state_doc:
        logger.warning(f"State OAuth inválido o ya usado: {state[:20]}...")
        raise HTTPException(status_code=400, detail="State inválido o expirado")

    user_id = state_doc["user_id"]

    # Verificar que el state no fue manipulado
    if not _verify_state(state, user_id):
        raise HTTPException(status_code=400, detail="State inválido")

    # Intercambiar code por tokens
    try:
        provider_module = PROVIDERS[provider]
        token_data = await provider_module.exchange_code(code)

        await credentials_service.store_token(
            user_id=user_id,
            provider=provider,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            scopes=token_data.get("scopes"),
            expires_in=token_data.get("expires_in"),
        )

        logger.info(f"OAuth {provider} completado para user {user_id}")

        # Redirigir al frontend
        frontend_url = settings.ALLOWED_ORIGINS.split(",")[0].strip()
        return RedirectResponse(
            url=f"{frontend_url}/settings/integrations?connected={provider}",
            status_code=302,
        )

    except Exception as e:
        logger.error(f"Error en callback OAuth {provider}: {e}")
        raise HTTPException(status_code=500, detail="Error completando autorización")


@router.get("/")
async def list_integrations(user: dict = Depends(get_current_user)):
    """Lista los providers conectados del usuario."""
    user_id = user["firebase_uid"]
    connected = await credentials_service.list_connected(user_id)

    # Devolver estado de todos los providers
    all_providers = {}
    for p in PROVIDERS:
        all_providers[p] = any(c["provider"] == p for c in connected)

    return {
        "connected": connected,
        "available": list(PROVIDERS.keys()),
        "status": all_providers,
    }


@router.delete("/{provider}")
async def disconnect_provider(
    provider: str,
    user: dict = Depends(get_current_user),
):
    """Desconecta un provider OAuth."""
    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail="Provider no soportado")

    user_id = user["firebase_uid"]
    revoked = await credentials_service.revoke(user_id, provider)

    if not revoked:
        raise HTTPException(
            status_code=404,
            detail=f"{provider} no estaba conectado"
        )

    logger.info(f"Provider {provider} desconectado para user {user_id}")
    return {"status": "disconnected", "provider": provider}
