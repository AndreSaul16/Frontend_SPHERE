"""
Token budget enforcement por usuario.
Dos capas: req/min (Redis) + token budget diario (MongoDB).
"""

from datetime import datetime, timezone
from app.infrastructure.database import get_users_collection
from app.core.logger import api_logger as logger


async def check_available(user_id: str, estimated_tokens: int = 1000) -> bool:
    """
    Verifica si el usuario tiene tokens disponibles en su presupuesto diario.

    Args:
        user_id: Firebase UID
        estimated_tokens: Estimación de tokens a consumir

    Returns:
        True si hay presupuesto disponible, False si se excedió
    """
    users_col = get_users_collection()
    user = await users_col.find_one({"firebase_uid": user_id})

    if not user:
        return False

    usage = user.get("usage", {})
    budget = usage.get("token_budget_daily", 100_000)
    used = usage.get("tokens_used_today", 0)
    reset_at = usage.get("tokens_reset_at")

    # Verificar si es hora de resetear
    now = datetime.now(timezone.utc)
    if reset_at:
        # MongoDB puede devolver naive datetimes — normalizar a aware
        if reset_at.tzinfo is None:
            reset_at = reset_at.replace(tzinfo=timezone.utc)
        if now > reset_at:
            # Reset del contador
            await users_col.update_one(
                {"firebase_uid": user_id},
                {
                    "$set": {
                        "usage.tokens_used_today": 0,
                        "usage.tokens_reset_at": _next_reset_time(now),
                    }
                },
            )
            return True

    return (used + estimated_tokens) <= budget


async def consume(user_id: str, tokens: int) -> bool:
    """
    Registra el consumo de tokens de una invocación al LLM.

    Returns:
        True si se registró, False si el usuario no existe
    """
    users_col = get_users_collection()
    result = await users_col.update_one(
        {"firebase_uid": user_id},
        {"$inc": {"usage.tokens_used_today": tokens}},
    )
    return result.modified_count > 0


def _next_reset_time(now: datetime) -> datetime:
    """Calcula el próximo reset (medianoche UTC del día siguiente)."""
    from datetime import timedelta

    tomorrow = now.date() + timedelta(days=1)
    return datetime.combine(tomorrow, datetime.min.time(), tzinfo=timezone.utc)
