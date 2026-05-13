from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.core.logger import api_logger as logger
from app.core.plan_limits import validate_topup_tier, get_user_plan
from app.infrastructure.database import db

router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY


def _ts_to_dt(ts):
    if ts is None:
        return None
    return datetime.fromtimestamp(int(ts), tz=timezone.utc)


def _resolve_plan_from_metadata(obj) -> str | None:
    """Lee plan_id de la metadata del objeto Stripe (session/subscription)."""
    md = obj.get("metadata") or {}
    return md.get("plan_id")


def _grant_subscription(users_col, user_id: str, plan_id: str, customer_id: str,
                        subscription_id: str | None, period_end: datetime | None):
    """Asigna plan, otorga balance del periodo y actualiza datos Stripe."""
    plan_messages = settings.plan_messages_map.get(plan_id, 0)
    update = {
        "$set": {
            "subscription.plan_id": plan_id,
            "subscription.status": "active",
            "subscription.stripe_customer_id": customer_id,
            "subscription.stripe_subscription_id": subscription_id,
            "subscription.current_period_end": period_end,
            "subscription.cancel_at_period_end": False,
            "wallet.pro_messages_balance": plan_messages,
            "wallet.pro_messages_granted_this_period": plan_messages,
            "wallet.last_period_reset": datetime.now(timezone.utc),
        }
    }
    users_col.update_one({"firebase_uid": user_id}, update)


def _grant_topup(users_col, user_id: str, plan_id: str):
    """Suma mensajes de top-up al wallet del usuario."""
    topup_messages = settings.topup_messages_map.get(plan_id, 0)
    if topup_messages <= 0:
        logger.warning(f"Top-up plan_id desconocido: {plan_id}")
        return
    users_col.update_one(
        {"firebase_uid": user_id},
        {"$inc": {"wallet.topup_messages_balance": topup_messages}},
    )


