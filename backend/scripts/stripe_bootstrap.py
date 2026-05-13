"""
Bootstrap de productos y precios en Stripe (Test mode).

Ejecuta:
    cd backend
    set STRIPE_SECRET_KEY=sk_test_xxx
    python scripts/stripe_bootstrap.py

Crea los 7 productos/precios de SPHERE y te imprime los Price IDs listos
para pegar en .env. Idempotente: si un producto ya existe (mismo lookup_key),
no lo duplica — devuelve el existente.
"""
import os
import sys

import stripe


# Productos y precios a crear. Todos en EUR.
# `lookup_key` permite que el script sea idempotente (Stripe deduplica por esto).
PRODUCTS = [
    {
        "lookup_key": "sphere_starter_monthly",
        "name": "SPHERE Starter",
        "description": "1.000 mensajes Pro/mes + 100 MB RAG + 3 agentes custom.",
        "price_eur_cents": 999,
        "recurring": True,
        "env_var": "STRIPE_PRICE_STARTER",
    },
    {
        "lookup_key": "sphere_premium_monthly",
        "name": "SPHERE Premium",
        "description": "2.000 mensajes Pro/mes + 1 GB RAG + agentes ilimitados + API access.",
        "price_eur_cents": 1999,
        "recurring": True,
        "env_var": "STRIPE_PRICE_PREMIUM",
    },
    {
        "lookup_key": "sphere_topup_free_100",
        "name": "Top-up 100 mensajes (Free)",
        "description": "100 mensajes Pro adicionales. No caducan mientras la cuenta esté activa.",
        "price_eur_cents": 499,
        "recurring": False,
        "env_var": "STRIPE_PRICE_TOPUP_FREE",
    },
    {
        "lookup_key": "sphere_topup_starter_700",
        "name": "Top-up 700 mensajes (Starter)",
        "description": "700 mensajes Pro adicionales. Solo planes Starter o Premium.",
        "price_eur_cents": 599,
        "recurring": False,
        "env_var": "STRIPE_PRICE_TOPUP_STARTER",
    },
    {
        "lookup_key": "sphere_topup_premium_1k",
        "name": "Top-up 1.000 mensajes (Premium)",
        "description": "1.000 mensajes Pro adicionales. Solo plan Premium.",
        "price_eur_cents": 799,
        "recurring": False,
        "env_var": "STRIPE_PRICE_TOPUP_PREMIUM_1K",
    },
    {
        "lookup_key": "sphere_topup_premium_2k",
        "name": "Top-up 2.000 mensajes (Premium)",
        "description": "2.000 mensajes Pro adicionales. Solo plan Premium.",
        "price_eur_cents": 1499,
        "recurring": False,
        "env_var": "STRIPE_PRICE_TOPUP_PREMIUM_2K",
    },
    {
        "lookup_key": "sphere_topup_premium_10k",
        "name": "Top-up 10.000 mensajes (Premium)",
        "description": "10.000 mensajes Pro adicionales. Solo plan Premium.",
        "price_eur_cents": 7499,
        "recurring": False,
        "env_var": "STRIPE_PRICE_TOPUP_PREMIUM_10K",
    },
]


def get_or_create_price(spec: dict) -> str:
    """Devuelve el Price ID, creando producto+precio si no existen."""
    # 1) Buscar precio existente con este lookup_key.
    existing = stripe.Price.list(lookup_keys=[spec["lookup_key"]], active=True, limit=1)
    if existing.data:
        return existing.data[0].id

    # 2) Crear producto.
    product = stripe.Product.create(
        name=spec["name"],
        description=spec["description"],
        tax_code="txcd_10103001",  # SaaS digital
    )

    # 3) Crear precio.
    price_params = {
        "product": product.id,
        "unit_amount": spec["price_eur_cents"],
        "currency": "eur",
        "lookup_key": spec["lookup_key"],
        "tax_behavior": "inclusive",  # IVA incluido (UE)
    }
    if spec["recurring"]:
        price_params["recurring"] = {"interval": "month"}

    price = stripe.Price.create(**price_params)
    return price.id


def main():
    secret = os.environ.get("STRIPE_SECRET_KEY")
    if not secret:
        print("ERROR: STRIPE_SECRET_KEY no está en el entorno.", file=sys.stderr)
        print("Ejecuta:  set STRIPE_SECRET_KEY=sk_test_xxxx", file=sys.stderr)
        sys.exit(1)

    # Test mode acepta sk_test_ (Secret Key) y rk_test_ (Restricted Key).
    is_test = secret.startswith("sk_test_") or secret.startswith("rk_test_")
    if not is_test:
        confirm = input(
            f"⚠️  La key NO es test mode (empieza por '{secret[:8]}'). "
            f"Vas a crear productos REALES. ¿Continuar? [y/N]: "
        )
        if confirm.lower() != "y":
            sys.exit(1)

    stripe.api_key = secret

    print("Creando/recuperando productos y precios en Stripe...\n")
    env_lines = []
    for spec in PRODUCTS:
        price_id = get_or_create_price(spec)
        print(f"  ✓ {spec['name']}")
        print(f"      {spec['env_var']}={price_id}")
        env_lines.append(f"{spec['env_var']}={price_id}")

    print("\n" + "=" * 60)
    print("PEGA ESTO EN TU .env:")
    print("=" * 60)
    print("\n".join(env_lines))
    print("\n" + "=" * 60)
    print("Próximos pasos:")
    print("=" * 60)
    print("1. Pega los IDs anteriores en backend/.env (o el .env raíz).")
    print("2. Configura el webhook en https://dashboard.stripe.com/test/webhooks")
    print("   - URL: https://TU_DOMINIO/api/v1/webhooks/stripe")
    print("   - Eventos: checkout.session.completed, invoice.payment_succeeded,")
    print("              invoice.payment_failed, customer.subscription.updated,")
    print("              customer.subscription.deleted")
    print("3. Copia el 'Signing secret' del webhook en STRIPE_WEBHOOK_SECRET.")
    print("4. Activa Stripe Tax para España (IVA 21%) en Settings → Tax.")


if __name__ == "__main__":
    main()
