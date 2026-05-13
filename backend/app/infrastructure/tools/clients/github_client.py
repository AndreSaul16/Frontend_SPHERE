"""
Cliente atómico para GitHub API.
Operaciones directas sin pasar por n8n.
"""
import httpx
from app.core.logger import checkpoint_logger as logger

GITHUB_API = "https://api.github.com"


async def create_repo(access_token: str, name: str, private: bool = True, description: str = "") -> dict:
    """Crea un repositorio en la cuenta del usuario."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GITHUB_API}/user/repos",
            json={
                "name": name,
                "private": private,
                "description": description,
                "auto_init": True,
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"Repo creado: {data.get('full_name')}")
        return {"url": data["html_url"], "name": data["full_name"]}


async def create_issue(access_token: str, owner: str, repo: str, title: str, body: str = "") -> dict:
    """Crea un issue en un repositorio."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues",
            json={"title": title, "body": body},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return {"url": data["html_url"], "number": data["number"]}


async def create_pr_comment(access_token: str, owner: str, repo: str, pr_number: int, body: str) -> dict:
    """Crea un comentario en un Pull Request."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues/{pr_number}/comments",
            json={"body": body},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        return {"status": "commented"}
