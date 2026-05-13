"""
Tests del distributed lock.
"""
import pytest
from unittest.mock import patch, AsyncMock
from app.core.distributed_lock import DistributedLock


@pytest.mark.asyncio
async def test_lock_acquires_when_no_redis():
    """Sin Redis, acquire retorna True (degradación graceful)."""
    with patch("app.core.distributed_lock.get_redis", return_value=None):
        lock = DistributedLock("test:lock")
        result = await lock.acquire()
        assert result is True


@pytest.mark.asyncio
async def test_lock_acquires_successfully():
    """Con Redis disponible, lock se adquiere."""
    mock_redis = AsyncMock()
    mock_redis.set.return_value = True

    with patch("app.core.distributed_lock.get_redis", return_value=mock_redis):
        lock = DistributedLock("test:lock:1", ttl_seconds=30)
        result = await lock.acquire()
        assert result is True
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_lock_fails_when_already_held():
    """Si el lock ya está tomado, acquire retorna False."""
    mock_redis = AsyncMock()
    mock_redis.set.return_value = None  # NX falló

    with patch("app.core.distributed_lock.get_redis", return_value=mock_redis):
        lock = DistributedLock("test:lock:held")
        result = await lock.acquire()
        assert result is False


@pytest.mark.asyncio
async def test_lock_context_manager():
    """DistributedLock funciona como context manager."""
    mock_redis = AsyncMock()
    mock_redis.set.return_value = True
    mock_redis.eval = AsyncMock()

    with patch("app.core.distributed_lock.get_redis", return_value=mock_redis):
        async with DistributedLock("test:ctx") as acquired:
            assert acquired is True
