import stripe

from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


# Mapeo plan_id -> Price ID de Stripe.
# Se rellenan desde .env tras crearlos en el dashboard Stripe.
def _price_map() -> dict[str, str]:
    return {
        "starter": settings.STRIPE_PRICE_STARTER,
        "premium": settings.STRIPE_PRICE_PREMIUM,
        "topup_free": settings.STRIPE_PRICE_TOPUP_FREE,
        "topup_starter": settings.STRIPE_PRICE_TOPUP_STARTER,
        "topup_premium_1k": settings.STRIPE_PRICE_TOPUP_PREMIUM_1K,
        "topup_premium_2k": settings.STRIPE_PRICE_TOPUP_PREMIUM_2K,
        "topup_premium_10k": settings.STRIPE_PRICE_TOPUP_PREMIUM_10K,
    }


def _is_topup(plan_id: str) -> bool:
    return plan_id.startswith("topup_")


class StripeClient:
    @staticmethod
    def create_checkout_session(user_id: str, plan_id: str, customer_email: str) -> str:
        prices = _price_map()
        price_id = prices.get(plan_id)
        if not price_id:
            raise ValueError(f"Invalid or unconfigured plan_id: {plan_id}")

        is_topup = _is_topup(plan_id)
        mode = "payment" if is_topup else "subscription"

        params = {
            "payment_method_types": ["card"],
            "line_items": [{"price": price_id, "quantity": 1}],
            "mode": mode,
            "success_url": f"{settings.FRONTEND_URL}/billing?success=true",
            "cancel_url": f"{settings.FRONTEND_URL}/billing?canceled=true",
            "client_reference_id": user_id,
            "customer_email": customer_email,
            "automatic_tax": {"enabled": True},
            # Metadata en la session: el webhook lee plan_id desde aquí.
            "metadata": {"plan_id": plan_id, "user_id": user_id},
        }

        # Para suscripciones, propaga la metadata al objeto subscription
        # (necesario para customer.subscription.updated/deleted).
        if mode == "subscription":
            params["subscription_data"] = {
                "metadata": {"plan_id": plan_id, "user_id": user_id}
            }
        else:
            params["payment_intent_data"] = {
                "metadata": {"plan_id": plan_id, "user_id": user_id}
            }

        session = stripe.checkout.Session.create(**params)
        return session.url

    @staticmethod
    def create_billing_portal_session(stripe_customer_id: str) -> str:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=f"{settings.FRONTEND_URL}/billing",
        )
        return session.url
