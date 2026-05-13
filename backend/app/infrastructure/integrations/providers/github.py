"""OAuth provider para GitHub."""
from app.core.config import settings


def authorize_url(state: str) -> str:
    """Genera la URL de autorización de GitHub OAuth."""
    scopes = "repo,read:user"
    return (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.OAUTH_REDIRECT_BASE_URL}/github/callback"
        f"&scope={scopes}"
        f"&state={state}"
    )


async def exchange_code(code: str) -> dict:
    """Intercambia el code de autorización por tokens."""
    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{settings.OAUTH_REDIRECT_BASE_URL}/github/callback",
            },
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            raise ValueError(f"GitHub OAuth error: {data.get('error_description', data['error'])}")

        return {
            "access_token": data["access_token"],
            "refresh_token": None,  # GitHub OAuth App tokens no expiran
            "scopes": data.get("scope", "").split(","),
            "expires_in": None,
        }


async def revoke(token: str):
    """Revoca un token de GitHub."""
    import httpx

    async with httpx.AsyncClient() as client:
        await client.delete(
            f"https://api.github.com/applications/{settings.GITHUB_CLIENT_ID}/token",
            json={"access_token": token},
            auth=(settings.GITHUB_CLIENT_ID, settings.GITHUB_CLIENT_SECRET),
        )
