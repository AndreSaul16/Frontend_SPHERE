# Tasks: fix-platform-stability

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 260–340 |
| 400-line budget risk | **Medium** |
| Chained PRs recommended | **Yes** (12 files, 3 concerns) |
| Suggested split | PR 1 (Backend) → PR 2 (Frontend) → PR 3 (Infra + Verify) |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |
| Decision needed before apply | No |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Backend wallet hardening + Stripe config flag | PR 1 | Base: `feature/fix-platform-stability`. Includes tests. |
| 2 | Frontend balance UX + Stripe graceful + settings scroll | PR 2 | Base: PR 1 branch. Depends on `stripe_configured` API field. |
| 3 | n8n Railway config + full verification | PR 3 | Base: PR 2 branch. Independently deployable. |

---

## Phase 1: Backend Stability (Credit Wallet + Stripe Config)

- [x] 1.1 Fix `_ensure_wallet` guard in `backend/app/core/auth.py:108`: replace `if "wallet" in user_doc` with `isinstance(user_doc.get("wallet"), dict) and "pro_messages_balance" in user_doc["wallet"]`, add WARNING log for invalid wallets
- [x] 1.2 Add `_repair_wallet(uid, user_doc)` function in `backend/app/core/auth.py` (idempotent: skip valid wallets, init invalid ones with 5 credits via `$set`)
- [x] 1.3 Add `stripe_configured: bool` computed property to `backend/app/core/config.py` (True when `STRIPE_SECRET_KEY` is non-empty)
- [x] 1.4 Extend `_validate_env_vars()` in `backend/main.py` to set `settings.stripe_configured`, log CRITICAL if key missing
- [x] 1.5 Add `stripe_configured` bool field to `GET /billing/me` response in `backend/app/presentation/api/v1/billing.py`
- [x] 1.6 **Tests**: `backend/tests/test_auth.py` — parametrize `_ensure_wallet` for `{}`, `null`, missing `pro_messages_balance`, valid wallet (CS-001, CS-002); test `_repair_wallet` idempotency
- [x] 1.7 **Tests**: `backend/tests/test_billing_api.py` — assert `stripe_configured` field, test checkout-disabled when false (BF-003)

## Phase 2: Frontend Experience (Balance UX + Stripe + Scroll)

- [ ] 2.1 Add Firebase auth-ready gate to `useBillingStore.refresh()` in `frontend/src/store/useBillingStore.ts` (poll `auth.currentUser` every 100ms, 5s max) + retry with backoff (1s/2s/4s, 3 attempts) + `isLoading` flag
- [ ] 2.2 Wire `decrementOptimistic()` call in `frontend/src/components/chat/ChatPanel.tsx` after each successful message send
- [ ] 2.3 Add loading skeleton, error state, `stripe_configured` handling (hide buttons + "Pagos no disponibles"), and checkout error alert in `frontend/src/pages/BillingPage.tsx`
- [ ] 2.4 Fix scroll: change `overflow-hidden` → `overflow-y-auto` on root div in `frontend/src/pages/SettingsPage.tsx:50`, add `pointer-events-none` to decorative blobs if present
- [ ] 2.5 **Tests**: `frontend/tests/components/BillingPage.test.tsx` — loading skeleton, error state, Stripe-disabled button absence, checkout error toast (BF-001, BF-002, BF-004)

## Phase 3: Infrastructure (n8n Deployment)

- [ ] 3.1 Create `railway.toml` in project root: n8n service with `n8nio/n8n:latest`, port 5678, env vars `N8N_HOST`, `N8N_PORT`, `N8N_PROTOCOL`, `WEBHOOK_URL` (IN-001)

## Phase 4: Verification

- [ ] 4.1 Run `pytest backend/tests/` — all backend tests pass, CS-001/CS-002/CS-003/IN-001 scenarios verified
- [ ] 4.2 Run `vitest frontend/tests/` — all frontend tests pass, BF-001/BF-002/BF-004/SP-001 scenarios verified
- [ ] 4.3 Manual visual: SettingsPage mobile viewport (375px), verify scroll + sticky tab bar
