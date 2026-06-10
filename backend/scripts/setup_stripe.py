"""
Configuración idempotente de Stripe para SPHERE.

Lee STRIPE_SECRET_KEY del .env (nunca la imprime) y:
  --verify            : llamada de solo lectura (valida clave + muestra cuenta)
  --products          : crea/asegura los 5 productos+precios (idempotente por lookup_key)
  --webhook <URL>     : crea/asegura el webhook endpoint a <URL> (.../api/v1/webhooks/stripe)

Crear productos/precios/webhooks NO cobra a nadie: el cargo solo ocurre en un
checkout real. Todo es reversible (archivar producto, borrar webhook).
"""
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
import os

# Cargar .env de la raíz del monorepo (mismo que usa el backend).
ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ROOT_ENV)

import stripe

KEY = os.environ.get("STRIPE_SECRET_KEY", "").strip()
if not KEY:
    print("ERROR: STRIPE_SECRET_KEY vacío en .env", file=sys.stderr)
    sys.exit(1)
stripe.api_key = KEY


def g(obj, key, default=None):
    """Acceso seguro a campos de objetos Stripe (su .get está sombreado)."""
    try:
        return obj[key]
    except Exception:
        return default


def _masked() -> str:
    """Prefijo enmascarado de la clave para logs (nunca la clave completa)."""
    if len(KEY) <= 12:
        return KEY[:3] + "***"
    return KEY[:8] + "..." + KEY[-2:]


# SKU -> (env var, nombre, créditos, importe en céntimos EUR)
CATALOG = {
    "executive":     ("STRIPE_PRICE_EXECUTIVE",     "SPHERE — Executive Pack",  150,  3900),
    "director":      ("STRIPE_PRICE_DIRECTOR",      "SPHERE — Director Pack",   500, 13900),
    "boardroom":     ("STRIPE_PRICE_BOARDROOM",     "SPHERE — Boardroom Pack", 2000, 55000),
    "quick_meeting": ("STRIPE_PRICE_QUICK_MEETING", "SPHERE — Quick Meeting",    25,   799),
    "deep_dive":     ("STRIPE_PRICE_DEEP_DIVE",     "SPHERE — Deep Dive",        50,  1499),
}

WEBHOOK_EVENTS = [
    "checkout.session.completed",
    "invoice.payment_succeeded",
    "invoice.payment_failed",
    "customer.subscription.updated",
    "customer.subscription.deleted",
]


def verify():
    livemode = KEY.startswith("sk_live_") or KEY.startswith("rk_live_")
    print(f"Clave: {_masked()}  (modo {'LIVE' if livemode else 'TEST'})")
    acct = stripe.Account.retrieve()
    print(f"Cuenta Stripe: {g(acct,'id')}  país={g(acct,'country')}  "
          f"charges_enabled={g(acct,'charges_enabled')}  "
          f"details_submitted={g(acct,'details_submitted')}")
    prods = stripe.Product.list(limit=100, active=True)
    print(f"Productos activos actuales: {len(prods.data)}")
    for p in prods.data:
        sku = g(g(p, 'metadata', {}), 'sphere_sku')
        print(f"  - {p['id']}  {g(p,'name')}" + (f"  [sphere_sku={sku}]" if sku else ""))


def _find_price_by_lookup(lookup_key: str):
    res = stripe.Price.list(lookup_keys=[lookup_key], active=True, limit=1)
    return res.data[0] if res.data else None


def ensure_products():
    results = {}
    for sku, (env_var, name, credits, amount) in CATALOG.items():
        lookup_key = f"sphere_{sku}"
        existing = _find_price_by_lookup(lookup_key)
        if existing:
            print(f"= {sku}: precio ya existe ({existing['id']}), reutilizado")
            results[env_var] = existing["id"]
            continue

        product = stripe.Product.create(
            name=name,
            metadata={"sphere_sku": sku, "credits": str(credits)},
        )
        price = stripe.Price.create(
            product=product["id"],
            unit_amount=amount,
            currency="eur",
            lookup_key=lookup_key,
            metadata={"sphere_sku": sku, "credits": str(credits)},
        )
        print(f"+ {sku}: producto {product['id']} + precio {price['id']} "
              f"({amount/100:.2f}€ → {credits} créditos)")
        results[env_var] = price["id"]

    print("\n=== Variables de entorno (para Railway, servicio backend) ===")
    for env_var, price_id in results.items():
        print(f"{env_var}={price_id}")
    return results


def ensure_webhook(url: str):
    if not url.endswith("/api/v1/webhooks/stripe"):
        print(f"AVISO: la URL no termina en /api/v1/webhooks/stripe → {url}")
    # Idempotencia: si ya hay un endpoint con esa URL, no duplicar.
    for ep in stripe.WebhookEndpoint.list(limit=100).data:
        if g(ep, "url") == url:
            print(f"= Webhook ya existe: {ep['id']} → {url}")
            print("  (El signing secret solo se muestra al crear. Si lo necesitas, "
                  "bórralo en el dashboard y reejecuta, o créalo nuevo.)")
            return ep["id"], None
    ep = stripe.WebhookEndpoint.create(
        url=url,
        enabled_events=WEBHOOK_EVENTS,
        description="SPHERE backend — credit grants",
    )
    print(f"+ Webhook creado: {ep['id']} → {url}")
    print("\n=== Signing secret (cópialo a STRIPE_WEBHOOK_SECRET en Railway) ===")
    print(f"STRIPE_WEBHOOK_SECRET={g(ep,'secret')}")
    return ep["id"], g(ep, "secret")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--products", action="store_true")
    ap.add_argument("--webhook", metavar="URL", default=None)
    args = ap.parse_args()

    if args.verify:
        verify()
    if args.products:
        ensure_products()
    if args.webhook:
        ensure_webhook(args.webhook)
    if not (args.verify or args.products or args.webhook):
        ap.print_help()
