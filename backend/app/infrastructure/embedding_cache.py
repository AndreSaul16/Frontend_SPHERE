"""
Caché semántico de embeddings con Redis.
Evita llamadas redundantes a OpenAI para queries similares.
"""
import hashlib
from typing import Optional

from app.infrastructure.redis_client import get_redis
from app.core.logger import db_logger as logger


async def get_cached_embedding(query: str, model: str = "text-embedding-3-small") -> Optional[list[float]]:
    """
    Busca un embedding en cache por hash del query normalizado.
    
    Returns:
        Lista de floats si hay hit, None si hay miss.
    """
    redis_client = await get_redis()
    if not redis_client:
        return None

    try:
        cache_key = _cache_key(query, model)
        cached = await redis_client.get(cache_key)
        if cached:
            import json
            return json.loads(cached)
    except Exception as e:
        logger.debug(f"Cache miss (error): {e}")

    return None


async def set_cached_embedding(
    query: str,
    embedding: list[float],
    model: str = "text-embedding-3-small",
    ttl_hours: int = 24,
):
    """Guarda un embedding en cache con TTL."""
    redis_client = await get_redis()
    if not redis_client:
        return

    try:
        cache_key = _cache_key(query, model)
        import json
        await redis_client.setex(
            cache_key,
            ttl_hours * 3600,
            json.dumps(embedding),
        )
    except Exception as e:
        logger.debug(f"Cache set error: {e}")


def _cache_key(query: str, model: str) -> str:
    """Genera una key de cache determinística."""
    normalized = query.strip().lower()
    hash_val = hashlib.sha256(f"{normalized}:{model}".encode()).hexdigest()[:16]
    return f"embedding:{hash_val}"
