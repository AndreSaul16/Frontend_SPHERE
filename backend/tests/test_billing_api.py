import pytest
import os
from unittest.mock import patch, MagicMock
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Fixtures: plan-varied profiles
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_billing_info(authed_client_a: AsyncClient, db_instance):
    # Setup test user wallet
    db = db_instance.get_async_db()
    await db["users"].update_one(
        {"firebase_uid": "test_user_a"},
        {"$set": {
            "wallet": {"pro_messages_balance": 150, "topup_messages_balance": 50},
            "subscription": {"plan_id": "premium"}
        }}
    )
    
    response = await authed_client_a.get("/api/v1/billing/me")
    
    assert response.status_code == 200
    data = response.json()
    assert data["plan_id"] == "premium"
    assert data["pro_messages_balance"] == 150
    assert data["topup_messages_balance"] == 50


@pytest.mark.asyncio
async def test_create_checkout_session(authed_client_a: AsyncClient):
    with patch("app.infrastructure.stripe_client.StripeClient.create_checkout_session") as mock_stripe:
        mock_stripe.return_value = "https://checkout.stripe.com/test"
        
        response = await authed_client_a.post("/api/v1/billing/checkout", json={"plan_id": "premium"})
        
        assert response.status_code == 200
        assert response.json()["url"] == "https://checkout.stripe.com/test"
        mock_stripe.assert_called_once_with("test_user_a", "premium", "usera@test.com")


@pytest.mark.asyncio
async def test_create_portal_session(authed_client_a: AsyncClient, db_instance):
    db = db_instance.get_async_db()
    await db["users"].update_one(
        {"firebase_uid": "test_user_a"},
        {"$set": {"subscription": {"stripe_customer_id": "cus_123"}}}
    )

    with patch("app.infrastructure.stripe_client.StripeClient.create_billing_portal_session") as mock_stripe:
        mock_stripe.return_value = "https://billing.stripe.com/test"
        
        response = await authed_client_a.post("/api/v1/billing/portal")
        
        assert response.status_code == 200
        assert response.json()["url"] == "https://billing.stripe.com/test"
        mock_stripe.assert_called_once_with("cus_123")


# ---------------------------------------------------------------------------
# Task 3.1 / 3.3 — Top-up tier validation tests
# ---------------------------------------------------------------------------


class TestTopupTierValidation:
    """Verifica que el tier del usuario coincida con el top-up solicitado."""

    def test_allowed_topups_mapping_is_correct(self):
        """Mapping ALLOWED_TOPUPS_BY_PLAN debe coincidir con la especificación."""
        from app.core.plan_limits import ALLOWED_TOPUPS_BY_PLAN

        # free → solo topup_free
        assert ALLOWED_TOPUPS_BY_PLAN["free"] == {"topup_free"}
        # starter → solo topup_starter
        assert ALLOWED_TOPUPS_BY_PLAN["starter"] == {"topup_starter"}
        # premium → topups premium
        assert ALLOWED_TOPUPS_BY_PLAN["premium"] == {
            "topup_premium_1k",
            "topup_premium_2k",
            "topup_premium_10k",
        }

    @pytest.mark.asyncio
    async def test_free_user_buys_topup_free_returns_200(
        self, authed_client_a: AsyncClient, db_instance
    ):
        """Free user buying topup_free → 200 OK."""
        from tests.conftest import _make_user_profile, MOCK_USER_A

        free_profile = _make_user_profile(MOCK_USER_A, plan_id="free")

        with patch("app.core.auth._auto_provision_user", return_value=free_profile):
            with patch("app.infrastructure.stripe_client.StripeClient.create_checkout_session") as mock_stripe:
                mock_stripe.return_value = "https://checkout.stripe.com/test"
                response = await authed_client_a.post(
                    "/api/v1/billing/checkout", json={"plan_id": "topup_free"}
                )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_free_user_attempts_premium_topup_returns_403(
        self, authed_client_a: AsyncClient, db_instance
    ):
        """Free user buying topup_premium_10k → 403 Forbidden."""
        from tests.conftest import _make_user_profile, MOCK_USER_A

        free_profile = _make_user_profile(MOCK_USER_A, plan_id="free")

        with patch("app.core.auth._auto_provision_user", return_value=free_profile):
            response = await authed_client_a.post(
                "/api/v1/billing/checkout", json={"plan_id": "topup_premium_10k"}
            )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "billing.topup_not_allowed"

    @pytest.mark.asyncio
    async def test_premium_user_buys_premium_topup_returns_200(
        self, authed_client_a: AsyncClient, db_instance
    ):
        """Premium user buying topup_premium_1k → 200 OK."""
        from tests.conftest import _make_user_profile, MOCK_USER_A

        premium_profile = _make_user_profile(MOCK_USER_A, plan_id="premium")

        with patch("app.core.auth._auto_provision_user", return_value=premium_profile):
            with patch("app.infrastructure.stripe_client.StripeClient.create_checkout_session") as mock_stripe:
                mock_stripe.return_value = "https://checkout.stripe.com/test"
                response = await authed_client_a.post(
                    "/api/v1/billing/checkout", json={"plan_id": "topup_premium_1k"}
                )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_starter_user_buys_starter_topup_returns_200(
        self, authed_client_a: AsyncClient, db_instance
    ):
        """Starter user buying topup_starter → 200 OK."""
        from tests.conftest import _make_user_profile, MOCK_USER_A

        starter_profile = _make_user_profile(MOCK_USER_A, plan_id="starter")

        with patch("app.core.auth._auto_provision_user", return_value=starter_profile):
            with patch("app.infrastructure.stripe_client.StripeClient.create_checkout_session") as mock_stripe:
                mock_stripe.return_value = "https://checkout.stripe.com/test"
                response = await authed_client_a.post(
                    "/api/v1/billing/checkout", json={"plan_id": "topup_starter"}
                )

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Task 3.2 / 3.3 — Webhook defense-in-depth tests
# ---------------------------------------------------------------------------


