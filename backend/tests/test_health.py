"""
Tests para el endpoint de Health.
Verifica que el health check funciona correctamente.
"""
import pytest
import time


class TestHealthEndpoint:
    """Tests para /api/v1/health/"""

    @pytest.mark.asyncio
    async def test_health_check_success(self, async_client):
        """Test: Health check devuelve estado correcto."""
        response = await async_client.get("/api/v1/health/health")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["service"] == "SPHERE Orchestrator"
        
        print(f"\n🏥 Health Check:")
        print(f"   Status: {data['status']}")
        print(f"   Checks: {data.get('checks', {})}")

    @pytest.mark.asyncio
    async def test_health_check_has_version(self, async_client):
        """Test: Health check incluye información de versión."""
        response = await async_client.get("/api/v1/health/health")
        
        data = response.json()
        assert "version" in data
        assert data["version"] == "3.0-multi-tenant"

    @pytest.mark.asyncio
    async def test_health_check_has_checks(self, async_client):
        """Test: Health check incluye checks de dependencias."""
        response = await async_client.get("/api/v1/health/health")
        
        data = response.json()
        assert "checks" in data
        assert isinstance(data["checks"], dict)
        # MongoDB check should be present
        assert "mongodb" in data["checks"]

    @pytest.mark.asyncio
    async def test_liveness_probe(self, async_client):
        """Test: Liveness probe devuelve alive."""
        response = await async_client.get("/api/v1/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestDeployEndpoint:
    """Tests para GET /api/v1/health/deploy (deploy-metadata)."""

    @pytest.mark.asyncio
    async def test_deploy_happy_all_vars_set(self, async_client, monkeypatch):
        """SC-DM-HAPPY: Con GIT_COMMIT_SHA y BUILD_TIMESTAMP seteados,
        el endpoint devuelve deploy_status: live."""
        from app.core.config import settings as s

        monkeypatch.setattr(s, "GIT_COMMIT_SHA", "abc123def456")
        monkeypatch.setattr(s, "BUILD_TIMESTAMP", "2026-06-09T12:00:00Z")

        response = await async_client.get("/api/v1/health/deploy")

        assert response.status_code == 200
        data = response.json()
        assert data["commit_sha"] == "abc123def456"
        assert data["build_timestamp"] == "2026-06-09T12:00:00Z"
        assert data["deploy_status"] == "live"
        assert data["service_name"] == "backend"
        assert data["version"] == s.PROJECT_NAME

    @pytest.mark.asyncio
    async def test_deploy_missing_env_vars(self, async_client, monkeypatch):
        """SC-DM-MISSING: Sin GIT_COMMIT_SHA y BUILD_TIMESTAMP,
        el endpoint devuelve deploy_status: deploying y commit_sha: unknown."""
        from app.core.config import settings as s

        monkeypatch.setattr(s, "GIT_COMMIT_SHA", "")
        monkeypatch.setattr(s, "BUILD_TIMESTAMP", "")

        response = await async_client.get("/api/v1/health/deploy")

        assert response.status_code == 200
        data = response.json()
        assert data["commit_sha"] == "unknown"
        assert data["deploy_status"] == "deploying"
        # version should still be present even without deploy vars
        assert data["version"] == s.PROJECT_NAME
        assert data["service_name"] == "backend"

    @pytest.mark.asyncio
    async def test_deploy_no_secret_leak(self, async_client, monkeypatch):
        """SC-DM-SECRETS: La respuesta NUNCA debe contener
        claves sensibles como api_key, secret, token, password."""
        from app.core.config import settings as s

        monkeypatch.setattr(s, "GIT_COMMIT_SHA", "abc123")
        monkeypatch.setattr(s, "BUILD_TIMESTAMP", "2026-06-09T12:00:00Z")
        # El endpoint solo expone lo que devuelve — no debería incluir secretos

        response = await async_client.get("/api/v1/health/deploy")

        assert response.status_code == 200
        data = response.json()
        body_str = str(data).lower()
        # Ninguna clave sensible debe aparecer en la respuesta
        forbidden = ["api_key", "secret", "token", "password", "mongodb_url"]
        for key in forbidden:
            assert key not in body_str, (
                f"Se filtró '{key}' en la respuesta: {data}"
            )

    @pytest.mark.asyncio
    async def test_deploy_response_time_under_50ms(self, async_client, monkeypatch):
        """SC-DM-PERF: La respuesta debe ser rápida (sin DB queries)."""
        from app.core.config import settings as s

        monkeypatch.setattr(s, "GIT_COMMIT_SHA", "abc123")
        monkeypatch.setattr(s, "BUILD_TIMESTAMP", "2026-06-09T12:00:00Z")

        # Warm-up: una llamada para evitar cold-start del cliente HTTP
        await async_client.get("/api/v1/health/deploy")

        # Medir 5 iteraciones
        times = []
        for _ in range(5):
            start = time.perf_counter()
            await async_client.get("/api/v1/health/deploy")
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)

        avg_ms = sum(times) / len(times)
        max_ms = max(times)
        print(f"\n⏱️  Deploy endpoint latency: avg={avg_ms:.2f}ms, max={max_ms:.2f}ms")

        # P99 under 50ms — verificamos que el máximo esté bajo 50ms
        # (con margen para CI environments)
        assert max_ms < 50, (
            f"Deploy endpoint demasiado lento: max={max_ms:.2f}ms (target <50ms)"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
