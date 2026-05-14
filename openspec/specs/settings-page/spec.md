# settings-page

> **Source**: fix-platform-stability (archived 2026-05-14)
> **TDD**: ACTIVE (vitest)

## Requirements

| ID | Requirement | N |
|----|------------|---|
| SP-001 | SettingsPage MUST scroll vertically on mobile while keeping tab bar fixed | 2 |

### SP-001: Mobile Scroll

- GIVEN mobile viewport (375x812)  WHEN content overflows  THEN main area scrolls; blobs use `pointer-events-none`
- GIVEN page scrolled to bottom  WHEN tab bar renders  THEN remains sticky/visible
