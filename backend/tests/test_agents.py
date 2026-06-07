"""
Tests para el endpoint de Agents.
Verifica CRUD de agentes personalizados.
"""

import pytest
from datetime import datetime


class TestAgentsEndpoint:
    """Tests para /api/v1/agents/"""

    @pytest.mark.asyncio
    async def test_create_agent(self, authed_client_a):
        """Test: Crear un nuevo agente evolucionado."""
        agent_data = {
            "identity": {"name": "Oberon Pytest", "role": "tester", "color": "purple"},
            "brain_config": {
                "system_prompt": "Eres un agente de prueba evolucionado con más de diez caracteres.",
                "model": "deepseek-chat",
            },
            "default_tools": [],
        }

        response = await authed_client_a.post("/api/v1/agents/", json=agent_data)

        assert response.status_code == 200, f"Error: {response.text}"

        data = response.json()
        assert "agent_id" in data
        assert data["identity"]["name"] == "Oberon Pytest"
        # 'deepseek-chat' (legacy/deprecado) se normaliza a 'deepseek-v4-pro'.
        assert data["brain_config"]["model"] == "deepseek-v4-pro"

        # Guardar ID para otros tests
        pytest.test_agent_id = data["agent_id"]
        print(f"\n✅ Agente evolucionado creado: {data['agent_id']}")

    @pytest.mark.asyncio
    async def test_create_agent_defaults(self, authed_client_a):
        """Test: Crear agente con valores por defecto."""
        agent_data = {
            "identity": {"name": "Agente Minimal"},
            "brain_config": {"system_prompt": "Prompt básico con más de diez caracteres fácilmente."},
        }

        response = await authed_client_a.post("/api/v1/agents/", json=agent_data)

        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()

        # Verificar defaults
        assert data["identity"]["role"] == "specialist"
        assert data["brain_config"]["model"] == "deepseek-v4-pro"
        assert data["is_public"] is False

    @pytest.mark.asyncio
    async def test_list_agents(self, authed_client_a):
        """Test: Listar todos los agentes."""
        response = await authed_client_a.get("/api/v1/agents/")

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        print(f"\n📋 Agentes encontrados: {len(data)}")

        # Verificar estructura
        if data:
            agent = data[0]
            assert "agent_id" in agent
            assert "identity" in agent
            assert "brain_config" in agent

    @pytest.mark.asyncio
    async def test_get_agent_detail(self, authed_client_a):
        """Test: Obtener detalles de un agente (incluyendo prompt)."""
        # Crear agente primero con el esquema correcto
        agent_data = {
            "identity": {"name": "Detail Test Agent", "description": "Para test de detalle"},
            "brain_config": {
                "system_prompt": "Este es el prompt secreto con más de diez caracteres.",
            },
        }
        create_response = await authed_client_a.post("/api/v1/agents/", json=agent_data)
        assert create_response.status_code == 200, f"Error creando: {create_response.text}"
        agent_id = create_response.json()["agent_id"]

        # Obtener detalle
        response = await authed_client_a.get(f"/api/v1/agents/{agent_id}")

        assert response.status_code == 200

        data = response.json()
        assert data["agent_id"] == agent_id
        assert "brain_config" in data
        assert data["brain_config"]["system_prompt"] == "Este es el prompt secreto con más de diez caracteres."

    @pytest.mark.asyncio
    async def test_get_agent_nonexistent(self, authed_client_a):
        """Test: Obtener agente inexistente."""
        fake_id = "nonexistent-agent-12345"

        response = await authed_client_a.get(f"/api/v1/agents/{fake_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_agent(self, authed_client_a):
        """Test: Eliminar un agente."""
        # Crear agente para eliminar con el esquema correcto
        agent_data = {
            "identity": {"name": "To Be Deleted", "description": "Este agente será eliminado"},
            "brain_config": {
                "system_prompt": "Un prompt de más de diez caracteres para testing.",
            },
        }
        create_response = await authed_client_a.post("/api/v1/agents/", json=agent_data)
        assert create_response.status_code == 200, f"Error creando: {create_response.text}"
        agent_id = create_response.json()["agent_id"]

        # Eliminar
        response = await authed_client_a.delete(f"/api/v1/agents/{agent_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["agent_id"] == agent_id
        print(f"\n🗑️ Agente eliminado: {agent_id}")

        # Verificar que ya no existe
        get_response = await authed_client_a.get(f"/api/v1/agents/{agent_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_agent_nonexistent(self, authed_client_a):
        """Test: Eliminar agente inexistente."""
        fake_id = "nonexistent-agent-12345"

        response = await authed_client_a.delete(f"/api/v1/agents/{fake_id}")

        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
