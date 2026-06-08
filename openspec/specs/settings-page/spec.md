# settings-page

> **Source**: fix-platform-stability (archived 2026-05-14), ragnarok-production-audit-v2 (archived 2026-05-21)
> **TDD**: ACTIVE (vitest)

## Requirements

| ID | Requirement | N |
|----|------------|---|
| SP-001 | SettingsPage MUST scroll vertically on mobile while keeping tab bar fixed | 2 |
| SP-002 | ServiceCredentialsSettings MUST prefix all fetch URLs with `API_URL` constant | 2 |

### SP-001: Mobile Scroll

- GIVEN mobile viewport (375x812)  WHEN content overflows  THEN main area scrolls; blobs use `pointer-events-none`
- GIVEN page scrolled to bottom  WHEN tab bar renders  THEN remains sticky/visible

### SP-002: Absolute API URLs

- GIVEN `API_URL` is `"https://api.sphere.ai"`
  WHEN ServiceCredentialsSettings fetches service credentials
  THEN the fetch URL is `"https://api.sphere.ai/api/v1/me/service-credentials"`
  AND NOT the relative path `"/api/v1/me/service-credentials"`

- GIVEN any credential operation (Notion, Google, LinkedIn, n8n)
  WHEN a fetch request is constructed in ServiceCredentialsSettings.tsx
  THEN the URL string starts with the `API_URL` constant from config
