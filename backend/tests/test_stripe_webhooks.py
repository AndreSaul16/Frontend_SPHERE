import pytest
import stripe
from httpx import AsyncClient
from unittest.mock import patch

@pytest.fixture
def mock_stripe_event():
    return {
        "id": "evt_test_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": "test_user_a",
                "customer": "cus_test",
                "subscription": "sub_test"
            }
        }
    }

@pytest.mark.asyncio
async def test_stripe_webhook_invalid_signature(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/webhooks/stripe", 
        json={"id": "evt_123"},
        headers={"stripe-signature": "invalid"}
    )
    # The construction will fail in stripe client if signature is invalid
    # Assuming the current implementation raises 400
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_stripe_webhook_idempotency_and_success(async_client: AsyncClient, mock_stripe_event, db_instance):
    # Limpieza de runs anteriores (idempotencia del propio test).
    events_col = db_instance.get_sync_client()["sphere_db"]["stripe_events_processed"]
    events_col.delete_many({"_id": "evt_test_123"})

    with patch("stripe.Webhook.construct_event", return_value=mock_stripe_event):
        # 1. First request, should process
        response = await async_client.post(
            "/api/v1/webhooks/stripe",
            json=mock_stripe_event,
            headers={"stripe-signature": "valid"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Check DB
        assert events_col.find_one({"_id": "evt_test_123"}) is not None

        # 2. Second request, same event, should be already processed
        response2 = await async_client.post(
            "/api/v1/webhooks/stripe",
            json=mock_stripe_event,
            headers={"stripe-signature": "valid"}
        )
        assert response2.status_code == 200
        assert response2.json()["status"] == "already processed"