class TestWebhookTopupDefense:
    """Verifica que el webhook NO otorga créditos si el top-up no corresponde al tier."""

    @pytest.mark.asyncio
    async def test_webhook_cross_tier_topup_grants_no_credits(
        self, async_client: AsyncClient, db_instance
    ):
        """Free user recibe webhook de topup_premium_10k → no créditos, warning log."""
        db_sync = db_instance.get_sync_client()["sphere_db"]

        # Configurar usuario free
        db_sync["users"].delete_many({"firebase_uid": "test_user_a"})
        db_sync["users"].insert_one({
            "firebase_uid": "test_user_a",
            "email": "usera@test.com",
            "subscription": {"plan_id": "free", "status": "active"},
            "wallet": {
                "pro_messages_balance": 5,
                "topup_messages_balance": 0,
            },
        })

        # Limpiar idempotencia
        db_sync["stripe_events_processed"].delete_many(
            {"_id": "evt_cross_tier_topup"}
        )

        import stripe as stripe_lib
        event = {
            "id": "evt_cross_tier_topup",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": "test_user_a",
                    "customer": "cus_test",
                    "mode": "payment",
                    "metadata": {"plan_id": "topup_premium_10k"},
                }
            },
        }

        with patch.object(stripe_lib.Webhook, "construct_event", return_value=event):
            response = await async_client.post(
                "/api/v1/webhooks/stripe",
                json=event,
                headers={"stripe-signature": "valid"},
            )

        # Webhook no debe romper — Stripe reintentaría por siempre
        assert response.status_code == 200

        # No deben haberse otorgado créditos de top-up
        user = db_sync["users"].find_one({"firebase_uid": "test_user_a"})
        assert user["wallet"]["topup_messages_balance"] == 0

        # Verificar que NO se creó transacción de top-up
        tx_count = db_sync["credit_transactions"].count_documents({
            "user_id": "test_user_a",
            "balance_source": "topup",
        })
        assert tx_count == 0, (
            f"Se crearon {tx_count} transacciones de top-up inesperadas"
        )


# ---------------------------------------------------------------------------
# BF-003: Stripe config flag tests
# ---------------------------------------------------------------------------


class TestStripeConfiguredFlag:
    """Tests para stripe_configured: flag computado desde STRIPE_SECRET_KEY."""

    def test_stripe_configured_true_when_key_present(self):
        """BF-003: STRIPE_SECRET_KEY no vacío → stripe_configured=True."""
        from app.core.config import Settings
        s = Settings(STRIPE_SECRET_KEY="sk_test_valid", MONGODB_URL="mongodb://localhost")
        assert s.stripe_configured is True

    def test_stripe_configured_false_when_key_empty(self):
        """BF-003: STRIPE_SECRET_KEY vacío → stripe_configured=False."""
        from app.core.config import Settings
        s = Settings(STRIPE_SECRET_KEY="", MONGODB_URL="mongodb://localhost")
        assert s.stripe_configured is False

    def test_stripe_configured_false_when_key_whitespace(self):
        """BF-003: STRIPE_SECRET_KEY solo espacios → stripe_configured=False."""
        from app.core.config import Settings
        s = Settings(STRIPE_SECRET_KEY="   ", MONGODB_URL="mongodb://localhost")
        assert s.stripe_configured is False

    def test_stripe_configured_true_with_surrounding_whitespace(self):
        """BF-003: STRIPE_SECRET_KEY con espacios alrededor → stripe_configured=True."""
        from app.core.config import Settings
        s = Settings(STRIPE_SECRET_KEY="  sk_test_abc  ", MONGODB_URL="mongodb://localhost")
        assert s.stripe_configured is True


class TestBillingMeStripeConfigured:
    """Tests de integración: GET /billing/me incluye stripe_configured."""

    @pytest.mark.asyncio
    async def test_billing_me_includes_stripe_configured(self, authed_client_a, db_instance):
        """BF-003: GET /billing/me debe incluir el campo stripe_configured."""
        db = db_instance.get_async_db()
        await db["users"].update_one(
            {"firebase_uid": "test_user_a"},
            {"$set": {
                "wallet": {"pro_messages_balance": 5, "topup_messages_balance": 0},
                "subscription": {"plan_id": "free", "status": "active"},
            }}
        )

        response = await authed_client_a.get("/api/v1/billing/me")
        assert response.status_code == 200
        data = response.json()
        assert "stripe_configured" in data, (
            f"El response debe tener el campo stripe_configured. Keys: {list(data.keys())}"
        )
        assert isinstance(data["stripe_configured"], bool), (
            f"stripe_configured debe ser bool, es {type(data['stripe_configured'])}"
        )
