"""
Tests para el endpoint de Sessions.
Verifica CRUD de sesiones de chat.
"""

import pytest
from datetime import datetime


class TestSessionsEndpoint:
    """Tests para /api/v1/sessions/"""

    @pytest.mark.asyncio
    async def test_create_session(self, authed_client_a):
        """Test: Crear una nueva sesión evolucionada."""
        session_data = {
            "title": "Test Session Evolution",
            "user_id": "test_user_pytest",
            "visual_config": {"name": "Pepe Test", "color": "gold"},
        }
        response = await authed_client_a.post("/api/v1/sessions/", json=session_data)

        assert response.status_code == 200, f"Error: {response.text}"

        data = response.json()
        assert "session_id" in data
        assert data["title"] == "Test Session Evolution"
        assert data["visual_config"]["name"] == "Pepe Test"
        assert data["visual_config"]["color"] == "gold"
        assert "context_files" in data
        assert isinstance(data["context_files"], list)

        # Guardar para cleanup
        pytest.session_id_created = data["session_id"]
        print(f"\n✅ Sesión evolucionada creada: {data['session_id']}")

    @pytest.mark.asyncio
    async def test_create_session_default_values(self, authed_client_a):
        """Test: Crear sesión con valores por defecto."""
        response = await authed_client_a.post("/api/v1/sessions/", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Nueva Estrategia"

    @pytest.mark.asyncio
    async def test_list_sessions(self, authed_client_a):
        """Test: Listar todas las sesiones."""
        response = await authed_client_a.get("/api/v1/sessions/")

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Verificar estructura de la nueva sesión
        if data:
            session = data[0]
            assert "session_id" in session
            assert "user_id" in session
            assert "visual_config" in session
            assert "context_files" in session

    @pytest.mark.asyncio
    async def test_get_session_history_empty(self, authed_client_a):
        """Test: Obtener historial de una sesión nueva (vacío)."""
        # Crear sesión primero
        create_response = await authed_client_a.post(
            "/api/v1/sessions/", json={"title": "Empty History Test"}
        )
        session_id = create_response.json()["session_id"]

        # Obtener historial
        response = await authed_client_a.get(f"/api/v1/sessions/{session_id}/history")

        assert response.status_code == 200

        data = response.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) == 0, "Nueva sesión debería tener historial vacío"

    @pytest.mark.asyncio
    async def test_get_session_history_nonexistent(self, authed_client_a):
        """Test: Obtener historial de sesión inexistente devuelve 404."""
        fake_id = "nonexistent-session-id-12345"

        response = await authed_client_a.get(f"/api/v1/sessions/{fake_id}/history")

        # require_owner lanza 404 para sesiones que no existen
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_session(self, authed_client_a):
        """Test: Eliminar una sesión."""
        # Crear sesión para eliminar
        create_response = await authed_client_a.post(
            "/api/v1/sessions/", json={"title": "To Be Deleted"}
        )
        session_id = create_response.json()["session_id"]

        # Eliminar
        response = await authed_client_a.delete(f"/api/v1/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["session_id"] == session_id
        print(f"\n🗑️ Sesión eliminada: {session_id}")

    @pytest.mark.asyncio
    async def test_delete_session_nonexistent(self, authed_client_a):
        """Test: Intentar eliminar sesión inexistente."""
        fake_id = "nonexistent-session-12345"

        response = await authed_client_a.delete(f"/api/v1/sessions/{fake_id}")

        assert response.status_code == 404, f"Error detallado: {response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
