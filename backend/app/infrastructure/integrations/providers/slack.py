"""OAuth provider para Slack."""
from app.core.config import settings


SCOPES = "chat:write,channels:read"


def authorize_url(state: str) -> str:
    """Genera la URL de autorización de Slack OAuth."""
    return (
        f"https://slack.com/oauth/v2/authorize"
        f"?client_id={settings.SLACK_CLIENT_ID}"
        f"&redirect_uri={settings.OAUTH_REDIRECT_BASE_URL}/slack/callback"
        f"&scope={SCOPES}"
        f"&state={state}"
    )


async def exchange_code(code: str) -> dict:
    """Intercambia el code de autorización por tokens."""
    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "client_id": settings.SLACK_CLIENT_ID,
                "client_secret": settings.SLACK_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{settings.OAUTH_REDIRECT_BASE_URL}/slack/callback",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        if not data.get("ok"):
            raise ValueError(f"Slack OAuth error: {data.get('error', 'unknown')}")

        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token"),
            "scopes": data.get("scope", "").split(","),
            "expires_in": data.get("expires_in"),
        }


async def revoke(token: str):
    """Revoca un token de Slack."""
    import httpx

    async with httpx.AsyncClient() as client:
        await client.post(
            "https://slack.com/api/auth.revoke",
            data={"token": token},
        )
