"""
Bootstrap de productos y precios en Stripe (Test mode).

Ejecuta:
    cd backend
    set STRIPE_SECRET_KEY=sk_test_xxx
    python scripts/stripe_bootstrap.py

Crea los 5 productos/precios de SPHERE y te imprime los Price IDs listos
para pegar en .env. Idempotente: si un producto ya existe (mismo lookup_key),
no lo duplica — devuelve el existente.

Modelo solo-créditos: NO hay suscripciones. Todos los productos son one-time
(recurring=False). El plan Free (50 créditos/mes) no se crea en Stripe — se
otorga internamente. Lo de pago son packs de recarga + top-ups rápidos.
"""
import os
import sys

import stripe


# Productos y precios a crear. Todos en EUR, todos one-time (sin suscripciones).
# `lookup_key` permite que el script sea idempotente (Stripe deduplica por esto).
PRODUCTS = [
    # ── Packs de recarga ──
    {
        "lookup_key": "sphere_pack_executive",
        "name": "SPHERE · Executive Pack",
        "description": "150 créditos. Para seguir trabajando ese mismo día.",
        "price_eur_cents": 3900,
        "recurring": False,
        "env_var": "STRIPE_PRICE_EXECUTIVE",
    },
    {
        "lookup_key": "sphere_pack_director",
        "name": "SPHERE · Director Pack",
        "description": "500 créditos. El más popular: uso recurrente semanal.",
        "price_eur_cents": 13900,
        "recurring": False,
        "env_var": "STRIPE_PRICE_DIRECTOR",
    },
    {
        "lookup_key": "sphere_pack_boardroom",
        "name": "SPHERE · Boardroom Pack",
        "description": "2.000 créditos. Uso intensivo de herramientas y board completo.",
        "price_eur_cents": 55000,
        "recurring": False,
        "env_var": "STRIPE_PRICE_BOARDROOM",
    },
    # ── Top-ups rápidos ──
    {
        "lookup_key": "sphere_topup_quick_meeting",
        "name": "SPHERE · Quick Meeting",
        "description": "25 créditos. 5 interacciones extra con la Junta completa.",
        "price_eur_cents": 799,
        "recurring": False,
        "env_var": "STRIPE_PRICE_QUICK_MEETING",
    },
    {
        "lookup_key": "sphere_topup_deep_dive",
        "name": "SPHERE · Deep Dive",
        "description": "50 créditos. Sesión intensiva: 10 interacciones con el board.",
        "price_eur_cents": 1499,
        "recurring": False,
        "env_var": "STRIPE_PRICE_DEEP_DIVE",
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
    print("   - Evento: checkout.session.completed")
    print("     (modelo solo-créditos: no hay suscripciones que renovar/cancelar)")
    print("3. Copia el 'Signing secret' del webhook en STRIPE_WEBHOOK_SECRET.")
    print("4. Activa Stripe Tax para España (IVA 21%) en Settings → Tax.")


if __name__ == "__main__":
    main()
