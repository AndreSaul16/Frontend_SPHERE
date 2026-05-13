"""
Helper para inyectar credenciales de usuario en payloads de n8n.
Carga las credenciales cifradas de MongoDB, las descifra, y las prepara
para inyección en los webhooks de n8n.
"""

from typing import Optional
from app.core.credentials import credentials_service
from app.core.tool_context import get_current_user_id
from app.core.logger import checkpoint_logger as logger


# Map de servicios a sus credenciales requeridas
SERVICE_CREDENTIAL_MAP = {
    "calendar": ["google_calendar"],
    "whatsapp": ["whatsapp"],
    "linkedin": ["linkedin"],
    "instagram": ["instagram"],
    "jules": ["jules"],
}


async def load_user_credentials_for_services(
    user_id: str,
    services: list[str],
) -> dict:
    """
    Carga credenciales de múltiples servicios para un usuario.

    Args:
        user_id: Firebase UID del usuario
        services: Lista de servicios necesarios (ej: ["calendar", "whatsapp"])

    Returns:
        dict con credenciales descifradas listas para n8n:
        {
            "google_calendar": {"api_key": "...", "calendar_id": "primary"},
            "whatsapp": {"api_key": "...", "phone_number_id": "123"},
        }
    """
    if not user_id:
        return {}

    # Resolve service names to credential keys
    credential_keys = []
    for service in services:
        credential_keys.extend(SERVICE_CREDENTIAL_MAP.get(service, [service]))

    # Load credentials
    try:
        creds = await credentials_service.load_credentials_for_n8n(
            user_id, credential_keys
        )
        return creds
    except Exception as e:
        logger.warning(f"Error loading credentials for user {user_id}: {e}")
        return {}


async def inject_credentials_into_payload(
    payload: dict,
    services: list[str],
) -> tuple[dict, dict]:
    """
    Carga credenciales del usuario actual y las prepara para inyección.

    Args:
        payload: Payload original del webhook
        services: Servicios necesarios

    Returns:
        Tuple de (payload, credentials) donde credentials es el dict para n8n
    """
    user_id = get_current_user_id()
    if not user_id:
        return payload, {}

    credentials = await load_user_credentials_for_services(user_id, services)
    return payload, credentials


def get_required_services(webhook_path: str) -> list[str]:
    """
    Determina qué servicios necesita un webhook basado en su path.

    Args:
        webhook_path: Path del webhook (ej: "shared/calendar-list")

    Returns:
        Lista de servicios necesarios (ej: ["google_calendar"])
    """
    if "calendar" in webhook_path:
        return ["google_calendar"]
    elif "whatsapp" in webhook_path:
        return ["whatsapp"]
    elif "linkedin" in webhook_path:
        return ["linkedin"]
    elif "instagram" in webhook_path:
        return ["instagram"]
    elif "jules" in webhook_path:
        return ["jules"]
    return []
