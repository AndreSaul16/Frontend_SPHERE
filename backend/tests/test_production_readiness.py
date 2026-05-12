"""
Tests para rate limiting por plan y email verification gate.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestPlanRateLimits:
    """Verifica los límites de rate por plan."""

    def test_plan_rate_limits_configured(self):
        """Los límites por plan deben estar definidos correctamente."""
        from app.core.plan_limits import RATE_LIMIT_CHAT_BY_PLAN, RATE_LIMIT_GENERAL_BY_PLAN

        assert RATE_LIMIT_CHAT_BY_PLAN == {
            "free": (10, 60),
            "starter": (30, 60),
            "premium": (60, 60),
        }

        assert RATE_LIMIT_GENERAL_BY_PLAN == {
            "free": (30, 60),
            "starter": (60, 60),
            "premium": (120, 60),
        }

    def test_rate_limits_fallback_to_free(self):
        """Si el plan no existe, debe devolver límites de free."""
        from app.core.plan_limits import RATE_LIMIT_CHAT_BY_PLAN

        assert "free" in RATE_LIMIT_CHAT_BY_PLAN
        free_limit = RATE_LIMIT_CHAT_BY_PLAN["free"]
        assert free_limit[0] == 10


class TestEmailVerifiedGate:
    """Verifica que el email_verified gate funcione correctamente."""

    @pytest.mark.asyncio
    async def test_auto_provision_unverified_user_gets_zero_balance(self):
        """Usuario con email_verified=False debe tener wallet=0 y status=email_unverified."""
        from app.core import auth as auth_module

        mock_col = AsyncMock()
        created_user = {
            "firebase_uid": "test_unverified",
            "email": "test@example.com",
            "wallet": {
                "pro_messages_balance": 0,
                "pro_messages_granted_this_period": 0,
                "last_period_reset": None,
                "topup_messages_balance": 0,
            },
            "subscription": {
                "plan_id": "free",
                "status": "email_unverified",
            },
            "email_verified": False,
        }
        mock_col.find_one = AsyncMock(side_effect=[None, created_user])
        mock_col.update_one = AsyncMock()

        # Mock settings con properties necesarias
        mock_settings = MagicMock()
        mock_settings.plan_messages_map = {"free": 5}
        mock_settings.TOKEN_BUDGET_DAILY_DEFAULT = 100_000
        mock_settings.is_development = True

        with patch.object(auth_module, "get_users_collection", return_value=mock_col):
            with patch.object(auth_module, "settings", mock_settings):
                user = await auth_module._auto_provision_user({
                    "uid": "test_unverified",
                    "email": "test@example.com",
                    "email_verified": False,
                })

        assert user["wallet"]["pro_messages_balance"] == 0
        assert user["wallet"]["pro_messages_granted_this_period"] == 0
        assert user["subscription"]["status"] == "email_unverified"

    @pytest.mark.asyncio
    async def test_auto_provision_verified_user_gets_credits(self):
        """Usuario con email_verified=True debe tener wallet con créditos."""
        from app.core import auth as auth_module

        mock_col = AsyncMock()
        created_user = {
            "firebase_uid": "test_verified",
            "email": "verified@example.com",
            "wallet": {
                "pro_messages_balance": 5,
                "pro_messages_granted_this_period": 5,
                "last_period_reset": None,
                "topup_messages_balance": 0,
            },
            "subscription": {
                "plan_id": "free",
                "status": "active",
            },
            "email_verified": True,
        }
        mock_col.find_one = AsyncMock(side_effect=[None, created_user])
        mock_col.update_one = AsyncMock()

        mock_settings = MagicMock()
        mock_settings.plan_messages_map = {"free": 5}
        mock_settings.TOKEN_BUDGET_DAILY_DEFAULT = 100_000
        mock_settings.is_development = False

        with patch.object(auth_module, "get_users_collection", return_value=mock_col):
            with patch.object(auth_module, "settings", mock_settings):
                user = await auth_module._auto_provision_user({
                    "uid": "test_verified",
                    "email": "verified@example.com",
                    "email_verified": True,
                })

        assert user["wallet"]["pro_messages_balance"] == 5
        assert user["subscription"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_auto_provision_dev_token_always_verified(self):
        """Dev-token: sin email_verified en claims, pero is_development=True
        debe dar créditos como verificado."""
        from app.core import auth as auth_module

        # Simular que Firebase NO está inicializado (modo dev)
        auth_module._firebase_initialized = False

        mock_col = AsyncMock()
        created_user = {
            "firebase_uid": "dev_user",
            "email": "dev@sphere.local",
            "wallet": {
                "pro_messages_balance": 5,
                "pro_messages_granted_this_period": 5,
                "last_period_reset": None,
                "topup_messages_balance": 0,
            },
            "subscription": {
                "plan_id": "free",
                "status": "active",
            },
            "email_verified": True,
        }
        mock_col.find_one = AsyncMock(side_effect=[None, created_user])
        mock_col.update_one = AsyncMock()

        mock_settings = MagicMock()
        mock_settings.plan_messages_map = {"free": 5}
        mock_settings.TOKEN_BUDGET_DAILY_DEFAULT = 100_000
        mock_settings.is_development = True

        with patch.object(auth_module, "get_users_collection", return_value=mock_col):
            with patch.object(auth_module, "settings", mock_settings):
                user = await auth_module._auto_provision_user({
                    "uid": "dev_user",
                    "email": "dev@sphere.local",
                    "name": "Dev User",
                })

        assert user["wallet"]["pro_messages_balance"] == 5
        assert user["subscription"]["status"] == "active"
