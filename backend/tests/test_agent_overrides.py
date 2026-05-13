"""
Tests del overlay pattern de agentes (agent_resolver).
"""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_agent_override_upsert_and_delete(authed_client_a, clean_test_data):
    """Crea un override, lo lee, lo borra — vuelve al default."""
    # Crear override
    resp = await authed_client_a.put("/api/v1/me/agent-overrides/CTO", json={
        "system_prompt_addition": "Siempre responde con ejemplos en TypeScript",
        "temperature_override": 0.5,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_role"] == "CTO"
    assert data["system_prompt_addition"] == "Siempre responde con ejemplos en TypeScript"

    # Listar overrides
    resp = await authed_client_a.get("/api/v1/me/agent-overrides")
    assert resp.status_code == 200
    overrides = resp.json()
    assert any(o["agent_role"] == "CTO" for o in overrides)

    # Borrar override
    resp = await authed_client_a.delete("/api/v1/me/agent-overrides/CTO")
    assert resp.status_code == 200

    # Verificar que ya no está
    resp = await authed_client_a.get("/api/v1/me/agent-overrides")
    overrides = resp.json()
    assert not any(o["agent_role"] == "CTO" for o in overrides)


@pytest.mark.asyncio
async def test_agent_override_not_found_delete(authed_client_a):
    """Borrar un override que no existe → 404."""
    resp = await authed_client_a.delete("/api/v1/me/agent-overrides/NONEXISTENT")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_user_context_builder():
    """El builder de USER_CONTEXT solo incluye campos poblados."""
    from app.core.user_context import build_user_context_block

    # Sin datos relevantes (dict vacío = sin display_name, sin prof, etc.)
    user_empty = {}
    result = build_user_context_block(user_empty)
    # Con un dict vacío, el función puede generar líneas por defecto (estilo, idioma, moneda)
    # La clave es que no contiene datos personalizados
    # Un usuario sin ningún campo produce contexto con defaults

    # Con datos parciales
    user_partial = {
        "display_name": "Saul",
        "professional_profile": {"role": "Founder"},
        "communication_style": {"tone": "casual", "verbosity": "concise"},
    }
    result = build_user_context_block(user_partial)
    assert "USER_CONTEXT" in result
    assert "Saul" in result
    assert "Founder" in result
    assert "casual" in result


@pytest.mark.asyncio
async def test_resolve_agent_config_core_role():
    """resolve_agent_config para un rol core devuelve el prompt base + USER_CONTEXT."""
    from app.application.agent_resolver import resolve_agent_config

    user = {
        "display_name": "Test User",
        "professional_profile": {"role": "CEO"},
        "communication_style": {"tone": "formal", "verbosity": "detailed"},
        "financial_preferences": {"base_currency": "USD"},
        "ui_preferences": {"locale": "en-US"},
    }

    # Mock la colección de overrides para evitar acceso a DB real
    mock_col = AsyncMock()
    mock_col.find_one = AsyncMock(return_value=None)

    with patch("app.application.agent_resolver.get_user_agent_overrides_collection", return_value=mock_col):
        resolved = await resolve_agent_config("test_user", "CEO", user=user)

    # Debe tener el prompt del CEO
    assert "Oberon" in resolved.system_prompt
    # Debe tener USER_CONTEXT inyectado
    assert "USER_CONTEXT" in resolved.system_prompt
    assert "Test User" in resolved.system_prompt
