"""OAuth provider para Slack (BYO: client_id/secret vienen del usuario)."""
import httpx

# Scopes fijos para SPHERE (no los elige el usuario).
DEFAULT_SCOPES = "chat:write,channels:read"


def authorize_url(
    state: str, client_id: str, redirect_uri: str, scopes: str = DEFAULT_SCOPES
) -> str:
    """Genera la URL de autorización de Slack OAuth."""
    return (
        f"https://slack.com/oauth/v2/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scopes}"
        f"&state={state}"
    )


async def exchange_code(
    code: str, client_id: str, client_secret: str, redirect_uri: str
) -> dict:
    """Intercambia el code de autorización por tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
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


async def revoke(token: str, client_id: str = "", client_secret: str = ""):
    """Revoca un token de Slack."""
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://slack.com/api/auth.revoke",
            data={"token": token},
        )
