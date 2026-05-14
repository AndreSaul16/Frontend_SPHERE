# Apply Progress: fix-platform-stability — PR 1 (Backend Stability)

**Date**: 2026-05-14
**Branch**: feature/fix-platform-stability
**Mode**: Strict TDD (pytest)
**Delivery**: auto-chain / feature-branch-chain — PR 1 of 3

## Completed Tasks

### Phase 1: Backend Stability (Credit Wallet + Stripe Config)

- [x] 1.1 Fix `_ensure_wallet` guard: `isinstance(dict) and "pro_messages_balance" in wallet` + WARNING log
- [x] 1.2 Add `_repair_wallet()`: idempotent, skip valid wallets, init invalid with 5 credits via `$set`
- [x] 1.3 Add `stripe_configured` property to `Settings`: True when STRIPE_SECRET_KEY non-empty
- [x] 1.4 Extend `_validate_env_vars()`: log CRITICAL if STRIPE_SECRET_KEY missing
- [x] 1.5 Add `stripe_configured` bool field to `GET /billing/me` response
- [x] 1.6 Wallet unit tests: empty dict, None, valid wallet, missing key, repair invalid, repair idempotent
- [x] 1.7 Stripe config tests: key present, empty, whitespace, whitespace-surround, billing/me integration

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | `tests/test_auth.py::TestEnsureWallet` | Unit | ✅ 6/8 | ✅ Written | ✅ Passed | ✅ 4 cases | ✅ Extracted `_is_wallet_valid()` |
| 1.2 | `tests/test_auth.py::TestRepairWallet` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 2 cases | ✅ Uses shared helper |
| 1.3 | `tests/test_billing_api.py::TestStripeConfiguredFlag` | Unit | ✅ 7/9 | ✅ Written | ✅ Passed | ✅ 4 cases | ➖ None needed |
| 1.5 | `tests/test_billing_api.py::TestBillingMeStripeConfigured` | Integration | N/A (new) | ✅ Written | ✅ Passed | ➖ Single | ➖ None needed |

### Test Summary
- **Total tests written**: 11
- **Total tests passing**: 11 (26 of 28 full suite; 2 pre-existing failures unrelated)
- **Layers used**: Unit (10), Integration (1)
- **Approval tests** (refactoring): None — no refactoring tasks
- **Pure functions created**: 1 (`_is_wallet_valid`)

## Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `backend/app/core/auth.py` | Modified | Fixed `_ensure_wallet` guard (L108), added `_is_wallet_valid()`, added `_repair_wallet()`, WARNING logs |
| `backend/app/core/config.py` | Modified | Added `stripe_configured: bool` computed property |
| `backend/main.py` | Modified | Added Stripe validation to `_validate_env_vars()`, CRITICAL log |
| `backend/app/presentation/api/v1/billing.py` | Modified | Added `stripe_configured` to `GET /billing/me` response |
| `backend/tests/test_auth.py` | Modified | Added `TestEnsureWallet` (4 tests) + `TestRepairWallet` (2 tests) |
| `backend/tests/test_billing_api.py` | Modified | Added `TestStripeConfiguredFlag` (4 tests) + `TestBillingMeStripeConfigured` (1 test) |

## Deviations from Design

None — implementation matches design.

## Issues Found

None.

## Remaining Tasks (for PR 2 and PR 3)

### Phase 2: Frontend Experience
- [ ] 2.1 Firebase auth-ready gate to `useBillingStore.refresh()`
- [ ] 2.2 Wire `decrementOptimistic()` in `ChatPanel.tsx`
- [ ] 2.3 Loading skeleton, error state, stripe_configured handling in `BillingPage.tsx`
- [ ] 2.4 Fix scroll in `SettingsPage.tsx`
- [ ] 2.5 Frontend tests

### Phase 3: Infrastructure
- [ ] 3.1 Create `railway.toml` for n8n

### Phase 4: Verification
- [ ] 4.1 Full pytest suite
- [ ] 4.2 Frontend vitest suite
- [ ] 4.3 Manual visual: SettingsPage mobile

## Workload / PR Boundary
- Mode: auto-chain / feature-branch-chain
- Current work unit: Unit 1 (Backend wallet hardening + Stripe config flag)
- Boundary: Phase 1 only (tasks 1.1-1.7)
- Estimated review budget impact: ~320 changed lines (within 400-line budget)

## Status
7/7 tasks complete in Phase 1. Ready for PR 2 (Frontend).
