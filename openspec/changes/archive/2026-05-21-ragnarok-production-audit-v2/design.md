# Design: SPHERE Production Readiness — Re-Audit v2

## Technical Approach

Fix 14 production issues across backend (Clean Architecture) and frontend (React 19 + Zustand 5 + TypeScript strict). Phased: CRITICAL (provider routing, core agents, rate limiter) → HIGH (credit system, agent persistence, metrics) → MEDIUM/LOW (scaffolding, dead code).

## Architecture Decisions

### Model Provider Routing

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Inline if/else in `agent_node()` | Simple but scattered; duplicate in board_classifier | Rejected |
| `ModelProviderRegistry` class with static mapping | Single source of truth; testable; env-var aware | **Chosen** |

**Implementation**: New file `backend/app/core/model_registry.py` exposes `resolve_provider(model: str) -> dict` returning `{api_key, base_url}`. Maps `gpt-*` → `settings.OPENAI_API_KEY` + `"https://api.openai.com/v1"`, `deepseek-*` → `settings.DEEPSEEK_API_KEY` + `settings.DEEPSEEK_BASE_URL`. Fallback: DeepSeek (preserves backwards compat). `agent_node()` (line 390) and `board_classifier.py` (line 22) call `resolve_provider(resolved.model)` instead of hardcoding.

### Core Agents Endpoint

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Hardcode metadata in endpoint | Backend becomes source of truth; simple | **Chosen** |
| Derive from DB collection | Adds migration; core agents aren't user-owned | Rejected |

**Implementation**: New `GET /api/v1/agents/core` in `agents.py` returns 5 agents as JSON array. Each: `{id, name, role, description, capabilities, color, hexColor, isOnline, avatar}`. Names/roles from `DEFAULT_CORE_PROMPTS` keys (CEO→Oberon, CTO→Nexus, etc.). Order preserved: `group-chat` first. Frontend: `chatService.getCoreAgents()` fetches; `useChatStore.fetchCustomAgents` renamed `refreshAgents` (loads core + custom). `MOCK_AGENTS` const removed. Core agents initialize as `[]`.

### Rate Limiter Singleton

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Module-level dict `_rate_limiters: Dict[str, Limiter]` | Simple; per-plan; in-process; no Redis needed | **Chosen** |
| Redis-only distributed | Adds latency; unnecessary for 2 workers | Rejected |

**Implementation**: Lazy-init singleton dict in `stream.py`. `_get_limiter(plan_id)` creates `Limiter(Rate(...))` on first access, reuses thereafter. Remove per-request `Limiter(rate)` (line 364-367). Thread safety: FastAPI single event loop, `try_acquire` is synchronous — no contention. Separate from `fastapi_limiter` Redis (different concern).

### Agent Persistence (HIGH-09)

**Choice**: Store core agent overrides in user document `agent_overrides` field (`{agent_id: {name?, color?}}`). New `PATCH /api/v1/agents/core/{agent_id}` endpoint (separate from existing custom-agent PATCH). Frontend: `renameAgent`/`updateAgentColor` become async, call API, update store on success.

**Rationale**: Core agents aren't in the custom-agents DB collection. A user-doc subfield avoids a new collection while keeping overrides per-user. Existing `agent_overrides` collection (line 6 of agent_resolver) is for prompt/temperature overrides, not UI metadata — separate concern.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/core/model_registry.py` | Create | `resolve_provider(model)` — maps model prefix → API key/base URL |
| `backend/app/application/orchestrator.py` | Modify | `agent_node()` uses `resolve_provider()` instead of hardcoded DeepSeek (line 390-397) |
| `backend/app/application/board_classifier.py` | Modify | `classifier_llm` uses `resolve_provider()` (line 22-28) |
| `backend/app/presentation/api/v1/agents.py` | Modify | Add `GET /agents/core` + `PATCH /agents/core/{agent_id}` |
| `backend/app/core/auth.py` | Modify | `_auto_provision_user()` adds `board_meeting_enabled: True`, `board_iterations: 1` |
| `backend/app/presentation/api/v1/stream.py` | Modify | Singleton limiter dict replaces per-request `Limiter(rate)` |
| `frontend/src/services/api.ts` | Modify | Export `API_URL`; add `getCoreAgents()`, `updateCoreAgent()` |
| `frontend/src/store/useChatStore.ts` | Modify | Remove `MOCK_AGENTS`; `refreshAgents` loads core+custom; async `renameAgent`/`updateAgentColor` |
| `frontend/src/components/chat/ChatPanel.tsx` | Modify | Remove `decrementOptimistic()` (line 144); remove hardcoded "24ms"/"0.8k/min" (lines 469-470); add latency/token measurement via `useRef` |
| `frontend/src/pages/settings/ServiceCredentialsSettings.tsx` | Modify | Import `API_URL`; prefix 4 fetch URLs |

## Data Flow

```
Model Routing:
  agent_resolver.py → resolved.model → model_registry.resolve_provider()
  → ChatOpenAI(api_key=OPENAI_API_KEY, base_url=https://api.openai.com/v1)

Core Agents:
  useChatStore.refreshAgents() → GET /agents/core (5 agents)
  → chatService.getCustomAgents() (user's agents)
  → merged Agent[] for UI

Rate Limiter:
  stream endpoint → _get_limiter(plan_id).try_acquire(user_id)
  → singleton counter survives between requests
  → 429 if threshold exceeded

Credit Decrement:
  ChatPanel.handleSendMessage → sendMessage(store) → chatService.streamChat()
  → on stream OK: decrementOptimistic() in api.ts (ONLY point)
  → ChatPanel NO LONGER decrements

Agent Persistence:
  renameAgent(id, name) → PATCH /agents/core/{id} {name}
  → backend writes user_doc.agent_overrides.{id}.name
  → store updated on response
```

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit (pytest) | `resolve_provider()` with gpt/deepseek/unknown models | Parametrized test: assert correct API key per prefix |
| Unit (pytest) | `GET /agents/core` returns 5 agents with required fields | FastAPI TestClient, verify JSON schema |
| Unit (pytest) | Singleton limiter accumulates between calls | Two sequential `try_acquire` calls, assert counter increment |
| Unit (vitest) | `refreshAgents` merges core + custom agents | Mock fetch, assert `getAgents()` length |
| Unit (vitest) | `renameAgent` calls API and updates store | Spy on `chatService.updateCoreAgent`, assert store mutation |
| Unit (vitest) | Credit decrement only in api.ts (not ChatPanel) | Verify `decrementOptimistic` called exactly once per send flow |
| Integration | Board meeting enabled for new users | E2E: register new user, assert `board_meeting_enabled` in GET /me response |

## Migration / Rollout

No database migrations. Board meeting defaults applied to new users via `$setOnInsert`. Existing users: board meeting setting unchanged (opt-in via Settings page). Rate limiter: in-process singleton means state resets on deploy — acceptable for 2-worker setup. All changes are per-commit revertable.

## Phase 3-4 (MEDIUM/LOW): Brief Notes

- **n8n scaffolds**: Create `backend/n8n/workflows/` dir, add `.gitkeep`, document in code comment.
- **console.error gate**: Wrap all `console.error` in `import.meta.env.DEV` checks across frontend.
- **Logout handler**: `ProfilePage.tsx` — wire `onClick` to Firebase `signOut()` + `resetState()`.
- **Jules test**: Add `stub=True` mode in `create_jules_task` tool; `app/infrastructure/tools/jules_tool.py`.
- **Dead buttons, paperclip, delete error**: Basic wiring/cleanup in ProfilePage, ChatPanel, useChatStore.
