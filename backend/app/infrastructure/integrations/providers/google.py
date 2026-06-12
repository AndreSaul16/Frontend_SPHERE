"""OAuth provider para Google (Calendar/Gmail). BYO: client_id/secret del usuario.

Google Calendar API NO acepta una API key para operar sobre el calendario del
usuario: requiere un access_token OAuth2. Por eso Calendar se conecta vía OAuth
(no como service-credential api_key). El token se auto-refresca (access_type=offline).
"""
from urllib.parse import urlencode

import httpx

# Scope de calendario completo (crear/listar/editar/borrar eventos + disponibilidad).
DEFAULT_SCOPES = "https://www.googleapis.com/auth/calendar"


def authorize_url(
    state: str, client_id: str, redirect_uri: str, scopes: str = DEFAULT_SCOPES
) -> str:
    """URL de autorización de Google OAuth 2.0.

    access_type=offline + prompt=consent son imprescindibles para obtener un
    refresh_token (si no, Google solo lo emite la primera vez)."""
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scopes,
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


async def exchange_code(
    code: str, client_id: str, client_secret: str, redirect_uri: str
) -> dict:
    """Intercambia el code por tokens (access + refresh)."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise ValueError(
                f"Google OAuth error: {data.get('error_description', data['error'])}"
            )
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token"),
            "scopes": (data.get("scope", "") or "").split(" "),
            "expires_in": data.get("expires_in"),
        }


async def revoke(token: str, client_id: str = "", client_secret: str = ""):
    """Revoca el token en Google."""
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": token},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
