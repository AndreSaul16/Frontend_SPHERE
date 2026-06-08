"""OAuth provider para GitHub (BYO: client_id/secret vienen del usuario)."""
import httpx

# Scopes fijos para SPHERE (no los elige el usuario).
DEFAULT_SCOPES = "repo,read:user"


def authorize_url(
    state: str, client_id: str, redirect_uri: str, scopes: str = DEFAULT_SCOPES
) -> str:
    """Genera la URL de autorización de GitHub OAuth."""
    return (
        f"https://github.com/login/oauth/authorize"
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
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            raise ValueError(
                f"GitHub OAuth error: {data.get('error_description', data['error'])}"
            )

        return {
            "access_token": data["access_token"],
            "refresh_token": None,  # GitHub OAuth App tokens no expiran
            "scopes": data.get("scope", "").split(","),
            "expires_in": None,
        }


async def revoke(token: str, client_id: str, client_secret: str):
    """Revoca un token de GitHub (requiere las creds de la app del usuario)."""
    async with httpx.AsyncClient() as client:
        await client.delete(
            f"https://api.github.com/applications/{client_id}/token",
            json={"access_token": token},
            auth=(client_id, client_secret),
        )
