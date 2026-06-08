# rate-limiting

## Purpose

Enforce per-plan API rate limits using a persistent singleton counter, replacing the current per-request Limiter instances that never accumulate.

## Requirements

| ID | Requirement | N |
|----|------------|---|
| RL-001 | Limiter MUST be a module-level singleton (not created per request) | 1 |
| RL-002 | Per-plan rate thresholds MUST be enforced (free, pro, enterprise) | 1 |
| RL-003 | Limiter counter state MUST survive between requests in-process | 1 |
| RL-004 | Requests exceeding per-window threshold MUST return 429 | 1 |

### RL-001: Singleton Limiter

- GIVEN two concurrent requests to the same endpoint
  WHEN both call `limiter.try_acquire()`
  THEN both observe the same Limiter instance and cumulative counter

### RL-002: Per-Plan Limits

- GIVEN user on free plan
  WHEN request count within time window reaches free-tier limit
  THEN subsequent requests are rejected
  AND pro users have a higher threshold than free users

### RL-003: State Persistence Between Requests

- GIVEN request #1 consumes 1 quota unit from the singleton limiter
  WHEN request #2 arrives (same process)
  THEN the remaining quota reflects request #1's consumption

### RL-004: Threshold Enforcement

- GIVEN rate limit counter equals or exceeds plan threshold
  WHEN a new request arrives
  THEN response status is 429 Too Many Requests
  AND response body includes `Retry-After` header
