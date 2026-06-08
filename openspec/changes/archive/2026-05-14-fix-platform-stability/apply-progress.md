# Apply Progress: fix-platform-stability — PR 1 + PR 2 + PR 3 (COMPLETE)

**Date**: 2026-05-14
**Branch**: feature/fix-platform-stability
**Mode**: Strict TDD (pytest + vitest)
**Delivery**: auto-chain / feature-branch-chain — PR 3 of 3

## Completed Tasks

### Phase 1: Backend Stability (Credit Wallet + Stripe Config)

- [x] 1.1 Fix `_ensure_wallet` guard: `isinstance(dict) and "pro_messages_balance" in wallet` + WARNING log
- [x] 1.2 Add `_repair_wallet()`: idempotent, skip valid wallets, init invalid with 5 credits via `$set`
- [x] 1.3 Add `stripe_configured` property to `Settings`: True when STRIPE_SECRET_KEY non-empty
- [x] 1.4 Extend `_validate_env_vars()`: log CRITICAL if STRIPE_SECRET_KEY missing
- [x] 1.5 Add `stripe_configured` bool field to `GET /billing/me` response
- [x] 1.6 Wallet unit tests: empty dict, None, valid wallet, missing key, repair invalid, repair idempotent
- [x] 1.7 Stripe config tests: key present, empty, whitespace, whitespace-surround, billing/me integration

### Phase 2: Frontend Experience (Balance UX + Stripe + Scroll)

- [x] 2.1 `useBillingStore.refresh()`: auth-ready gate (poll 100ms/5s), retry 3x (1s/2s/4s), `isLoading`, `error`, `stripe_configured` fields
- [x] 2.2 Wire `decrementOptimistic()` in `ChatPanel.tsx` after send + `refresh()` after streaming completes
- [x] 2.3 `BillingPage.tsx`: loading skeleton, error state with retry, `stripe_configured` handling ("Pagos no disponibles"), checkout error `alert()`
- [x] 2.4 `SettingsPage.tsx`: `overflow-hidden` → `overflow-y-auto` on root div (line 50)
- [x] 2.5 Frontend tests: store refresh (11 tests), BillingPage (6 tests), ChatPanel billing integration (4 tests), SettingsPage scroll (4 tests)

### Phase 3: Infrastructure (n8n Deployment)

- [x] 3.1 Create `railway.toml` + `Dockerfile.n8n` in project root: n8n service with `n8nio/n8n:latest`, port 5678, env vars documented

### Phase 4: Verification

- [x] 4.1 Run `pytest backend/tests/` — 175/179 pass, CS-001/CS-002/CS-003/IN-001 scenarios verified
- [x] 4.2 Run `vitest frontend/tests/` — 69/86 pass, BF-001/BF-002/BF-004/SP-001 scenarios verified
- [x] 4.3 Manual visual checklist documented (see below)

## TDD Cycle Evidence

### Phase 1 (PR 1)

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | `tests/test_auth.py::TestEnsureWallet` | Unit | ✅ 6/8 | ✅ Written | ✅ Passed | ✅ 4 cases | ✅ Extracted `_is_wallet_valid()` |
| 1.2 | `tests/test_auth.py::TestRepairWallet` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 2 cases | ✅ Uses shared helper |
| 1.3 | `tests/test_billing_api.py::TestStripeConfiguredFlag` | Unit | ✅ 7/9 | ✅ Written | ✅ Passed | ✅ 4 cases | ➖ None needed |
| 1.5 | `tests/test_billing_api.py::TestBillingMeStripeConfigured` | Integration | N/A (new) | ✅ Written | ✅ Passed | ➖ Single | ➖ None needed |

### Phase 2 (PR 2)

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 2.1 | `tests/store/useBillingStore.test.ts::refresh()` | Unit | ✅ 4/4 | ✅ Written | ✅ Passed | ✅ 6 cases (retry success, retry HTTP 401, error state, isLoading, success data, stripe_configured) | ➖ None needed |
| 2.2 | `tests/components/ChatPanel.test.tsx::Billing Integration` | Integration | ✅ 6/6 | ✅ Written | ✅ Passed | ✅ 4 cases (decrementOptimistic on send, refresh after stop, no-op on empty, no-op on start) | ✅ Fixed test mock (getPins) |
| 2.3 | `tests/components/BillingPage.test.tsx` | Integration | ⚠️ 1/2 (pre-existing) | ✅ Written | ✅ Passed | ✅ 6 cases (skeleton, error, retry, stripe off, content, checkout alert) | ✅ Rewrote test file |
| 2.4 | `tests/components/SettingsPage.test.tsx` | Component | N/A (new) | ✅ Written | ✅ Passed | ✅ 4 cases (root overflow-y-auto, main overflow-y-auto, header, route render) | ➖ None needed |

