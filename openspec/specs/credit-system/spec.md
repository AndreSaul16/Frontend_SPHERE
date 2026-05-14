# credit-system

> **Source**: fix-platform-stability (archived 2026-05-14)
> **TDD**: ACTIVE (pytest)

## Requirements

| ID | Requirement | N |
|----|------------|---|
| CS-001 | `_ensure_wallet` MUST re-initialize invalid wallets (`null`, `{}`, missing `pro_messages_balance`) | 3 |
| CS-002 | Valid wallets MUST NOT be overwritten | 1 |
| CS-003 | Admin repair endpoint SHALL fix invalid wallets for existing users | 2 |

### CS-001: Wallet Hardening

- GIVEN `wallet: {}`  WHEN `_ensure_wallet` is called  THEN init with `pro_messages_balance: 5`
- GIVEN `wallet: null`  WHEN `_ensure_wallet` is called  THEN init with `pro_messages_balance: 5`
- GIVEN `wallet: {topup_messages_balance: 0}` (no pro key)  WHEN `_ensure_wallet` runs  THEN re-init

### CS-002: Valid Wallet Preservation

- GIVEN wallet `{pro_messages_balance: 3, topup_messages_balance: 0}`  WHEN `_ensure_wallet` runs  THEN balance unchanged

### CS-003: Repair Endpoint

- GIVEN user with wallet `{}`  WHEN repair called  THEN wallet initialized, user can send messages
- GIVEN user with valid wallet (balance 3)  WHEN repair called  THEN balance remains 3
