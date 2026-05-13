"""
Cliente Redis singleton para rate limiting y distributed locks.
"""
import redis.asyncio as redis
from app.core.config import settings
from app.core.logger import api_logger as logger

_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Obtiene el cliente Redis singleton."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            # Verificar conexión
            await _redis_client.ping()
            logger.info("Redis conectado correctamente")
        except Exception as e:
            logger.warning(f"Redis no disponible: {e}. Rate limiting deshabilitado.")
            _redis_client = None
    return _redis_client


async def close_redis():
    """Cierra la conexión Redis."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis desconectado")
