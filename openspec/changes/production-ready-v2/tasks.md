# Tasks: Production Ready de verdad — Second Production-Readiness Pass

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 180–240 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main (single PR; user preference) |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | All 4 phases — rate limiter fix, email gate tests, billing fix, hygiene cleanup | Single PR | ~200 lines; all backend + 2 test files |

## Phase 1: P0 — Fix rate limiter availability

- [ ] 1.1 Verify pyrate_limiter v4 `try_acquire(blocking=False)` API by checking installed version against PyPI docs. Confirm default changed from non-blocking to blocking in v4.
- [ ] 1.2 Fix `stream.py:320` — change `limiter.try_acquire(user_id)` → `limiter.try_acquire(user_id, blocking=False)`. Add `pyrate_limiter` to `requirements.txt` (direct dependency, currently only transitive via fastapi-limiter).
- [ ] 1.3 Add test `test_try_acquire_returns_429_immediately_not_blocks` in `backend/tests/test_rate_limit.py` — verify bucket-full returns False immediately (no sleep/hang).

## Phase 2: P1 — Email gate coverage

- [ ] 2.1 Create `unverified_user_profile` fixture in `conftest.py` — extend `_make_user_profile` with `email_verified` parameter; set `subscription.status = "email_unverified"` and `pro_messages = 0` when False.
- [ ] 2.2 Create `backend/tests/test_email_gate.py` with 5 tests: unverified user gets 0 balance, verified gets 5 credits, 403 on unverified stream POST, 200 on verified stream POST, dev-token bypasses email gate (always verified).

## Phase 3: P2 — Stream billing + token cap

- [ ] 3.1 Add test in `test_stream_billing.py`: `board_classifier_node` propagates `already_charged` through board meeting graph.
- [ ] 3.2 Add test in `test_stream_billing.py`: `next_iteration_node` propagates `already_charged` through board meeting graph.
- [ ] 3.3 Add end-to-end test: stream POST charges exactly once — verify second agent_node call skips with `already_charged=True`.
- [ ] 3.4 **CRITICAL** — Wire `cm.aadjust_after_completion()` in `stream.py` `generate_chat_events()` after the `astream_events` loop completes. Currently gated behind `already_charged=False` in `orchestrator.py:417` but charge was moved to stream with `already_charged=True`, leaving token cap unenforced on stream path.

## Phase 4: Hygiene — Dead code removal + docs + token cap verify

### Decision A (A1): Delete legacy /chat
- [ ] 4.1 Remove `/chat` router registration from `main.py`.
- [ ] 4.2 Delete `backend/routes/chat.py` (no active callers — zero frontend consumers per exploration grep).
- [ ] 4.3 Remove `RATE_LIMIT_CHAT_PER_MINUTE` from `config.py`.
- [ ] 4.4 Remove dead `chatService.sendMessage()` from `frontend/src/services/api.ts` (0 component callers).

### Decision B (B1): Document low test balances
- [ ] 4.5 Add comment in `conftest.py` above `_PLAN_WALLETS` explaining 5/50/100 test balances are intentional (20x below production config) to make credit-exhaustion tests fast.

### Decision C (C1): Verify token cap
- [ ] 4.6 Verify `credit_manager.py:103-137` token cap logic — confirm `TOKEN_CAP_PER_MESSAGE = 4000` and `_charge_extra` flow work correctly with stream path after Phase 3.4 fix.
- [ ] 4.7 Add integration test: stream with 4k+ tokens triggers extra charge via `aadjust_after_completion`.