@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # construct_event valida firma + secret. En tests se mockea esta función.
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET or ""
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        # Cualquier otro error de construct_event = firma inválida.
        logger.warning(f"Stripe webhook construct_event failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    db_client = db.get_sync_client()[settings.DB_NAME]
    events_col = db_client["stripe_events_processed"]
    users_col = db_client["users"]
    transactions_col = db_client["credit_transactions"]

    # Idempotencia
    if events_col.find_one({"_id": event["id"]}):
        return {"status": "already processed"}

    event_type = event["type"]
    obj = event["data"]["object"]
    logger.info(f"Stripe webhook: {event_type} ({event['id']})")

    try:
        if event_type == "checkout.session.completed":
            user_id = obj.get("client_reference_id")
            customer_id = obj.get("customer")
            mode = obj.get("mode")  # "subscription" | "payment"
            plan_id = _resolve_plan_from_metadata(obj)

            if not user_id or not plan_id:
                logger.error(f"checkout.session.completed sin user_id/plan_id: {obj.get('id')}")
            elif mode == "subscription":
                subscription_id = obj.get("subscription")
                # Resolver period_end consultando la subscripción (session no lo trae siempre).
                period_end = None
                if subscription_id:
                    try:
                        sub = stripe.Subscription.retrieve(subscription_id)
                        period_end = _ts_to_dt(sub.get("current_period_end"))
                    except Exception as e:
                        logger.warning(f"No pude leer subscription {subscription_id}: {e}")
                _grant_subscription(users_col, user_id, plan_id, customer_id, subscription_id, period_end)
                transactions_col.insert_one({
                    "user_id": user_id,
                    "delta": settings.plan_messages_map.get(plan_id, 0),
                    "balance_source": "plan",
                    "reason": "subscription_grant",
                    "stripe_event_id": event["id"],
                    "created_at": datetime.now(timezone.utc),
                })
            elif mode == "payment":  # top-up
                # Defense-in-depth: validar que el top-up corresponde al tier del usuario
                user_doc = users_col.find_one({"firebase_uid": user_id})
                if user_doc and not validate_topup_tier(user_doc, plan_id):
                    logger.warning(
                        f"WEBHOOK SECURITY: cross-tier top-up rechazado. "
                        f"user={user_id} tier={get_user_plan(user_doc)} "
                        f"topup={plan_id} event={event['id']}"
                    )
                    # No otorgamos créditos pero NO rompemos el webhook
                    # (Stripe reintentaría por siempre)
                else:
                    _grant_topup(users_col, user_id, plan_id)
                    transactions_col.insert_one({
                        "user_id": user_id,
                        "delta": settings.topup_messages_map.get(plan_id, 0),
                        "balance_source": "topup",
                        "reason": "topup_purchase",
                        "stripe_event_id": event["id"],
                        "created_at": datetime.now(timezone.utc),
                    })

        elif event_type == "invoice.payment_succeeded":
            # Renovación de suscripción → reset del balance del periodo.
            customer_id = obj.get("customer")
            subscription_id = obj.get("subscription")
            if subscription_id:
                user = users_col.find_one({"subscription.stripe_subscription_id": subscription_id})
                if user:
                    plan_id = (user.get("subscription") or {}).get("plan_id", "free")
                    plan_messages = settings.plan_messages_map.get(plan_id, 0)
                    period_end = None
                    try:
                        sub = stripe.Subscription.retrieve(subscription_id)
                        period_end = _ts_to_dt(sub.get("current_period_end"))
                    except Exception:
                        pass
                    users_col.update_one(
                        {"_id": user["_id"]},
                        {"$set": {
                            "subscription.status": "active",
                            "subscription.current_period_end": period_end,
                            "wallet.pro_messages_balance": plan_messages,
                            "wallet.pro_messages_granted_this_period": plan_messages,
                            "wallet.last_period_reset": datetime.now(timezone.utc),
                        }},
                    )
                    transactions_col.insert_one({
                        "user_id": user.get("firebase_uid"),
                        "delta": plan_messages,
                        "balance_source": "plan",
                        "reason": "period_reset",
                        "stripe_event_id": event["id"],
                        "created_at": datetime.now(timezone.utc),
                    })

        elif event_type == "invoice.payment_failed":
            subscription_id = obj.get("subscription")
            if subscription_id:
                users_col.update_one(
                    {"subscription.stripe_subscription_id": subscription_id},
                    {"$set": {"subscription.status": "past_due"}},
                )

        elif event_type == "customer.subscription.updated":
            subscription_id = obj.get("id")
            period_end = _ts_to_dt(obj.get("current_period_end"))
            cancel_at_period_end = obj.get("cancel_at_period_end", False)
            status = obj.get("status", "active")
            users_col.update_one(
                {"subscription.stripe_subscription_id": subscription_id},
                {"$set": {
                    "subscription.current_period_end": period_end,
                    "subscription.cancel_at_period_end": cancel_at_period_end,
                    "subscription.status": status,
                }},
            )

        elif event_type == "customer.subscription.deleted":
            subscription_id = obj.get("id")
            # El plan ha terminado. Bajamos a free, conservamos top-ups.
            users_col.update_one(
                {"subscription.stripe_subscription_id": subscription_id},
                {"$set": {
                    "subscription.plan_id": "free",
                    "subscription.status": "canceled",
                    "subscription.stripe_subscription_id": None,
                    "subscription.cancel_at_period_end": False,
                    "wallet.pro_messages_balance": settings.plan_messages_map["free"],
                    "wallet.pro_messages_granted_this_period": settings.plan_messages_map["free"],
                    "wallet.last_period_reset": datetime.now(timezone.utc),
                }},
            )

        else:
            logger.info(f"Stripe event no manejado: {event_type}")

    except Exception as e:
        logger.error(f"Error procesando webhook {event_type}: {e}")
        # No metemos en stripe_events_processed → Stripe reintentará.
        raise HTTPException(status_code=500, detail="webhook_processing_error")

    events_col.insert_one({
        "_id": event["id"],
        "type": event_type,
        "processed_at": datetime.now(timezone.utc),
    })
    return {"status": "success"}
