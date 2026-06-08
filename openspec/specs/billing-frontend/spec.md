# billing-frontend

> **Source**: fix-platform-stability (archived 2026-05-14)
> **TDD**: ACTIVE (vitest)

## Requirements

| ID | Requirement | N |
|----|------------|---|
| BF-001 | `refresh()` MUST defer fetch until Firebase auth resolves, retry on failure | 2 |
| BF-002 | Balance UI MUST show loading state (not 0) while fetch is incomplete | 2 |
| BF-003 | FastAPI MUST validate Stripe config at startup, expose `stripe_configured` | 2 |
| BF-004 | Frontend MUST handle unavailable payments with user feedback | 2 |

### BF-001: Auth-Aware Refresh

- GIVEN Firebase auth initializing  WHEN `refresh()` called  THEN defer until `onAuthStateChanged`
- GIVEN `/billing/me` returns 401  WHEN `refresh()` fails  THEN retry 3x with backoff (1s, 2s, 4s)

### BF-002: Loading State

- GIVEN `loaded: false`  WHEN BillingPage renders balance  THEN show skeleton/spinner, NOT "0"
- GIVEN `loaded: true`, balance 3  WHEN rendered  THEN display numeric balance

### BF-003: Stripe Startup Check

- GIVEN `STRIPE_SECRET_KEY=""`  WHEN FastAPI boots  THEN log CRITICAL, disable Stripe, `stripe_configured: false`
- GIVEN `STRIPE_SECRET_KEY` is set  WHEN `/billing/me` called  THEN response includes `stripe_configured: true`

### BF-004: Stripe UX Degradation

- GIVEN `stripe_configured: false`  WHEN BillingPage renders  THEN hide buttons, show "Pagos no disponibles"
- GIVEN checkout returns 5xx  WHEN user clicks Subscribe  THEN show error toast (not just console.error)
