"""
Modelos LLM canónicos de DeepSeek + normalización de nombres legacy.

DeepSeek deprecó `deepseek-chat` y `deepseek-reasoner` (EOL 2026-07-24) y el ID
`deepseek-r1` nunca fue válido. Los agentes de SPHERE usan `deepseek-v4-pro`
(reasoning, respuestas de calidad); las tareas internas de clasificación/routing
usan `deepseek-v4-flash` (rápido y barato).

Verificado contra https://api-docs.deepseek.com/quick_start/pricing (jun 2026):
  deepseek-v4-pro    → $0.435/1M in (cache miss), $0.87/1M out
  deepseek-v4-flash  → $0.14/1M in (cache miss),  $0.28/1M out
"""

# Modelo de razonamiento para los agentes (respuestas de calidad).
DEEPSEEK_REASONING = "deepseek-v4-pro"
# Modelo rápido/barato para clasificación interna (router, board classifier).
DEEPSEEK_FAST = "deepseek-v4-flash"

# Modelos válidos que el usuario puede elegir para sus agentes custom.
ALLOWED_AGENT_MODELS = {DEEPSEEK_REASONING, DEEPSEEK_FAST}

# Precios por 1M de tokens (USD), para el ajuste de créditos post-inferencia.
MODEL_PRICING = {
    DEEPSEEK_REASONING: {"input": 0.435, "output": 0.87},
    DEEPSEEK_FAST: {"input": 0.14, "output": 0.28},
}

# Mapeo de nombres legacy/inválidos/deprecados → modelo válido actual.
_LEGACY_MODEL_MAP = {
    "deepseek-chat": DEEPSEEK_REASONING,
    "deepseek-reasoner": DEEPSEEK_REASONING,
    "deepseek-r1": DEEPSEEK_REASONING,   # nunca fue un ID válido
    # GPT solo se usa para embeddings; si un agente lo tuviera guardado, redirigir.
    "gpt-4o": DEEPSEEK_REASONING,
    "gpt-4o-mini": DEEPSEEK_FAST,
}


def normalize_model(name: str | None) -> str:
    """Devuelve un model ID de DeepSeek válido y actual a partir de cualquier
    nombre (legacy, inválido o None). Garantiza que la inferencia nunca use un
    modelo deprecado/inexistente. Default: modelo de razonamiento."""
    if not name:
        return DEEPSEEK_REASONING
    n = name.strip()
    if n in ALLOWED_AGENT_MODELS:
        return n
    return _LEGACY_MODEL_MAP.get(n, DEEPSEEK_REASONING)


def pricing_for(model: str) -> dict:
    """Precio (input/output por 1M tokens) del modelo, normalizado."""
    return MODEL_PRICING.get(normalize_model(model), MODEL_PRICING[DEEPSEEK_REASONING])
