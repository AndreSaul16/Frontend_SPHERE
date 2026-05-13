"""
Unit tests para app.core.auth.
Cubre: init_firebase, _verify_token (dev/prod/expired/invalid), _auto_provision_user.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
import app.core.auth as auth_module
from app.core.auth import init_firebase, _verify_token, _auto_provision_user


@pytest.fixture(autouse=True)
def reset_firebase_state():
    """Resetea el flag global de inicialización entre tests."""
    auth_module._firebase_initialized = False
    yield
    auth_module._firebase_initialized = False


# ── init_firebase ────────────────────────────────────────────

def test_init_firebase_skips_when_no_path():
    """Si FIREBASE_CREDENTIALS_PATH está vacío, no hace nada y no marca como inicializado."""
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.FIREBASE_CREDENTIALS_PATH = ""
        init_firebase()
    assert auth_module._firebase_initialized is False


def test_init_firebase_raises_when_file_missing(tmp_path):
    """Si el path apunta a un archivo inexistente, init_firebase propaga la excepción."""
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.FIREBASE_CREDENTIALS_PATH = str(tmp_path / "no_existe.json")
        with pytest.raises(Exception):
            init_firebase()
    assert auth_module._firebase_initialized is False


def test_init_firebase_sets_initialized_on_success():
    """Con SDK inicializado correctamente, _firebase_initialized queda en True."""
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.FIREBASE_CREDENTIALS_PATH = "/fake/creds.json"
        with patch("app.core.auth.credentials.Certificate"):
            with patch("app.core.auth.firebase_admin.initialize_app"):
                init_firebase()
    assert auth_module._firebase_initialized is True


def test_init_firebase_is_idempotent():
    """Segunda llamada no re-inicializa el SDK aunque ya esté inicializado."""
    auth_module._firebase_initialized = True
    with patch("app.core.auth.firebase_admin.initialize_app") as mock_init:
        init_firebase()
    mock_init.assert_not_called()


# ── _verify_token: modo development ─────────────────────────

async def test_verify_token_dev_mode_accepts_dev_token():
    """En dev sin Firebase, 'dev-token' devuelve claims sintéticos de dev_user."""
    auth_module._firebase_initialized = False
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.is_production = False
        result = await _verify_token("dev-token")
    assert result["uid"] == "dev_user"
    assert result["email"] == "dev@sphere.local"


async def test_verify_token_dev_mode_rejects_other_tokens():
    """En dev sin Firebase, cualquier token que no sea 'dev-token' devuelve 401."""
    auth_module._firebase_initialized = False
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.is_production = False
        with pytest.raises(HTTPException) as exc:
            await _verify_token("token-real-cualquiera")
    assert exc.value.status_code == 401


# ── _verify_token: modo production ──────────────────────────

async def test_verify_token_prod_without_firebase_returns_503():
    """En producción con Firebase no inicializado, cualquier token devuelve 503."""
    auth_module._firebase_initialized = False
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.is_production = True
        with pytest.raises(HTTPException) as exc:
            await _verify_token("cualquier-token")
    assert exc.value.status_code == 503


# ── _verify_token: errores del SDK ──────────────────────────

async def test_verify_token_valid_returns_claims():
    """Token válido devuelve los claims decodificados por el SDK."""
    auth_module._firebase_initialized = True
    expected = {"uid": "abc123", "email": "user@example.com", "name": "User"}
    with patch("app.core.auth.firebase_auth.verify_id_token", return_value=expected):
        result = await _verify_token("valid-token")
    assert result == expected


async def test_verify_token_expired_returns_401():
    """Token expirado devuelve 401 con detalle 'Token expirado'."""
    auth_module._firebase_initialized = True
    from firebase_admin.auth import ExpiredIdTokenError
    with patch("app.core.auth.firebase_auth.verify_id_token",
               side_effect=ExpiredIdTokenError("Token is expired.", None)):
        with pytest.raises(HTTPException) as exc:
            await _verify_token("expired-token")
    assert exc.value.status_code == 401
    assert "expirado" in exc.value.detail


async def test_verify_token_invalid_returns_401():
    """Token malformado devuelve 401 con detalle 'Token inválido'."""
    auth_module._firebase_initialized = True
    from firebase_admin.auth import InvalidIdTokenError
    with patch("app.core.auth.firebase_auth.verify_id_token",
               side_effect=InvalidIdTokenError("Invalid token.", None)):
        with pytest.raises(HTTPException) as exc:
            await _verify_token("invalid-token")
    assert exc.value.status_code == 401
    assert "inválido" in exc.value.detail


async def test_verify_token_unknown_error_returns_401():
    """Error inesperado del SDK devuelve 401 genérico, no 500."""
    auth_module._firebase_initialized = True
    with patch("app.core.auth.firebase_auth.verify_id_token",
               side_effect=Exception("unexpected sdk error")):
        with pytest.raises(HTTPException) as exc:
            await _verify_token("bad-token")
    assert exc.value.status_code == 401


# ── _auto_provision_user ─────────────────────────────────────

async def test_auto_provision_creates_new_user():
    """Usuario nuevo se inserta en MongoDB con todos los campos requeridos."""
    mock_col = AsyncMock()
    mock_col.find_one = AsyncMock(side_effect=[
        None,  # Primera llamada: buscar usuario existente → no existe
        {      # Segunda llamada: find_one después del upsert → usuario recién creado
            "firebase_uid": "new_uid",
            "email": "new@example.com",
            "display_name": "New User",
            "onboarding_completed": False,
            "wallet": {
                "pro_messages_balance": 5,
                "pro_messages_granted_this_period": 5,
                "topup_messages_balance": 0,
            },
        },
    ])

    with patch("app.core.auth.get_users_collection", return_value=mock_col):
        result = await _auto_provision_user({
            "uid": "new_uid",
            "email": "new@example.com",
            "name": "New User",
        })

    # Ahora usa update_one con upsert=True en lugar de insert_one
    mock_col.update_one.assert_called_once()
    assert result["firebase_uid"] == "new_uid"
    assert result["email"] == "new@example.com"
    assert result["onboarding_completed"] is False
    assert "_id" not in result


async def test_auto_provision_updates_existing_user_last_login():
    """Usuario existente actualiza last_login_at sin crear uno nuevo."""
    existing = {
        "firebase_uid": "existing_uid",
        "email": "existing@example.com",
        "onboarding_completed": True,
        "wallet": {
            "pro_messages_balance": 3,
            "topup_messages_balance": 0,
        },
    }
    mock_col = AsyncMock()
    mock_col.find_one = AsyncMock(return_value=existing)

    with patch("app.core.auth.get_users_collection", return_value=mock_col):
        result = await _auto_provision_user({
            "uid": "existing_uid",
            "email": "existing@example.com",
        })

    mock_col.update_one.assert_called_once()
    update_filter, update_op = mock_col.update_one.call_args[0]
    assert "last_login_at" in update_op["$set"]
    assert result["firebase_uid"] == "existing_uid"


async def test_auto_provision_strips_mongo_id():
    """El resultado nunca expone el _id interno de MongoDB."""
    existing = {
        "_id": "507f1f77bcf86cd799439011",
        "firebase_uid": "uid_x",
        "email": "x@test.com",
    }
    mock_col = AsyncMock()
    mock_col.find_one = AsyncMock(return_value=existing)

    with patch("app.core.auth.get_users_collection", return_value=mock_col):
        result = await _auto_provision_user({"uid": "uid_x", "email": "x@test.com"})

    assert "_id" not in result


async def test_auto_provision_uses_email_as_display_name_fallback():
    """Si los claims no traen 'name', se usa el email como display_name."""
    mock_col = AsyncMock()
    mock_col.find_one = AsyncMock(side_effect=[
        None,  # Primera: no existe
        {      # Segunda: recién creado
            "firebase_uid": "uid_no_name",
            "email": "fallback@example.com",
            "display_name": "fallback@example.com",
        },
    ])

    with patch("app.core.auth.get_users_collection", return_value=mock_col):
        result = await _auto_provision_user({
            "uid": "uid_no_name",
            "email": "fallback@example.com",
        })

    assert result["display_name"] == "fallback@example.com"


# ---------------------------------------------------------------------------
# Task 3.6 — Plan-varied fixture verification
# ---------------------------------------------------------------------------


class TestPlanVariedFixtures:
    """Verifica que los fixtures por plan estén correctamente configurados."""

    def test_free_user_fixture_balance(self, free_user_profile):
        """Free fixture: 5 créditos, plan_id='free'."""
        assert free_user_profile["subscription"]["plan_id"] == "free"
        assert free_user_profile["wallet"]["pro_messages_balance"] == 5

    def test_starter_user_fixture_balance(self, starter_user_profile):
        """Starter fixture: 50 créditos, plan_id='starter'."""
        assert starter_user_profile["subscription"]["plan_id"] == "starter"
        assert starter_user_profile["wallet"]["pro_messages_balance"] == 50

    def test_premium_user_fixture_balance(self, premium_user_profile):
        """Premium fixture: 100 créditos, plan_id='premium'."""
        assert premium_user_profile["subscription"]["plan_id"] == "premium"
        assert premium_user_profile["wallet"]["pro_messages_balance"] == 100
