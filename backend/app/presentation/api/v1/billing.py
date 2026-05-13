from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.errors import ErrorCode, billing_error, app_error
from app.core.plan_limits import validate_topup_tier, get_user_plan
from app.infrastructure.stripe_client import StripeClient
from app.infrastructure.database import get_users_collection

router = APIRouter()


class CheckoutRequest(BaseModel):
    plan_id: str


@router.post("/checkout")
async def create_checkout_session(
    req: CheckoutRequest,
    user: dict = Depends(get_current_user),
):
    # Top-up tier validation: el plan_id solicitado debe corresponder al tier actual
    if req.plan_id.startswith("topup_") and not validate_topup_tier(user, req.plan_id):
        raise app_error(
            ErrorCode.BILLING_TOPUP_NOT_ALLOWED,
            403,
            "Plan no disponible para tu tier.",
            current_plan=get_user_plan(user),
            requested=req.plan_id,
        )

    user_id = user["firebase_uid"]
    email = user["email"]
    try:
        url = StripeClient.create_checkout_session(user_id, req.plan_id, email)
        return {"url": url}
    except ValueError as e:
        raise billing_error(
            ErrorCode.BILLING_INVALID_PLAN, 400, str(e), plan_id=req.plan_id
        )
    except Exception as e:
        raise billing_error(
            ErrorCode.BILLING_STRIPE_ERROR, 500, f"Stripe error: {e}"
        )


@router.post("/portal")
async def create_portal_session(user: dict = Depends(get_current_user)):
    user_id = user["firebase_uid"]
    # Leer fresco de Mongo: el customer_id puede haberse seteado vía webhook
    # entre el login y este request, por lo que el dict `user` puede estar desactualizado.
    users_col = get_users_collection()
    fresh = await users_col.find_one(
        {"firebase_uid": user_id},
        {"subscription.stripe_customer_id": 1},
    )
    stripe_customer_id = ((fresh or {}).get("subscription") or {}).get("stripe_customer_id")
    if not stripe_customer_id:
        # Mantener 404 sin body estructurado para compatibilidad con tests existentes.
        raise HTTPException(status_code=404, detail="No stripe customer found")
    try:
        url = StripeClient.create_billing_portal_session(stripe_customer_id)
        return {"url": url}
    except Exception as e:
        raise billing_error(
            ErrorCode.BILLING_STRIPE_ERROR, 500, f"Stripe error: {e}"
        )


@router.get("/me")
async def get_billing_info(user: dict = Depends(get_current_user)):
    user_id = user["firebase_uid"]
    # Leer fresco de Mongo: balance/limits cambian en cada inferencia.
    users_col = get_users_collection()
    fresh = await users_col.find_one({"firebase_uid": user_id})
    if not fresh:
        raise HTTPException(status_code=404, detail="User not found")

    sub = fresh.get("subscription") or {}
    wallet = fresh.get("wallet") or {}
    limits = fresh.get("limits") or {}
    return {
        "plan_id": sub.get("plan_id", "free"),
        "status": sub.get("status", "active"),
        "current_period_end": sub.get("current_period_end"),
        "cancel_at_period_end": sub.get("cancel_at_period_end", False),
        "pro_messages_balance": wallet.get("pro_messages_balance", 0),
        "topup_messages_balance": wallet.get("topup_messages_balance", 0),
        "rag_storage_bytes_used": limits.get("rag_storage_bytes_used", 0),
        "custom_agents_count": limits.get("custom_agents_count", 0),
    }
