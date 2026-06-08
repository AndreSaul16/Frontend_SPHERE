# Design: fix-platform-stability

## Technical Approach

Five independent fixes with zero cross-contamination. Backend changes follow existing Clean/Hexagonal patterns — domain logic in `core/`, API in `presentation/`. Frontend follows Zustand 5 patterns with devtools middleware. No new dependencies required.

---

## Architecture Decisions

| # | Decision | Option A | Option B | Chosen | Rationale |
|---|----------|----------|----------|--------|-----------|
| AD1 | Wallet guard | `isinstance(wallet, dict) and "pro_messages_balance" in wallet` | `wallet is not None and len(wallet) > 0` | **A** | Explicit key check prevents `{topup: 0}` bypass; aligns with CS-001 scenario |
| AD2 | Repair function visibility | `_repair_wallet()` as internal `auth.py` function | Admin-only endpoint via router | **Both** | Internal for login-time repair; endpoint (CS-003) for batch/migration runs |
| AD3 | Refresh retry backoff | 3 attempts, 1s/2s/4s delay in store | 3 attempts, exponential in component | **A** | Store-level retry is reusable across all consumers; component stays dumb |
| AD4 | Auth readiness signal | Poll `auth.currentUser` with 100ms intervals up to 5s | Firebase `onAuthStateChanged` callback in store | **A** | Callback-based is cleaner but adds import complexity; polling is simple, bounded, testable |
| AD5 | Stripe validation | Lifespan `stripe_configured: bool` on Settings + expose via `/billing/me` | Check per-request in billing endpoint | **A** | Fails fast at boot, reduces per-request overhead, makes flag available to FE |
| AD6 | Stripe UX on failure | Toast notification via browser `alert()` | Custom toast component/modal | **A** | Zero new deps; SPHERE already uses `alert` in error paths. Upgrade to toast component later |

---

## Data Flow

### Credit Wallet Initialization (Login)

```
Firebase Auth → _auto_provision_user() → _ensure_wallet(uid, user_doc)
                                               │
                                    ┌──────────┴──────────┐
                                    ▼                      ▼
                            wallet válido?            wallet inválido
                            (dict + pro_key)          (null, {}, sin key)
                                    │                      │
                            return user_doc          WARNING log
                                    │                 _repair_wallet()
                                    │                 init 5 créditos
                                    ▼                      ▼
                            user_doc                   user_doc
```

### Balance Refresh (Frontend)

```
BillingPage mount → refresh()
                     │
                     ├─ auth ready? ──No──→ wait 100ms × 50 (5s max)
                     │                        │
                     ▼                        ▼ timeout → isLoading=true, stop
              fetch /billing/me
                     │
                ┌────┴────┐
               OK         fail
                │          │
           set balance   retry ← (1s, 2s, 4s)
           loaded=true    │
                      all fail → isLoading=false, loaded=false
```

### Stripe Graceful Degradation

```
FastAPI boot → _validate_env_vars()
                    │
            STRIPE_SECRET_KEY empty?
               ┌────┴────┐
              Yes         No
               │          │
         LOG CRITICAL   stripe_configured=true
         stripe_configured=false
               │          │
               ▼          ▼
    GET /billing/me → { stripe_configured: bool, ... }
               │
          Frontend BillingPage
          ┌────┴────┐
         false      true
          │          │
    hide buttons   show buttons
    show message
```

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/core/auth.py` | Modify | Fix `_ensure_wallet` guard (L108), add `_repair_wallet()`, add WARNING logs |
| `backend/app/core/config.py` | Modify | Add `stripe_configured: bool` computed property |
| `backend/main.py` | Modify | Add Stripe validation to `_validate_env_vars()`, set `settings.stripe_configured` |
| `backend/app/presentation/api/v1/billing.py` | Modify | Add `stripe_configured` to `GET /billing/me` response |
| `frontend/src/store/useBillingStore.ts` | Modify | Add auth-ready gate, retry logic, `isLoading` flag; wire `decrementOptimistic` |
| `frontend/src/pages/BillingPage.tsx` | Modify | Loading skeleton, error state, `stripe_configured` handling, checkout error toast |
| `frontend/src/pages/SettingsPage.tsx` | Modify | L50: `overflow-hidden` → `overflow-y-auto` |
| `backend/tests/test_auth.py` | Modify | Add `_ensure_wallet` unit tests (CS-001, CS-002) |
| `backend/tests/test_billing_api.py` | Modify | Add `stripe_configured` field assertion, checkout-disabled test |
| `frontend/tests/components/BillingPage.test.tsx` | Modify | Add loading/error/stripe-disabled test cases |
| `railway.toml` (root) | Create | n8n service definition: image `n8nio/n8n:latest`, port 5678, env vars |
| `frontend/src/components/chat/ChatPanel.tsx` | Modify | Call `decrementOptimistic()` after each successful message send |

---

## API Contract Changes

### `GET /billing/me` — add field

```json
{
  "plan_id": "free",
  "status": "active",
  "pro_messages_balance": 5,
  "topup_messages_balance": 0,
  "stripe_configured": true,    // NEW: bool
  // ... existing fields unchanged
}
```

---

## Database Schema

No schema migrations. `wallet` field continues as embedded subdocument in `users` collection. `_repair_wallet()` uses `$set` with `wallet.*` dot notation — existing pattern from `_auto_provision_user`.

---

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit (BE) | `_ensure_wallet` with `{}`, `null`, missing key, valid wallet | Pytest with `pytest.mark.parametrize`, mock `get_users_collection` |
| Unit (BE) | `_repair_wallet` idempotency (valid wallet unchanged) | Same pattern, assert `$set` not called |
| Unit (BE) | `stripe_configured` = True when key present, False when empty | Direct `Settings` instantiation test |
| Integration (BE) | `GET /billing/me` includes `stripe_configured` | Extend `test_get_billing_info`, assert new field |
| Integration (FE) | `useBillingStore.refresh()` retry on failure | Vitest, mock `fetch` → 401 → retry 3x |
| Component (FE) | BillingPage skeleton when `isLoading && !loaded` | `@testing-library/react`, set store state |
| Component (FE) | Stripe buttons hidden when `stripe_configured=false` | Set store, render, assert button absent |
| Component (FE) | SettingsPage scrolls on mobile | Vitest + `jsdom`, assert computed style `overflow-y` |
| Visual | SettingsPage mobile viewport (375px) | Manual check iOS Safari + Android Chrome |

---

## Migration / Rollout

- **D1 Wallet repair**: No migration; `_repair_wallet` runs on next login. No credit duplication risk — valid wallets preserved.
- **D2 Balance**: No migration; next BillingPage mount triggers refresh with retry.
- **D3 Stripe**: No migration; flag derived at boot. Railway env vars must be set before deploy.
- **D4 Settings**: CSS-only; instant rollback if needed.
- **D5 n8n**: New service deploy; does not affect existing backend/frontend. SQLite default, no DB migration.

---

## Open Questions

- [ ] D5: Should n8n use the shared PostgreSQL if SPHERE adopts one later, or stay SQLite? Decision: SQLite for now, migrate later.
