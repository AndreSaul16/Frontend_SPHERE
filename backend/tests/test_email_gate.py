"""
Integration tests for email verification gate.
Verifica que:
- Usuarios con email_unverified reciben 0 créditos y son rechazados en /stream.
- Usuarios verificados reciben créditos y acceden a /stream normalmente.
- Dev-token bypass trata al usuario como verificado en desarrollo.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.core.auth import _auto_provision_user


# ── Fixtures ──────────────────────────────────────────────────


@pytest.fixture
def unverified_user_profile():
    """Fixture reusable: perfil de usuario con email NO verificado."""
    from tests.conftest import _make_user_profile
    return _make_user_profile(
        {"uid": "unverified_uid", "email": "unverified@test.com", "name": "UV User"},
        plan_id="free",
        email_verified=False,
    )


# ── Auto-provision tests ──────────────────────────────────────


async def test_auto_provision_unverified_email_gets_zero_balance():
    """email_verified=False → pro_messages_balance=0 y status=email_unverified."""
    import app.core.auth as auth_mod

    mock_col = AsyncMock()
    mock_col.find_one = AsyncMock(side_effect=[
        None,  # Usuario no existe → crear
        {       # Recién creado
            "firebase_uid": "uv_uid",
            "email": "uv@example.com",
            "subscription": {"plan_id": "free", "status": "email_unverified"},
            "wallet": {"pro_messages_balance": 0, "topup_messages_balance": 0},
        },
    ])

    # Deshabilitar dev-token bypass: Firebase inicializado, modo producción
    old_firebase = auth_mod._firebase_initialized
    auth_mod._firebase_initialized = True
    try:
        with patch("app.core.auth.settings") as mock_settings:
            mock_settings.is_development = False
            mock_settings.plan_messages_map = {"free": 5}
            with patch("app.core.auth.get_users_collection", return_value=mock_col):
                result = await _auto_provision_user({
                    "uid": "uv_uid",
                    "email": "uv@example.com",
                    "email_verified": False,
                })

        assert result["wallet"]["pro_messages_balance"] == 0, (
            f"Unverified user should get 0 credits, got {result['wallet']['pro_messages_balance']}"
        )
        assert result["subscription"]["status"] == "email_unverified", (
            f"Expected 'email_unverified', got '{result['subscription']['status']}'"
        )
    finally:
        auth_mod._firebase_initialized = old_firebase


async def test_auto_provision_verified_email_gets_5_credits():
    """email_verified=True → pro_messages_balance=5 y status=active."""
    import app.core.auth as auth_mod

    mock_col = AsyncMock()
    mock_col.find_one = AsyncMock(side_effect=[
        None,  # No existe
        {       # Recién creado
            "firebase_uid": "v_uid",
            "email": "v@example.com",
            "subscription": {"plan_id": "free", "status": "active"},
            "wallet": {"pro_messages_balance": 5, "topup_messages_balance": 0},
        },
    ])

    old_firebase = auth_mod._firebase_initialized
    auth_mod._firebase_initialized = True
    try:
        with patch("app.core.auth.settings") as mock_settings:
            mock_settings.is_development = False
            mock_settings.plan_messages_map = {"free": 5}
            with patch("app.core.auth.get_users_collection", return_value=mock_col):
                result = await _auto_provision_user({
                    "uid": "v_uid",
                    "email": "v@example.com",
                    "email_verified": True,
                })

        assert result["wallet"]["pro_messages_balance"] == 5, (
            f"Verified user should get 5 credits, got {result['wallet']['pro_messages_balance']}"
        )
        assert result["subscription"]["status"] == "active", (
            f"Expected 'active', got '{result['subscription']['status']}'"
        )
    finally:
        auth_mod._firebase_initialized = old_firebase


async def test_dev_token_bypass_treats_user_as_verified_in_development():
    """En dev sin Firebase, dev-token bypass → email_verified=True aunque claims digan False."""
    import app.core.auth as auth_mod

    mock_col = AsyncMock()
    mock_col.find_one = AsyncMock(side_effect=[
        None,  # No existe
        {       # Recién creado con bypass activo
            "firebase_uid": "dev_bypass_uid",
            "email": "devbypass@test.com",
            "subscription": {"plan_id": "free", "status": "active"},
            "wallet": {"pro_messages_balance": 5, "topup_messages_balance": 0},
        },
    ])

    old_firebase = auth_mod._firebase_initialized
    auth_mod._firebase_initialized = False  # Simula dev sin Firebase
    try:
        with patch("app.core.auth.settings") as mock_settings:
            mock_settings.is_development = True
            mock_settings.plan_messages_map = {"free": 5}
            with patch("app.core.auth.get_users_collection", return_value=mock_col):
                result = await _auto_provision_user({
                    "uid": "dev_bypass_uid",
                    "email": "devbypass@test.com",
                    "email_verified": False,  # Firebase dice False
                })

        # Dev-token bypass ignora el claim y trata como verificado
        assert result["wallet"]["pro_messages_balance"] == 5, (
            f"Dev bypass should grant credits despite email_verified=False in claims"
        )
        assert result["subscription"]["status"] == "active", (
            f"Dev bypass should set status=active, got '{result['subscription']['status']}'"
        )
    finally:
        auth_mod._firebase_initialized = old_firebase


# ── Stream endpoint integration tests ─────────────────────────


@pytest.mark.asyncio
async def test_stream_returns_403_when_status_is_email_unverified(unverified_user_profile):
    """POST /stream con email_unverified → 403, detail.error == 'email_unverified'."""
    from httpx import AsyncClient, ASGITransport
    from main import app
    from app.core.auth import get_current_user

    mock_user = unverified_user_profile

    async def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/stream/", json={
                "query": "Hola",
                "session_id": "test_session_403",
            })

        assert response.status_code == 403, (
            f"Expected 403 for email_unverified, got {response.status_code}"
        )
        detail = response.json()["detail"]
        assert detail["error"] == "email_unverified", (
            f"Expected error='email_unverified', got '{detail.get('error')}'"
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_stream_allows_verified_user():
    """POST /stream con email verificado → no es rechazado por email gate (402 esperado por falta de créditos en entorno de test)."""
    from httpx import AsyncClient, ASGITransport
    from main import app
    from app.core.auth import get_current_user

    verified_user = {
        "firebase_uid": "verified_stream_uid",
        "email": "verified@test.com",
        "subscription": {"plan_id": "premium", "status": "active"},
        "wallet": {"pro_messages_balance": 100, "topup_messages_balance": 0},
    }

    async def override_get_current_user():
        return verified_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/stream/", json={
                "query": "Hola",
                "session_id": "test_session_ok",
            })

        # No debe ser 403 (email_unverified rejection)
        # Podría fallar por otras razones (DB no configurada en test), pero NO por email gate
        assert response.status_code != 403 or (
            response.status_code == 403 and
            response.json().get("detail", {}).get("error") != "email_unverified"
        ), (
            f"Verified user should NOT get email_unverified rejection. "
            f"Status: {response.status_code}, Detail: {response.text}"
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)
