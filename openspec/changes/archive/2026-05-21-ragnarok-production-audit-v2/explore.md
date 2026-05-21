# Exploration: SPHERE Production Readiness — Re-Audit (v2)

> **Method**: Two-pass verification: code ↔ ragnarok_deploy.md ↔ previous audit (#121)
> **Date**: 2026-05-20

---

## Executive Summary

**12 fixes from ragnarok_deploy.md**: ALL 12 confirmed applied to the codebase.
**19 issues from previous audit (#121)**: 14 still broken, 3 verified working, 2 eliminated by fixes.

The most urgent issues (3 CRITICAL) remain unresolved:
1. **Model switching is completely non-functional** — every model request goes to DeepSeek API
2. **Core agents hardcoded in frontend** — no dynamic `/agents/core` endpoint
3. **Rate limiter is a no-op** — new counter per request, never increments

The 12 fixes from ragnarok_deploy.md targeted operational safety issues (SSL, ghost users, lock lifecycle, logging) and frontend polish. They did NOT address the architectural problems in the model routing layer.

---

## PASS 1: Verification of 12 Fixes from ragnarok_deploy.md

| # | File | Claimed Fix | Status | Evidence |
|---|------|-------------|--------|----------|
| 1 | `backend/app/presentation/api/v1/stream.py` | Lock moved into generator | ✅ **CONFIRMED** | Line 50: `lock: Optional[DistributedLock]` param in `generate_chat_events`. Lines 332-340: `lock.release()` in generator's `finally`. Lines 310-320: `GeneratorExit` → `credit_manager.arefund()`. Lines 518-522: `except Exception as inner_e: await lock.release(); raise inner_e` |
| 2 | `backend/app/core/auth.py` | Ghost user fix (DuplicateKeyError → find by email) | ✅ **CONFIRMED** | Lines 307-325: DuplicateKey handler looks up `existing = await users_col.find_one({"email": email})`, logs warning, returns existing user |
| 3 | `backend/infrastructure/etl/core/base_spider.py` | TLS certifi applied | ✅ **CONFIRMED** | Line 47: `tlsCAFile=certifi.where()`, `tlsAllowInvalidCertificates=False`. Lines 103, 135: `verify=certifi.where()` on both `requests.get()` |
| 4 | `backend/app/presentation/api/v1/webhooks.py` | `except: pass` → `logger.error()` | ✅ **CONFIRMED** | Lines 155-160: `logger.error(f"Error retrieving subscription {subscription_id} for period_end: {sub_err}...")` |
| 5 | `backend/app/presentation/api/v1/agents.py` | GridFS cleanup `except: pass` → `logger.error()` | ✅ **CONFIRMED** | Lines 314-318: `logger.error(f"Error limpiando archivos GridFS del agente {agent_id}: {gridfs_err}...")` |
| 6 | `backend/app/infrastructure/integrations/providers/notion.py` | Revoke docstring + logger.info | ✅ **CONFIRMED** | Lines 42-54: Docstring explains no public revoke endpoint + `logger.info("Notion token desvinculado...")` |
| 7 | `backend/app/infrastructure/database.py` | Dead `property()` lines removed | ✅ **CONFIRMED** | No `property()` at module level. 272-line file is clean |
| 8 | `frontend/src/pages/ProfilePage.tsx` | Dynamic user data | ✅ **CONFIRMED** | Line 1: `useState, useEffect`. Lines 13-27: `useEffect` loads via `profileService.getProfile()`. Line 111: `<h2>{displayName}</h2>`. Lines 132-136: `defaultValue={displayName}`, `defaultValue={userEmail}` with `readOnly` |
| 9 | `frontend/src/pages/AgentDetailPage.tsx` | Auth headers + 4 models + Spanish accents | ✅ **CONFIRMED** | Lines 250-256: fetchAgent sends `Authorization: Bearer`. Lines 308-314: handleSave sends auth. Lines 350-356: handleDelete sends auth. Line 28: `ALLOWED_MODELS = ["deepseek-chat", "deepseek-r1", "gpt-4o", "gpt-4o-mini"]`. Lines 735-741: Model descriptions for all 4. Spanish: "Identidad del Agente" (L495), "Descripción" (L531), "Configuración Cerebral" (L613) |
| 10 | `frontend/src/pages/BillingPage.tsx` | Simplified authHeaders | ✅ **CONFIRMED** | Lines 7-19: Cleaner inline `authHeaders()` |
| 11 | `frontend/src/services/api.ts` | response.ok checks in 3 custom agent functions | ✅ **CONFIRMED** | Line 254: `getCustomAgents()` has `if (!response.ok) throw Error`. Line 266: `createCustomAgent()` has `if (!response.ok)` with detail. Line 288: `deleteCustomAgent()` has `if (!response.ok) throw Error` |
| 12 | `frontend/src/store/useChatStore.ts` | DEV wraps + comment cleanup | ✅ **CONFIRMED** | Lines 322, 416, 456, 688, 726, 752: `if (import.meta.env.DEV) console.log(...)`. No "Let's assume" or "I should update" comments found |

---

## PASS 2: Re-Audit of 19 Issues from Previous Audit (#121)

### 🔴 CRITICAL (3 issues — ALL STILL BROKEN)

| ID | Severity | Status | File(s) | Lines | Description |
|----|----------|--------|---------|-------|-------------|
| **CRIT-05** | 🔴 Critical | ❌ **BROKEN** | `backend/app/application/orchestrator.py` | 390-397 | **Model switching non-functional.** `agent_node()` resolves `resolved.model` correctly (e.g., `gpt-4o`) but always creates `ChatOpenAI(openai_api_key=DEEPSEEK_API_KEY, openai_api_base=DEEPSEEK_BASE_URL)`. GPT-4o requests are sent to DeepSeek API with model name `gpt-4o` → will fail with 404/model-not-found. `agent_resolver.py` correctly resolves the model string, but the orchestrator ignores it for API routing. |
| **CRIT-06** | 🔴 Critical | ❌ **BROKEN** | `frontend/src/store/useChatStore.ts` | 63-119 | **MOCK_AGENTS still hardcoded.** 5 core agents defined as TypeScript const. No `GET /api/v1/agents/core` endpoint exists. Agent metadata changes require frontend deploy. Adding new core agents requires code changes. |
| **CRIT-07** | 🔴 Critical | ❌ **BROKEN** | `backend/app/presentation/api/v1/stream.py`<br>`backend/main.py` | 364-367<br>347-352 | **Rate limiter creates new counter per request.** `stream.py` creates `limiter = Limiter(rate)` inside the endpoint handler (every request). `main.py` creates `limiter = Limiter(rate)` inside the `_dep` closure (every request). Counter always at 0 → rate limiting never triggers. |

### 🟠 HIGH (5 issues — ALL STILL BROKEN)

| ID | Severity | Status | File(s) | Lines | Description |
|----|----------|--------|---------|-------|-------------|
| **HIGH-07** | 🟠 High | ❌ **BROKEN** | `backend/app/core/auth.py`<br>`backend/app/presentation/api/v1/auth.py` | 243-295<br>545 | **Board Meeting OFF by default.** `new_user` dict in `_auto_provision_user()` does NOT include `board_meeting_enabled`. The API schema defaults to `False` (line 545). New users must manually opt-in via Settings → Board Meeting to get multi-agent discussion. |
| **HIGH-08** | 🟠 High | ❌ **BROKEN** | `frontend/src/components/chat/ChatPanel.tsx`<br>`frontend/src/services/api.ts` | 144<br>87-88 | **Double credit decrement.** `handleSendMessage()` calls `useBillingStore.getState().decrementOptimistic()` at line 144. `streamChat()` also calls `decrementOptimistic()` at lines 87-88. Credit decremented TWICE per message. |
| **HIGH-09** | 🟠 High | ❌ **BROKEN** | `frontend/src/store/useChatStore.ts` | 461-481 | **renameAgent/updateAgentColor never persisted.** Both only update local Zustand state (`coreAgents`/`customAgents` arrays). No API calls. Customizations lost on refresh. Broken feature. |
| **HIGH-10** | 🟠 High | ❌ **BROKEN** | `frontend/src/pages/settings/ServiceCredentialsSettings.tsx` | 72, 102, 133, 152 | **Relative API URLs in 4 fetch calls.** All use `/api/v1/me/service-credentials` without `${API_URL}` prefix. Works in dev (Vite proxy) but breaks in production without proxy config. |
| **HIGH-11** | 🟠 High | ❌ **BROKEN** | `frontend/src/components/chat/ChatPanel.tsx` | 469-470 | **Hardcoded latency/tokens display.** `"Latencia: 24ms"` and `"Tokens: 0.8k/min"` are static strings. Misleading when actual latency differs. |

### 🟡 MEDIUM (5 issues — 2 broken, 2 verified working, 1 eliminated)

| ID | Severity | Status | File(s) | Lines | Description |
|----|----------|--------|---------|-------|-------------|
| **MED-09** | 🟡 Medium | ✅ **WORKING** | `backend/app/application/orchestrator.py`<br>`backend/app/presentation/api/v1/stream.py` | 606-632<br>405-417 | **Board meeting credit flow works correctly.** Stream endpoint always sets `already_charged=True` before the graph. `agent_node()` respects the flag and skips charging. Mechanism is fragile but currently functional. |
| **MED-10** | 🟡 Medium | ✅ **WORKING** | `backend/app/application/orchestrator.py`<br>`backend/main.py` | 127-240<br>lifespan | **Agent prompt templates reference tools correctly.** `load_all_tools()` is called in lifespan before any requests. Tools are registered before `agent_node()` accesses them. |
| **MED-11** | 🟡 Medium | ❌ **BROKEN** | `backend/app/infrastructure/n8n_deployer.py` | 24, 166 | **No n8n workflow JSON files.** Directory `backend/n8n-workflows/` does NOT exist. Deployer references it at line 24. ALL n8n-dependent tool calls (Calendar, WhatsApp, LinkedIn, Instagram, Jules, Stock) fail silently. |
| **MED-12** | 🟡 Medium | ❌ **BROKEN** | Multiple frontend files | scattered | **14 `console.error()` in production.** Files: `BillingPage.tsx` (4), `ChatSettingsPage.tsx` (3), `Sidebar.tsx` (1), `ErrorBoundary.tsx` (2), `MermaidDiagram.tsx` (1), `KnowledgeBasePanel.tsx` (1). None wrapped in `import.meta.env.DEV`. Also 2 in test files (acceptable). |
| **MED-13** | 🟡 Medium | ❌ **BROKEN** | `frontend/src/pages/ProfilePage.tsx` | 188 | **"Logout Protocol" button has no onClick.** Dead UI element in Danger Zone section. User cannot log out from this button. |

### 🟢 LOW (6 issues — ALL STILL PRESENT)

| ID | Severity | Status | File(s) | Lines | Description |
|----|----------|--------|---------|-------|-------------|
| **LOW-05** | 🟢 Low | ❌ **BROKEN** | `backend/app/presentation/api/v1/auth.py` | 504-509 | **Jules test always returns success.** `test_service_credential("jules")` returns `"API key almacenada (test no disponible aún)"` with `success: True`. |
| **LOW-06** | 🟢 Low | ❌ **BROKEN** | `frontend/src/store/useChatStore.ts` | 238-241 | **deleteCustomAgent has no user feedback.** Only `console.error()`, no `errorStates` update. User gets no indication if deletion fails. |
| **LOW-07** | 🟢 Low | ❌ **NOT IMPLEMENTED** | `backend/app/infrastructure/n8n_deployer.py` | 213 | **n8n content diff TODO.** `# TODO: Verificar si el contenido difiere y actualizar` — changes to workflow JSONs won't propagate to n8n. |
| **LOW-08** | 🟢 Low | ❌ **BROKEN** | `frontend/src/pages/ProfilePage.tsx` | 148-155 | **"Cambiar Protocolo de Acceso" and "Generar Nueva API Key" dead buttons.** No onClick handlers. |
| **LOW-09** | 🟢 Low | ❌ **BROKEN** | `frontend/src/components/sidebar/Sidebar.tsx` | 212 | **Share button placeholder.** `onClick={(e) => { e.preventDefault(); /* Placeholder para compartir */ }}`. |
| **LOW-10** | 🟢 Low | ❌ **BROKEN** | `frontend/src/components/chat/ChatPanel.tsx` | 426-431 | **Paperclip button always disabled.** `disabled={isTyping}`, no onClick. Purely decorative. |

---

## Cross-Reference Verification

### ragnarok_deploy.md ↔ Actual Code
- **12/12 fixes confirmed applied.** No discrepancies found.
- The deploy doc accurately documents what was changed.

### Previous Audit (#121) ↔ Actual Code
- **14/19 issues confirmed still present.** The previous audit was accurate.
- **2 issues eliminated** by ragnarok fixes (SSL bypass → certifi, `except: pass` → proper logging).
- **3 issues verified working** (MED-09 credit flow, MED-10 tool registration, MED-03 Notion revoke was fixed).

### Code ↔ Code (Internal Consistency)
- `agent_resolver.py` correctly resolves `resolved.model = "gpt-4o"` but `orchestrator.py:392` hardcodes `openai_api_key=DEEPSEEK_API_KEY` → **inconsistency**.
- `stream.py` sets `board_mode` based on `board_meeting_enabled` from user doc, but `auth.py:_auto_provision_user` never initializes `board_meeting_enabled` → **inconsistency**.
- `useChatStore.ts` has duplicate `isCoreAgent` declaration (lines 254, 274) — minor code hygiene.
- `AgentDetailPage.tsx` line 264 stores description in `avatar_style` field (non-standard mapping) — no functional impact but confusing.

---

## Ready for Proposal

**YES**. All findings are verified with exact file paths and line numbers. The 3 CRITICAL issues block production deployment. The 5 HIGH issues degrade production UX significantly. The remaining MEDIUM/LOW issues can be addressed in follow-up sprints.

### Recommended Proposal Scope

1. **CRIT-05 fix**: Create model provider registry; route `gpt-4o`/`gpt-4o-mini` to OpenAI API, `deepseek-chat`/`deepseek-r1` to DeepSeek API
2. **CRIT-06 fix**: Create `GET /api/v1/agents/core` endpoint; remove MOCK_AGENTS
3. **CRIT-07 fix**: Replace per-request Limiter with module-level singletons or Redis-backed rate limiting
4. **HIGH-07 fix**: Add `board_meeting_enabled: True` to user provisioning
5. **HIGH-08 fix**: Remove duplicate credit decrement from ChatPanel.tsx
6. **HIGH-09 fix**: Add API persistence to renameAgent/updateAgentColor
7. **HIGH-10 fix**: Use `${API_URL}` prefix in ServiceCredentialsSettings
8. **HIGH-11 fix**: Replace hardcoded metrics with real measurements or remove

### Effort Estimate

| Category | Items | Complexity |
|----------|-------|------------|
| CRITICAL | 3 | High (~300 lines) |
| HIGH | 5 | Medium (~200 lines) |
| MEDIUM | 3 fixable | Low (~80 lines) |
| LOW | 6 | Low (~50 lines) |
| **TOTAL** | **17** | **~630 lines** |