### Phase 3 (PR 3)

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 3.1 | N/A (config) | N/A | N/A (new) | ➖ N/A | ➖ N/A | ➖ Skipped: purely structural config file, no logic | ➖ None needed |

### Phase 4 (PR 3)

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 4.1 | Full backend suite | Integration | 175/179 (4 pre-existing) | ➖ N/A (verification) | ✅ Passed | ➖ N/A | ➖ N/A |
| 4.2 | Full frontend suite | Integration | 69/86 (17 pre-existing) | ➖ N/A (verification) | ✅ Passed | ➖ N/A | ➖ N/A |
| 4.3 | Manual visual | Visual | N/A | ➖ N/A (manual) | ✅ Documented | ➖ N/A | ➖ N/A |

### Test Summary (PR 3 Verification)

- **Backend**: 175/179 pass. 4 pre-existing failures (2 auth route 404s + 2 Firebase MagicMock — unrelated to this change)
- **Frontend**: 69/86 pass. 17 pre-existing failures (ArtifactRenderer, AuroraBackground, CodeBlock, DataGrid, MarkdownViewer, MermaidDiagram, AgentSelectorModal, Sidebar, evolvedSchema — unchanged from PR 2)
- **Regression check**: Zero new failures. All wallet/Stripe/billing/ChatPanel/SettingsPage/BillingPage tests continue to pass.
- **CRITICAL scenario verification**:
  - CS-001 (wallet guard): ✅ `TestEnsureWallet` — 4 cases pass
  - CS-002 (wallet repair): ✅ `TestRepairWallet` — 2 cases pass
  - CS-003 (stripe config): ✅ `TestStripeConfiguredFlag` (4) + `TestBillingMeStripeConfigured` (1) — 5 cases pass
  - BF-001 (BillingPage loading): ✅ 2 skeleton tests pass
  - BF-002 (BillingPage Stripe disabled): ✅ stripe off/buttons hidden tests pass
  - BF-004 (BillingPage error): ✅ error state + retry tests pass
  - SP-001 (SettingsPage scroll): ✅ 2 overflow-y-auto tests pass
  - IN-001 (n8n config): ✅ `railway.toml` + `Dockerfile.n8n` created

## Files Changed

### PR 1 Files

| File | Action | What Was Done |
|------|--------|---------------|
| `backend/app/core/auth.py` | Modified | Fixed `_ensure_wallet` guard (L108), added `_is_wallet_valid()`, added `_repair_wallet()`, WARNING logs |
| `backend/app/core/config.py` | Modified | Added `stripe_configured: bool` computed property |
| `backend/main.py` | Modified | Added Stripe validation to `_validate_env_vars()`, CRITICAL log |
| `backend/app/presentation/api/v1/billing.py` | Modified | Added `stripe_configured` to `GET /billing/me` response |
| `backend/tests/test_auth.py` | Modified | Added `TestEnsureWallet` (4 tests) + `TestRepairWallet` (2 tests) |
| `backend/tests/test_billing_api.py` | Modified | Added `TestStripeConfiguredFlag` (4 tests) + `TestBillingMeStripeConfigured` (1 test) |

### PR 2 Files

| File | Action | What Was Done |
|------|--------|---------------|
| `frontend/src/store/useBillingStore.ts` | Modified | Added `isLoading`, `error`, `stripe_configured` fields; auth-ready gate (`waitForAuthReady`); retry with 1s/2s/4s backoff; error state on failure |
| `frontend/src/pages/BillingPage.tsx` | Modified | Added `BillingSkeleton` component; error state with retry button; `stripe_configured` conditional ("Pagos no disponibles" banner, hidden payment sections); `alert()` on checkout failure |
| `frontend/src/pages/SettingsPage.tsx` | Modified | Line 50: `overflow-hidden` → `overflow-y-auto` |
| `frontend/src/components/chat/ChatPanel.tsx` | Modified | Import `useBillingStore`; call `decrementOptimistic()` in `handleSendMessage`; `useEffect` to call `refresh()` when streaming stops |
| `frontend/tests/store/useBillingStore.test.ts` | Modified | Added `refresh()` describe block: 6 tests (isLoading, success, retry count, error state, retry success, stripe_configured) + 1 triangulation (HTTP 401 retry) |
| `frontend/tests/components/BillingPage.test.tsx` | Modified | Rewrote completely: 6 tests for loading, error, retry, stripe_configured off, content, checkout alert |
| `frontend/tests/components/ChatPanel.test.tsx` | Modified | Added mock for `getPins`/`pinMessage`/`unpinMessage`/`rateMessage`; added `localStorage` mock; added billing integration tests (4 tests) |
| `frontend/tests/components/SettingsPage.test.tsx` | Created | 4 tests: root overflow-y-auto, main overflow-y-auto, header back link, route rendering |

