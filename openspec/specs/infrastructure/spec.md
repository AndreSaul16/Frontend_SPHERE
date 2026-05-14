# infrastructure

> **Source**: fix-platform-stability (archived 2026-05-14)
> **TDD**: N/A (infrastructure config)

## Requirements

| ID | Requirement | N |
|----|------------|---|
| IN-001 | n8n MUST be deployable via Railway config with required env vars | 2 |

### IN-001: n8n Deployment

- GIVEN `railway.toml` or `railway.json`  WHEN validated  THEN n8n service exists, image `n8nio/n8n:latest`
- GIVEN n8n boots on Railway  THEN `N8N_HOST`, `N8N_PORT`, `N8N_PROTOCOL`, `WEBHOOK_URL` set; service reachable
