# Proposal: SPHERE Production Readiness — Re-Audit v2

## Intent

Fix 14 verified production-blocking issues from the second SPHERE audit. CRITICAL issues (broken model switching, hardcoded agents, no-op rate limiter) block any real user. HIGH issues (double charging, lost customizations, broken URLs) degrade UX severely.

## Scope

### In Scope
- **CRITICAL (3)**: Model provider routing, `/agents/core` endpoint, functional rate limiting
- **HIGH (5)**: Board meeting default ON, single credit decrement, agent rename/color persistence, absolute API URLs, real metrics
- **MEDIUM (3)**: n8n workflow files, DEV-wrap console.error, logout handler
- **LOW (6)**: Jules test fix, delete feedback, dead button handlers, paperclip removal

### Out of Scope
- New AI providers beyond OpenAI/DeepSeek
- n8n workflow content (scaffolding only)
- Redis-based distributed rate limiting
- Full orchestrator refactor

## Capabilities

### New Capabilities
- `model-provider-routing`: Route to correct provider API by model name
- `core-agents-endpoint`: `GET /api/v1/agents/core` serves server-defined core agents
- `rate-limiting`: Singleton counter per endpoint with TTL

### Modified Capabilities
- `credit-system`: Remove duplicate `decrementOptimistic()` in ChatPanel (HIGH-08)
- `settings-page`: Absolute API URLs in ServiceCredentialsSettings fetch calls (HIGH-10)

## Approach

**Phase 1 — CRITICAL (before any user)**:
1. `ModelProviderRegistry` maps model prefixes → API keys/URLs. `orchestrator.py:392` resolves provider from model name instead of hardcoding DeepSeek.
2. `GET /api/v1/agents/core` reads from server config (JSON/env). `useChatStore.ts` fetches from endpoint, removes `MOCK_AGENTS`.
3. Module-level `Limiter` singleton with TTL dict replaces per-request instances in `stream.py` + `main.py`.

**Phase 2 — HIGH (before public launch)**:
4. Add `board_meeting_enabled: True` to `_auto_provision_user()` new user dict.
5. Remove `decrementOptimistic()` from `ChatPanel.tsx:144`; keep only in `api.ts` stream path.
6. `PATCH /api/v1/agents/{id}` endpoint for rename/color; store calls API on mutation.
7. Import `API_URL` from config, prefix 4 fetch calls in `ServiceCredentialsSettings.tsx`.
8. Replace hardcoded `"24ms"`/`"0.8k/min"` with `useRef`-measured metrics or remove UI element.

**Phase 3 — MEDIUM**: n8n workflow scaffold directory, `import.meta.env.DEV` gating on console.error, logout onClick handler.

**Phase 4 — LOW**: Dead profile buttons, Jules test stub, share placeholder, paperclip removal, deleteCustomAgent error feedback.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `orchestrator.py` | Modified | Model provider routing (CRIT-05) |
| `agents.py` (API) | Modified | Core agents endpoint + PATCH update (CRIT-06, HIGH-09) |
| `stream.py`, `main.py` | Modified | Rate limiter singleton (CRIT-07) |
| `auth.py` | Modified | Board meeting default ON (HIGH-07) |
| `useChatStore.ts` | Modified | Remove MOCK_AGENTS, agent persistence |
| `ChatPanel.tsx` | Modified | Credit decrement fix, real metrics |
| `api.ts` | Modified | Core agents fetch, agent update PATCH |
| `ServiceCredentialsSettings.tsx` | Modified | Absolute API URLs |
| `ProfilePage.tsx` | Modified | Logout/dead button handlers |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Model routing breaks existing DeepSeek flow | Low | Registry defaults unchanged; add OpenAI routes only |
| Core agents ordering changes from MOCK_AGENTS | Med | Preserve same order in endpoint response |
| Singleton rate limiter leaks under high load | Low | TTL expiring dict entries; single-worker deployment |
| Board meeting default ON triggers unwanted credit usage | Low | User can disable in Settings; documented opt-out |

## Rollback Plan

Per-commit revert: model routing (1 line), core agents (keep MOCK_AGENTS as fallback), rate limiter (restore per-request instance), others (standard git revert). No database migrations required.

## Dependencies

- OpenAI API key available as environment variable for provider routing

## Success Criteria

- [ ] GPT-4o routes to OpenAI API, not DeepSeek
- [ ] Core agents load from backend endpoint without MOCK_AGENTS
- [ ] Rate limiter rejects requests after per-window threshold exceeded
- [ ] New users have board meeting enabled by default
- [ ] Single credit decremented per message (no double charge)
- [ ] Agent rename/color survives page refresh
- [ ] Service credentials page works in production without Vite proxy
- [ ] All 14 issues verified fixed via same two-pass audit methodology