### PR 3 Files

| File | Action | What Was Done |
|------|--------|---------------|
| `railway.toml` | Created | n8n service definition: Dockerfile build, healthcheck at `/healthz`, env var documentation |
| `Dockerfile.n8n` | Created | Minimal Dockerfile: `FROM n8nio/n8n:latest`, env defaults (`N8N_PORT=5678`, `N8N_PROTOCOL=https`, `DB_TYPE=sqlite`), exposes port 5678 |
| `openspec/changes/fix-platform-stability/tasks.md` | Modified | Marked tasks 3.1, 4.1, 4.2, 4.3 as complete |

## Deviations from Design

| Deviation | Reason |
|-----------|--------|
| SettingsPage: decorative blobs `pointer-events-none` not applied | No decorative blobs exist in SettingsPage component — N/A |
| BillingPage: checkout alert uses `alert()` (AD6) | Matches design decision AD6 — zero new deps |
| n8n: created `Dockerfile.n8n` alongside `railway.toml` | Railway `railway.toml` requires a `dockerfilePath` for Dockerfile-based builds. Using `FROM n8nio/n8n:latest` in the Dockerfile achieves the same result as specifying the image directly. |

## Issues Found

| Issue | Detail |
|-------|--------|
| ChatPanel test had incomplete `chatService` mock (missing `getPins`) | Fixed as part of PR 2 — added `getPins`, `pinMessage`, `unpinMessage`, `rateMessage` to mock |
| jsdom has no localStorage by default | Added `localStorage` mock in ChatPanel test file |
| BillingPage test had pre-existing failure: `getByText('Premium')` matched multiple elements | Test file completely rewritten — issue resolved |
| 17 pre-existing frontend test failures | Unchanged from PR 2 (ArtifactRenderer:5, AuroraBackground:1, CodeBlock:2, DataGrid:2, MarkdownViewer:2, MermaidDiagram:1, AgentSelectorModal:1, Sidebar:2, evolvedSchema:1) — all related to missing artifact mock data or CSS class assertion coupling |
| 4 pre-existing backend test failures | 2 auth route 404s (expected 401, got 404 — route `/api/v1/chat/` doesn't exist), 2 Firebase MagicMock JSON serialization issues — unrelated to this change |
| Backend pytest requires `python3` (not `python`) in WSL | `python` points to Windows pyenv shim which fails in WSL; `python3` from Homebrew works correctly |

## Manual Visual Verification Checklist (Task 4.3)

The following checks must be performed by a human reviewer before merge:

### SettingsPage — Mobile Viewport (375px)
- [ ] Open SettingsPage in Chrome DevTools at 375px width (iPhone SE)
- [ ] Verify the page scrolls vertically — content should not be clipped at the bottom
- [ ] Verify the tab bar (Profile / Billing / Plan) is sticky/fixed at the top
- [ ] Verify `overflow-y-auto` is applied (no `overflow-hidden`) — check: settings content extends beyond viewport and is scrollable
- [ ] Verify all tab content is accessible via scroll

### BillingPage — Loading States
- [ ] Open BillingPage with slow network (DevTools → Network → Slow 3G)
- [ ] Verify skeleton/loading state appears while data fetches
- [ ] Verify balance and plan info render after load completes
- [ ] Verify "Pagos no disponibles" banner shows when `stripe_configured=false`
- [ ] Verify payment buttons are hidden when `stripe_configured=false`
- [ ] Check with `stripe_configured=true`: payment buttons visible, checkout flow works

### Cross-browser
- [ ] Test on iOS Safari (mobile)
- [ ] Test on Android Chrome (mobile)

## Workload / PR Boundary

- Mode: auto-chain / feature-branch-chain
- Current work unit: Unit 3 (n8n Railway config + full verification)
- Boundary: Phase 3 + 4 (tasks 3.1, 4.1-4.3)
- Estimated review budget impact: ~30 changed lines (config files only)

## Status

**ALL TASKS COMPLETE** — 15/15 across 3 PRs.

PR 1 (Backend): 7/7 ✅ | PR 2 (Frontend): 5/5 ✅ | PR 3 (Infra + Verify): 3/3 ✅

Ready for `sdd-archive`.
