# Delta for settings-page

> Modifies existing spec: `openspec/specs/settings-page/spec.md` (SP-001 unchanged)

## ADDED Requirements

| ID | Requirement | N |
|----|------------|---|
| SP-002 | ServiceCredentialsSettings MUST prefix all fetch URLs with `API_URL` constant | 2 |

### SP-002: Absolute API URLs

- GIVEN `API_URL` is `"https://api.sphere.ai"`
  WHEN ServiceCredentialsSettings fetches service credentials
  THEN the fetch URL is `"https://api.sphere.ai/api/v1/me/service-credentials"`
  AND NOT the relative path `"/api/v1/me/service-credentials"`

- GIVEN any credential operation (Notion, Google, LinkedIn, n8n)
  WHEN a fetch request is constructed in ServiceCredentialsSettings.tsx
  THEN the URL string starts with the `API_URL` constant from config
