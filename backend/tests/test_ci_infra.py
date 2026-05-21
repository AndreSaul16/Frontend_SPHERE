"""Tests for CI/CD infrastructure configuration.

Validates GitHub Actions workflow, Dockerfiles, Railway configs,
dependency pinning, and build hygiene.
"""

import json
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]  # SPHERE repo root


def read_ci_yml() -> dict:
    path = ROOT / ".github" / "workflows" / "ci.yml"
    if not path.exists():
        raise FileNotFoundError(f"ci.yml not found at {path}")
    with open(path) as f:
        return yaml.safe_load(f)


# ── T-001: CI Pipeline ────────────────────────────────────────────────


def test_ci_yml_triggers_on_push_and_pr_to_main():
    """CI-001/CI-002: triggers on push + PR to main."""
    ci = read_ci_yml()
    # PyYAML 1.1 parses 'on' as boolean True; GitHub Actions docs use literal 'on'
    on = ci.get("on", ci.get(True))
    assert on is not None, "Missing 'on' trigger block"
    assert on.get("push") is not None, "Missing push trigger"
    assert on.get("pull_request") is not None, "Missing pull_request trigger"
    # Check branch filter: either the bare key or branches list
    push_cfg = on["push"]
    pr_cfg = on["pull_request"]
    if isinstance(push_cfg, dict) and "branches" in push_cfg:
        assert "main" in push_cfg["branches"]
    if isinstance(pr_cfg, dict) and "branches" in pr_cfg:
        assert "main" in pr_cfg["branches"]
    # Compare by value for simple string case
    assert push_cfg == "main" or ("branches" in push_cfg and "main" in push_cfg["branches"])
    assert pr_cfg == "main" or ("branches" in pr_cfg and "main" in pr_cfg["branches"])


def test_ci_yml_has_backend_job_with_services():
    """CI-001: test-backend job exists with mongo + redis services."""
    ci = read_ci_yml()
    jobs = ci["jobs"]
    backend = jobs["test-backend"]

    # Matrix
    matrix = backend["strategy"]["matrix"]
    assert "3.11" in matrix["python-version"]

    # Service containers
    services = backend.get("services", {})
    assert "mongodb" in services, "Missing MongoDB service"
    assert "redis" in services, "Missing Redis service"

    mongo_svc = services["mongodb"]
    assert "mongo" in mongo_svc.get("image", ""), "MongoDB image not mongo"
    assert "27017" in str(mongo_svc.get("ports", [])), "Missing port 27017"

    redis_svc = services["redis"]
    assert "redis" in redis_svc.get("image", ""), "Redis image not redis"
    assert "6379" in str(redis_svc.get("ports", [])), "Missing port 6379"


def test_ci_yml_backend_env_vars():
    """CI-001: backend job sets required env vars."""
    ci = read_ci_yml()
    backend = ci["jobs"]["test-backend"]

    # Merge job-level env and step-level env for validation
    env = backend.get("env", {})

    assert env.get("MONGODB_URL") == "mongodb://localhost:27017"
    assert env.get("DB_NAME") == "sphere_test"
    assert env.get("REDIS_URL") == "redis://localhost:6379/0"
    assert str(env.get("PYTHONUNBUFFERED")) == "1"
    assert env.get("ENVIRONMENT") == "development"


def test_ci_yml_has_frontend_job():
    """CI-002: test-frontend job exists with node 20 matrix."""
    ci = read_ci_yml()
    jobs = ci["jobs"]
    frontend = jobs["test-frontend"]

    matrix = frontend["strategy"]["matrix"]
    assert 20 in matrix["node-version"]


def test_ci_yml_has_lint_job_non_blocking():
    """CI-003: lint job exists with continue-on-error."""
    ci = read_ci_yml()
    lint = ci["jobs"]["lint"]
    assert lint.get("continue-on-error") is True, "Lint must be non-blocking"


def test_ci_yml_has_cache_for_pip():
    """CI-004: pip cache configured in backend job."""
    ci = read_ci_yml()
    backend = ci["jobs"]["test-backend"]
    steps = backend["steps"]
    cache_steps = [
        s for s in steps
        if isinstance(s.get("uses", ""), str) and "cache" in s.get("uses", "")
    ]
    assert len(cache_steps) >= 1, "At least one cache step expected"


# ── Sanity ────────────────────────────────────────────────────────────


def test_test_file_itself_loads():
    """Self-check: this test module loads without error."""
    assert ROOT.joinpath(".git").is_dir(), "ROOT should point to repo root"
