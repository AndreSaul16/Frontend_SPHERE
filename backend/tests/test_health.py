"""
Tests para el endpoint de Health.
Verifica que el health check funciona correctamente.
"""
import pytest


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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
