"""
Cliente atómico para Notion API.
"""
import httpx
from app.core.logger import checkpoint_logger as logger

NOTION_API = "https://api.notion.com/v1"


async def create_page(access_token: str, parent_id: str, title: str, content: str = "") -> dict:
    """Crea una página en Notion."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{NOTION_API}/pages",
            json={
                "parent": {"page_id": parent_id},
                "properties": {
                    "title": {
                        "title": [{"text": {"content": title}}]
                    }
                },
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": content}}]
                        }
                    }
                ] if content else [],
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return {"url": data.get("url", ""), "id": data["id"]}


async def update_page(access_token: str, page_id: str, content: str) -> dict:
    """Agrega contenido a una página existente."""
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            f"{NOTION_API}/blocks/{page_id}/children",
            json={
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": content}}]
                        }
                    }
                ]
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        return {"status": "updated"}
