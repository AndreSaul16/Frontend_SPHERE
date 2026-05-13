"""
Tests de atomicidad para sesiones.
Verifica que sesiones son independientes (cambios en A no afectan B).
"""

import pytest


class TestSessionAtomicity:
    """Tests de atomicidad e independencia de sesiones."""

    @pytest.mark.asyncio
    async def test_session_atomicity(self, authed_client_a):
        """Test: Cambios en sesión A no afectan sesión B."""
        # 1. Create Session A
        res_a = await authed_client_a.post(
            "/api/v1/sessions/",
            json={"title": "Session A", "base_agent_id": "ceo-1", "type": "direct"},
        )
        assert res_a.status_code == 200
        session_a = res_a.json()
        id_a = session_a["session_id"]

        # 2. Create Session B - Same agent, distinct session
        res_b = await authed_client_a.post(
            "/api/v1/sessions/",
            json={"title": "Session B", "base_agent_id": "ceo-1", "type": "direct"},
        )
        assert res_b.status_code == 200
        session_b = res_b.json()
        id_b = session_b["session_id"]

        # 3. Customize Session A (Change Color)
        update_res = await authed_client_a.patch(
            f"/api/v1/sessions/{id_a}",
            json={"visual_config": {"bubble_color": "#FF0000"}},
        )
        assert update_res.status_code == 200
        updated_a = update_res.json()

        # 4. Verify A is updated
        assert updated_a["visual_config"]["bubble_color"] == "#FF0000"

        # 5. Verify B is UNCHANGED
        get_b = await authed_client_a.get("/api/v1/sessions/")
        sessions = get_b.json()
        fetched_b = next(s for s in sessions if s["session_id"] == id_b)

        # B should NOT have the red color
        assert fetched_b["visual_config"].get("bubble_color") != "#FF0000"

        print("✅ Atomicity Verified: Session B not affected by Session A changes.")

    @pytest.mark.asyncio
    async def test_group_session_creation(self, authed_client_a):
        """Test: Crear sesión grupal con miembros."""
        # 1. Create Group Session
        res_g = await authed_client_a.post(
            "/api/v1/sessions/",
            json={
                "title": "Board Meeting",
                "base_agent_id": "group-chat",
                "type": "group",
                "members": ["ceo-1", "cto-1"],
            },
        )
        assert res_g.status_code == 200
        session_g = res_g.json()

        assert session_g["type"] == "group"
        assert "ceo-1" in session_g["members"]
        assert "cto-1" in session_g["members"]

        # 2. Update Group Theme
        id_g = session_g["session_id"]
        update_res = await authed_client_a.patch(
            f"/api/v1/sessions/{id_g}", json={"visual_config": {"theme": "Magenta"}}
        )
        assert update_res.status_code == 200
        updated_g = update_res.json()

        assert updated_g["visual_config"]["theme"] == "Magenta"
        print("✅ Group Session Verified.")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
