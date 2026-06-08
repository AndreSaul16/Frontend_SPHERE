# core-agents-endpoint

## Purpose

Serve core agent definitions from the backend API, eliminating the hardcoded `MOCK_AGENTS` constant in the frontend. Support agent metadata persistence (rename, color) via PATCH.

## Requirements

| ID | Requirement | N |
|----|------------|---|
| CAE-001 | `GET /api/v1/agents/core` MUST return all 5 core agents | 2 |
| CAE-002 | Each agent MUST include id, name, role, description, capabilities, color | 1 |
| CAE-003 | Unauthenticated requests MUST return 401 | 1 |
| CAE-004 | Frontend (`useChatStore`) MUST load agents from endpoint, not `MOCK_AGENTS` | 1 |
| CAE-005 | `PATCH /api/v1/agents/{id}` MUST persist agent rename to database | 1 |
| CAE-006 | `PATCH /api/v1/agents/{id}` MUST persist agent color to database | 1 |

### CAE-001: Core Agents Count

- GIVEN authenticated request
  WHEN `GET /api/v1/agents/core` is called
  THEN response body contains exactly 5 agents

- GIVEN no Bearer token
  WHEN `GET /api/v1/agents/core` is called
  THEN response is 401 Unauthorized

### CAE-002: Agent Metadata Format

- GIVEN core agents endpoint responds with 200
  WHEN response is parsed as JSON
  THEN each agent object has fields: `id` (string), `name` (string), `role` (string), `description` (string), `capabilities` (string[]), `color` (string)

### CAE-003: Authentication Required

- GIVEN request without valid Bearer token
  WHEN `GET /api/v1/agents/core` is called
  THEN response status is 401 Unauthorized

### CAE-004: Frontend Integration

- GIVEN `useChatStore` initializes
  WHEN core agents are loaded
  THEN agent data comes from `GET /api/v1/agents/core` fetch, NOT from the `MOCK_AGENTS` TypeScript constant

### CAE-005: Agent Rename Persistence

- GIVEN user calls `renameAgent(agentId, newName)`
  WHEN page is refreshed
  THEN agent displays the new name (persisted from backend `PATCH`)

### CAE-006: Agent Color Persistence

- GIVEN user calls `updateAgentColor(agentId, newColor)`
  WHEN page is refreshed
  THEN agent displays the new color (persisted from backend `PATCH`)
