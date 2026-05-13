"""
Tests de aislamiento multi-tenant:
User A NO puede ver sesiones/agentes/docs de User B.
"""
import pytest
from unittest.mock import patch
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_user_a_cannot_see_user_b_sessions(authed_client_a, authed_client_b, clean_test_data):
    """User A crea una sesión. User B no la ve en su listado."""
    # User A crea sesión
    resp = await authed_client_a.post("/api/v1/sessions/", json={
        "title": "Sesión Privada de A",
        "base_agent_id": "CEO",
    })
    assert resp.status_code == 200
    session_a = resp.json()

    # User B lista sesiones
    resp = await authed_client_b.get("/api/v1/sessions/")
    assert resp.status_code == 200
    sessions_b = resp.json()

    # User B NO debe ver la sesión de User A
    session_ids_b = [s["session_id"] for s in sessions_b]
    assert session_a["session_id"] not in session_ids_b


@pytest.mark.asyncio
async def test_user_b_cannot_access_user_a_session(authed_client_a, authed_client_b, clean_test_data):
    """User B intenta acceder a una sesión de User A → 404."""
    # User A crea sesión
    resp = await authed_client_a.post("/api/v1/sessions/", json={
        "title": "Sesión Privada de A",
        "base_agent_id": "CEO",
    })
    session_id = resp.json()["session_id"]

    # User B intenta obtener el historial
    resp = await authed_client_b.get(f"/api/v1/sessions/{session_id}/history")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_user_b_cannot_delete_user_a_session(authed_client_a, authed_client_b, clean_test_data):
    """User B intenta borrar una sesión de User A → 404."""
    # User A crea sesión
    resp = await authed_client_a.post("/api/v1/sessions/", json={
        "title": "Sesión Privada de A",
        "base_agent_id": "CEO",
    })
    session_id = resp.json()["session_id"]

    # User B intenta borrarla
    resp = await authed_client_b.delete(f"/api/v1/sessions/{session_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_user_a_cannot_see_user_b_agents(authed_client_a, authed_client_b, clean_test_data):
    """User A crea un agente. User B no lo ve (si no es público)."""
    # User A crea agente privado
    resp = await authed_client_a.post("/api/v1/agents/", json={
        "identity": {"name": "Mi Agente Privado"},
        "brain_config": {
            "system_prompt": "Eres un agente de prueba con más de diez caracteres.",
            "model": "deepseek-chat",
        },
        "is_public": False,
    })
    assert resp.status_code == 200, f"Error creando agente: {resp.text}"
    agent_a = resp.json()

    # User B lista agentes
    resp = await authed_client_b.get("/api/v1/agents/")
    assert resp.status_code == 200
    agents_b = resp.json()

    # User B NO debe ver el agente privado de A
    agent_ids_b = [a["agent_id"] for a in agents_b]
    assert agent_a["agent_id"] not in agent_ids_b


@pytest.mark.asyncio
async def test_user_b_cannot_update_user_a_agent(authed_client_a, authed_client_b, clean_test_data):
    """User B intenta modificar un agente de User A → 404."""
    # User A crea agente
    resp = await authed_client_a.post("/api/v1/agents/", json={
        "identity": {"name": "Agente A"},
        "brain_config": {
            "system_prompt": "Eres un agente de prueba con más de diez caracteres.",
        },
    })
    assert resp.status_code == 200, f"Error creando agente: {resp.text}"
    agent_id = resp.json()["agent_id"]

    # User B intenta modificarlo
    resp = await authed_client_b.patch(f"/api/v1/agents/{agent_id}", json={
        "identity": {"name": "Hackeado por B"},
        "brain_config": {"system_prompt": "Prompt hackeado con más de diez caracteres."},
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_user_b_cannot_delete_user_a_agent(authed_client_a, authed_client_b, clean_test_data):
    """User B intenta borrar un agente de User A → 404."""
    # User A crea agente
    resp = await authed_client_a.post("/api/v1/agents/", json={
        "identity": {"name": "Agente A"},
        "brain_config": {
            "system_prompt": "Eres un agente de prueba con más de diez caracteres.",
        },
    })
    assert resp.status_code == 200, f"Error creando agente: {resp.text}"
    agent_id = resp.json()["agent_id"]

    # User B intenta borrarlo
    resp = await authed_client_b.delete(f"/api/v1/agents/{agent_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_user_b_cannot_rate_user_a_session(authed_client_a, authed_client_b, clean_test_data):
    """User B intenta calificar un mensaje de una sesión de User A → 404."""
    # User A crea sesión
    resp = await authed_client_a.post("/api/v1/sessions/", json={
        "title": "Sesión A",
        "base_agent_id": "CEO",
    })
    session_id = resp.json()["session_id"]

    # User B intenta calificar
    resp = await authed_client_b.post(f"/api/v1/sessions/{session_id}/ratings", json={
        "message_id": "msg_123",
        "rating": "up",
    })
    assert resp.status_code == 404
