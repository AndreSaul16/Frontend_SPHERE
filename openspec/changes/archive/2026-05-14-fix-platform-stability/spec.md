# Delta Specs: fix-platform-stability

> **Status**: draft | **TDD**: ACTIVE (pytest + vitest) | All testable

## credit-system

###  Requirements

| ID | Requirement | N |
|----|------------|---|
| CS-001 | `_ensure_wallet` MUST re-initialize invalid wallets (`null`, `{}`, missing `pro_messages_balance`) | 3 |
| CS-002 | Valid wallets MUST NOT be overwritten | 1 |
| CS-003 | Admin repair endpoint SHALL fix invalid wallets for existing users | 2 |

#### CS-001: Wallet Hardening

- GIVEN `wallet: {}`  WHEN `_ensure_wallet` is called  THEN init with `pro_messages_balance: 5`
- GIVEN `wallet: null`  WHEN `_ensure_wallet` is called  THEN init with `pro_messages_balance: 5`
- GIVEN `wallet: {topup_messages_balance: 0}` (no pro key)  WHEN `_ensure_wallet` runs  THEN re-init

#### CS-002: Valid Wallet Preservation

- GIVEN wallet `{pro_messages_balance: 3, topup_messages_balance: 0}`  WHEN `_ensure_wallet` runs  THEN balance unchanged

#### CS-003: Repair Endpoint

- GIVEN user with wallet `{}`  WHEN repair called  THEN wallet initialized, user can send messages
- GIVEN user with valid wallet (balance 3)  WHEN repair called  THEN balance remains 3

---

## billing-frontend

###  Requirements

| ID | Requirement | N |
|----|------------|---|
| BF-001 | `refresh()` MUST defer fetch until Firebase auth resolves, retry on failure | 2 |
| BF-002 | Balance UI MUST show loading state (not 0) while fetch is incomplete | 2 |
| BF-003 | FastAPI MUST validate Stripe config at startup, expose `stripe_configured` | 2 |
| BF-004 | Frontend MUST handle unavailable payments with user feedback | 2 |

#### BF-001: Auth-Aware Refresh

- GIVEN Firebase auth initializing  WHEN `refresh()` called  THEN defer until `onAuthStateChanged`
- GIVEN `/billing/me` returns 401  WHEN `refresh()` fails  THEN retry 3x with backoff (1s, 2s, 4s)

#### BF-002: Loading State

- GIVEN `loaded: false`  WHEN BillingPage renders balance  THEN show skeleton/spinner, NOT "0"
- GIVEN `loaded: true`, balance 3  WHEN rendered  THEN display numeric balance

#### BF-003: Stripe Startup Check

- GIVEN `STRIPE_SECRET_KEY=""`  WHEN FastAPI boots  THEN log CRITICAL, disable Stripe, `stripe_configured: false`
- GIVEN `STRIPE_SECRET_KEY` is set  WHEN `/billing/me` called  THEN response includes `stripe_configured: true`

#### BF-004: Stripe UX Degradation

- GIVEN `stripe_configured: false`  WHEN BillingPage renders  THEN hide buttons, show "Pagos no disponibles"
- GIVEN checkout returns 5xx  WHEN user clicks Subscribe  THEN show error toast (not just console.error)

---

## settings-page

###  Requirements

| ID | Requirement | N |
|----|------------|---|
| SP-001 | SettingsPage MUST scroll vertically on mobile while keeping tab bar fixed | 2 |

#### SP-001: Mobile Scroll

- GIVEN mobile viewport (375x812)  WHEN content overflows  THEN main area scrolls; blobs use `pointer-events-none`
- GIVEN page scrolled to bottom  WHEN tab bar renders  THEN remains sticky/visible

---

## infrastructure

###  Requirements

| ID | Requirement | N |
|----|------------|---|
| IN-001 | n8n MUST be deployable via Railway config with required env vars | 2 |

#### IN-001: n8n Deployment

- GIVEN `railway.toml` or `railway.json`  WHEN validated  THEN n8n service exists, image `n8nio/n8n:latest`
- GIVEN n8n boots on Railway  THEN `N8N_HOST`, `N8N_PORT`, `N8N_PROTOCOL`, `WEBHOOK_URL` set; service reachable
