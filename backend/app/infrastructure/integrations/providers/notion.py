"""OAuth provider para Notion."""
from app.core.config import settings


def authorize_url(state: str) -> str:
    """Genera la URL de autorización de Notion OAuth."""
    return (
        f"https://api.notion.com/v1/oauth/authorize"
        f"?client_id={settings.NOTION_CLIENT_ID}"
        f"&redirect_uri={settings.OAUTH_REDIRECT_BASE_URL}/notion/callback"
        f"&response_type=code"
        f"&owner=user"
        f"&state={state}"
    )


async def exchange_code(code: str) -> dict:
    """Intercambia el code de autorización por tokens."""
    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.notion.com/v1/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{settings.OAUTH_REDIRECT_BASE_URL}/notion/callback",
            },
            auth=(settings.NOTION_CLIENT_ID, settings.NOTION_CLIENT_SECRET),
        )
        resp.raise_for_status()
        data = resp.json()

        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token"),
            "scopes": [],  # Notion no devuelve scopes en el token response
            "expires_in": data.get("expires_in"),
        }


async def revoke(token: str):
    """Notion no tiene endpoint de revocación pública."""
    pass
