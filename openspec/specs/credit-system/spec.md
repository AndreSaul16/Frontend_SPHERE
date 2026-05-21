# credit-system

> **Source**: fix-platform-stability (archived 2026-05-14), ragnarok-production-audit-v2 (archived 2026-05-21)
> **TDD**: ACTIVE (pytest, vitest)

## Requirements

| ID | Requirement | N |
|----|------------|---|
| CS-001 | `_ensure_wallet` MUST re-initialize invalid wallets (`null`, `{}`, missing `pro_messages_balance`) | 3 |
| CS-002 | Valid wallets MUST NOT be overwritten | 1 |
| CS-003 | Admin repair endpoint SHALL fix invalid wallets for existing users | 2 |
| CS-004 | ChatPanel.tsx MUST NOT call `decrementOptimistic()` (single decrement in `api.ts` only) | 2 |
| CS-005 | Board meeting flow MUST skip per-agent credit charge when `board_mode` is set | 1 |
| CS-006 | `_auto_provision_user` MUST set `board_meeting_enabled: True` and `board_iterations: 1` | 1 |
| CS-007 | ChatPanel MUST display real latency/token metrics or nothing; MUST NOT hardcode `"24ms"` / `"0.8k/min"` | 2 |

### CS-001: Wallet Hardening

- GIVEN `wallet: {}`  WHEN `_ensure_wallet` is called  THEN init with `pro_messages_balance: 5`
- GIVEN `wallet: null`  WHEN `_ensure_wallet` is called  THEN init with `pro_messages_balance: 5`
- GIVEN `wallet: {topup_messages_balance: 0}` (no pro key)  WHEN `_ensure_wallet` runs  THEN re-init

### CS-002: Valid Wallet Preservation

- GIVEN wallet `{pro_messages_balance: 3, topup_messages_balance: 0}`  WHEN `_ensure_wallet` runs  THEN balance unchanged

### CS-003: Repair Endpoint

- GIVEN user with wallet `{}`  WHEN repair called  THEN wallet initialized, user can send messages
- GIVEN user with valid wallet (balance 3)  WHEN repair called  THEN balance remains 3

### CS-004: Single Credit Decrement

- GIVEN user clicks Send
  WHEN `streamChat()` starts in `api.ts`
  THEN `decrementOptimistic()` is called ONCE (in `api.ts`)

- GIVEN `handleSendMessage` executes in ChatPanel.tsx
  WHEN the message is processed
  THEN ChatPanel.tsx does NOT call `decrementOptimistic()`

### CS-005: Board Meeting Credit Handling

- GIVEN `board_mode` flag is true
  WHEN an agent node executes
  THEN credit manager does NOT charge per-agent (stream-level `already_charged` covers it)

### CS-006: Board Meeting Defaults

- GIVEN `_auto_provision_user()` creates a new user document
  WHEN the user doc is inserted into MongoDB
  THEN `board_meeting_enabled` field equals `True`
  AND `board_iterations` field equals `1`

### CS-007: Real Metrics Display

- GIVEN SSE stream has completed
  WHEN time-to-first-token and total token count are measurable
  THEN ChatPanel displays the actual measured values

- GIVEN no measurement data is available (stream not started, error, or incomplete)
  WHEN ChatPanel renders the metrics section
  THEN no fake metrics are shown (no `"Latencia: 24ms"`, no `"Tokens: 0.8k/min"`)
