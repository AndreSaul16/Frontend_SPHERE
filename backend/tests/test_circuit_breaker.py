"""
Tests del circuit breaker.
Usa fakeredis para simular Redis en tests.
"""
import pytest
from unittest.mock import patch, AsyncMock
import fakeredis.aioredis


@pytest.fixture(autouse=True)
async def mock_redis():
    """Provee un fakeredis para todos los tests de circuit breaker."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    with patch("app.core.circuit_breaker.get_redis", return_value=fake):
        yield fake
    await fake.aclose()


from app.core.circuit_breaker import CircuitBreaker, CircuitState, CircuitOpenError


@pytest.mark.asyncio
async def test_circuit_starts_closed():
    """Un circuit breaker nuevo empieza en estado CLOSED."""
    cb = CircuitBreaker("test_cb", failure_threshold=3, recovery_timeout=5)
    state, failures = await cb._get_state()
    assert state == CircuitState.CLOSED
    assert failures == 0


@pytest.mark.asyncio
async def test_can_execute_when_closed():
    """En CLOSED, can_execute retorna True."""
    cb = CircuitBreaker("test_cb_closed")
    assert await cb.can_execute() is True


@pytest.mark.asyncio
async def test_failures_accumulate():
    """Los fallos se acumulan sin abrir el circuito bajo el umbral."""
    cb = CircuitBreaker("test_cb_fail", failure_threshold=5, recovery_timeout=10)
    await cb.record_failure()
    await cb.record_failure()
    await cb.record_failure()

    state, failures = await cb._get_state()
    assert state == CircuitState.CLOSED
    assert failures == 3


@pytest.mark.asyncio
async def test_circuit_opens_at_threshold():
    """Al alcanzar el umbral, el circuito se abre."""
    cb = CircuitBreaker("test_cb_open", failure_threshold=3, recovery_timeout=10)
    await cb.record_failure()
    await cb.record_failure()
    await cb.record_failure()

    state, _ = await cb._get_state()
    assert state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_cannot_execute_when_open():
    """En OPEN, can_execute retorna False."""
    cb = CircuitBreaker("test_cb_noexec", failure_threshold=1, recovery_timeout=60)
    await cb.record_failure()  # Abre el circuito

    assert await cb.can_execute() is False


@pytest.mark.asyncio
async def test_execute_raises_when_open():
    """execute() lanza CircuitOpenError si el circuito está abierto."""
    cb = CircuitBreaker("test_cb_raise", failure_threshold=1, recovery_timeout=60)
    await cb.record_failure()

    async def dummy():
        return "ok"

    with pytest.raises(CircuitOpenError):
        await cb.execute(dummy)


@pytest.mark.asyncio
async def test_success_resets_failures():
    """Un éxito en CLOSED resetea el contador de fallos."""
    cb = CircuitBreaker("test_cb_reset", failure_threshold=5, recovery_timeout=10)
    await cb.record_failure()
    await cb.record_failure()
    await cb.record_success()

    state, failures = await cb._get_state()
    assert state == CircuitState.CLOSED
    assert failures == 0
