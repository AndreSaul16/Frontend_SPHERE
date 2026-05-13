"""
Unit tests para app.infrastructure.redis_client.
Cubre: singleton, degradación graceful, ciclo de vida connect/close.
"""
import pytest
from unittest.mock import AsyncMock, patch
import app.infrastructure.redis_client as rc


@pytest.fixture(autouse=True)
async def reset_singleton():
    """Resetea el singleton entre tests para garantizar aislamiento."""
    rc._redis_client = None
    yield
    if rc._redis_client:
        try:
            await rc._redis_client.aclose()
        except Exception:
            pass
    rc._redis_client = None


async def test_get_redis_returns_none_when_unreachable():
    """Si el ping falla (Redis caído), get_redis devuelve None sin lanzar."""
    mock_client = AsyncMock()
    mock_client.ping.side_effect = ConnectionError("Connection refused")

    with patch("app.infrastructure.redis_client.redis.from_url", return_value=mock_client):
        result = await rc.get_redis()

    assert result is None


async def test_get_redis_returns_client_when_available():
    """Si el ping responde, get_redis devuelve el cliente configurado."""
    mock_client = AsyncMock()
    mock_client.ping.return_value = True

    with patch("app.infrastructure.redis_client.redis.from_url", return_value=mock_client):
        result = await rc.get_redis()

    assert result is mock_client
    mock_client.ping.assert_called_once()


async def test_get_redis_is_singleton():
    """Dos llamadas consecutivas devuelven la misma instancia sin reconectar."""
    mock_client = AsyncMock()
    mock_client.ping.return_value = True

    with patch("app.infrastructure.redis_client.redis.from_url", return_value=mock_client):
        first = await rc.get_redis()
        second = await rc.get_redis()

    assert first is second
    assert mock_client.ping.call_count == 1


async def test_close_redis_resets_singleton():
    """close_redis llama aclose() y deja el singleton en None."""
    mock_client = AsyncMock()
    mock_client.ping.return_value = True

    with patch("app.infrastructure.redis_client.redis.from_url", return_value=mock_client):
        await rc.get_redis()

    assert rc._redis_client is not None
    await rc.close_redis()

    assert rc._redis_client is None
    mock_client.aclose.assert_called_once()


async def test_close_redis_noop_when_not_connected():
    """close_redis no lanza si no hay conexión activa."""
    assert rc._redis_client is None
    await rc.close_redis()


async def test_get_redis_reconnects_after_close():
    """Tras close_redis, la siguiente llamada crea una nueva conexión."""
    mock_client = AsyncMock()
    mock_client.ping.return_value = True

    with patch("app.infrastructure.redis_client.redis.from_url", return_value=mock_client):
        await rc.get_redis()
        await rc.close_redis()
        await rc.get_redis()

    assert mock_client.ping.call_count == 2


async def test_get_redis_caches_none_on_failure():
    """Tras un fallo, el singleton queda en None (no queda cliente roto cacheado)."""
    mock_client = AsyncMock()
    mock_client.ping.side_effect = OSError("timeout")

    with patch("app.infrastructure.redis_client.redis.from_url", return_value=mock_client):
        result = await rc.get_redis()

    assert result is None
    assert rc._redis_client is None
