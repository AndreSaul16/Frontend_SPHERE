"""
Tests del token budget enforcement.
"""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
async def test_check_available_within_budget(db_instance):
    """Usuario con presupuesto disponible → True."""
    from app.application.token_budget import check_available

    with patch("app.application.token_budget.get_users_collection") as mock_get_col:
        mock_col = AsyncMock()
        mock_get_col.return_value = mock_col
        mock_col.find_one.return_value = {
            "firebase_uid": "test_user",
            "usage": {
                "token_budget_daily": 100_000,
                "tokens_used_today": 10_000,
                "tokens_reset_at": datetime.now(timezone.utc) + timedelta(hours=12),
            }
        }

        result = await check_available("test_user", estimated_tokens=5_000)
        assert result is True


@pytest.mark.asyncio
async def test_check_available_over_budget(db_instance):
    """Usuario que excedió el presupuesto → False."""
    from app.application.token_budget import check_available

    with patch("app.application.token_budget.get_users_collection") as mock_get_col:
        mock_col = AsyncMock()
        mock_get_col.return_value = mock_col
        mock_col.find_one.return_value = {
            "firebase_uid": "test_user",
            "usage": {
                "token_budget_daily": 100_000,
                "tokens_used_today": 99_000,
                "tokens_reset_at": datetime.now(timezone.utc) + timedelta(hours=12),
            }
        }

        result = await check_available("test_user", estimated_tokens=5_000)
        assert result is False


@pytest.mark.asyncio
async def test_check_available_resets_on_new_day():
    """Si pasó la hora de reset, el contador se resetea."""
    from app.application.token_budget import check_available

    with patch("app.application.token_budget.get_users_collection") as mock_get_col:
        mock_col = AsyncMock()
        mock_get_col.return_value = mock_col
        mock_col.find_one.return_value = {
            "firebase_uid": "test_user",
            "usage": {
                "token_budget_daily": 100_000,
                "tokens_used_today": 99_000,
                "tokens_reset_at": datetime.now(timezone.utc) - timedelta(hours=1),  # Ya pasó
            }
        }

        result = await check_available("test_user", estimated_tokens=5_000)
        assert result is True


@pytest.mark.asyncio
async def test_consume_increments_counter():
    """consume() incrementa tokens_used_today."""
    from app.application.token_budget import consume

    with patch("app.application.token_budget.get_users_collection") as mock_get_col:
        mock_col = AsyncMock()
        mock_get_col.return_value = mock_col
        mock_col.update_one.return_value = AsyncMock(modified_count=1)

        result = await consume("test_user", 1500)
        assert result is True
        mock_col.update_one.assert_called_once()
        call_args = mock_col.update_one.call_args
        assert call_args[0][0] == {"firebase_uid": "test_user"}
        assert call_args[0][1]["$inc"]["usage.tokens_used_today"] == 1500
