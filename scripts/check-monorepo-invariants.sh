#!/usr/bin/env bash
# check-monorepo-invariants.sh — Guard against root-level config contamination.
#
# SPHERE is a LOCAL monorepo but TWO separate GitHub repos:
#   - Backend_SHPERE  (backend/)
#   - Frontend_SPHERE (frontend/)
#
# Both repos receive the FULL monorepo on push. This guard verifies that
# root-level config is properly scoped to avoid affecting both services.
#
# Exit codes:  0 = clean, 1 = argument error, 2 = violation found
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VIOLATIONS=0

usage() {
    cat <<EOF
Usage: $(basename "$0")

Verifies root-level config is properly scoped per service.
Checks:
  - No unscoped .github/workflows/ at monorepo root
  - No railway.toml at monorepo root
  - No Dockerfile* at monorepo root

Exit codes:  0 = clean, 1 = argument error, 2 = violations found
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

echo "=== SPHERE Monorepo Invariant Check ==="
echo "   Root: $REPO_ROOT"
echo ""

# --- Check 1: .github/workflows/ scoping ---
if [[ -d "$REPO_ROOT/.github/workflows" ]]; then
    echo "ℹ️  .github/workflows/ found at monorepo root — checking scope…"
    echo ""

    UNscoped=0
    for wf in "$REPO_ROOT/.github/workflows"/*.yml "$REPO_ROOT/.github/workflows"/*.yaml; do
        [[ -f "$wf" ]] || continue
        wfname=$(basename "$wf")

        # Check for paths filter
        if grep -qE '^\s+paths:\s*$' "$wf" 2>/dev/null; then
            echo "   ✅ $wfname — has paths filter (scoped)"
        elif grep -q "paths:" "$wf" 2>/dev/null; then
            echo "   ✅ $wfname — has paths filter (scoped)"
        else
            echo "   ⚠️  $wfname — WARNING: no paths filter (will run on BOTH repos)"
            UNscoped=$((UNscoped + 1))
        fi
    done
    echo ""

    if [[ $UNscoped -gt 0 ]]; then
        echo "❌ FAIL: $UNscoped workflow(s) without paths scoping"
        echo "   WHY: Unscoped workflows run on BOTH Backend_SHPERE and"
        echo "   Frontend_SPHERE on every push. This can cause the SKIPPED"
        echo "   incident if a required check fails on the wrong repo."
        echo "   FIX: Add paths: ['backend/**'] or paths: ['frontend/**'] to each workflow."
        echo ""
        VIOLATIONS=$((VIOLATIONS + 1))
    else
        echo "✅ PASS: All workflows are scoped with paths filters"
    fi
else
    echo "✅ PASS: No .github/workflows/ at root"
fi

# --- Check 2: railway.toml ---
if [[ -f "$REPO_ROOT/railway.toml" ]]; then
    echo "❌ FAIL: railway.toml found at monorepo root"
    echo "   WHY: railway.toml at root would configure BOTH backend and"
    echo "   frontend services from a single file. Each service has its own"
    echo "   Railway configuration via the dashboard."
    echo "   FIX: Remove root railway.toml; configure per-service in Railway UI."
    echo ""
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo "✅ PASS: No railway.toml at root"
fi

# --- Check 3: Dockerfile* ---
DOCKERFILES=$(find "$REPO_ROOT" -maxdepth 1 -name 'Dockerfile*' 2>/dev/null || true)
if [[ -n "$DOCKERFILES" ]]; then
    echo "❌ FAIL: Dockerfile found at monorepo root:"
    for f in $DOCKERFILES; do
        echo "   • $(basename "$f")"
    done
    echo "   WHY: A root Dockerfile risks containerizing both services together."
    echo "   Frontend_SPHERE has rootDirectory='' — a Dockerfile would trigger"
    echo "   a frontend-only build to also pick up backend code."
    echo "   FIX: Place Dockerfiles in backend/ and frontend/ respectively."
    echo ""
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo "✅ PASS: No Dockerfile* at root"
fi

echo ""
echo "=== Result ==="

if [[ $VIOLATIONS -eq 0 ]]; then
    echo "✅ All invariants satisfied — root is clean."
    exit 0
else
    echo "❌ $VIOLATIONS violation(s) found. Fix them before deploying."
    exit 2
fi
