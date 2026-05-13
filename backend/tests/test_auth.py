"""
Tests de autenticación: verificación de token, auto-provisioning, 401.
"""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_no_auth_returns_401(async_client):
    """Un request sin Authorization header devuelve 401."""
    resp = await async_client.post("/api/v1/chat/", json={"query": "hola"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_returns_401(async_client):
    """Un token inválido devuelve 401."""
    from fastapi import HTTPException
    with patch("app.core.auth._verify_token", side_effect=HTTPException(status_code=401, detail="Token inválido")):
        async_client.headers["Authorization"] = "Bearer invalid_token"
        resp = await async_client.post("/api/v1/chat/", json={"query": "hola"})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_valid_token(authed_client_a):
    """GET /me devuelve el perfil del usuario autenticado."""
    resp = await authed_client_a.get("/api/v1/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["firebase_uid"] == "test_user_a"
    assert data["email"] == "usera@test.com"


@pytest.mark.asyncio
async def test_patch_me_updates_profile(authed_client_a):
    """PATCH /me actualiza el perfil del usuario."""
    resp = await authed_client_a.patch("/api/v1/me", json={
        "display_name": "Nuevo Nombre",
        "professional_profile": {
            "role": "CTO",
            "industry": "SaaS",
        }
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_onboarding_complete(authed_client_a):
    """POST /me/onboarding/complete marca onboarding como completado."""
    resp = await authed_client_a.post("/api/v1/me/onboarding/complete")
    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarding_completed"] is True


@pytest.mark.asyncio
async def test_sessions_require_auth(async_client):
    """GET /sessions/ sin auth devuelve 401."""
    resp = await async_client.get("/api/v1/sessions/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_agents_require_auth(async_client):
    """GET /agents/ sin auth devuelve 401."""
    resp = await async_client.get("/api/v1/agents/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_session_injects_user_id(authed_client_a):
    """POST /sessions/ inyecta el user_id del JWT, no del body."""
    resp = await authed_client_a.post("/api/v1/sessions/", json={
        "title": "Test Session",
        "base_agent_id": "CEO",
    })
    assert resp.status_code == 200
    data = resp.json()
    # El user_id debe venir del JWT, no del body
    assert data["user_id"] == "test_user_a"
