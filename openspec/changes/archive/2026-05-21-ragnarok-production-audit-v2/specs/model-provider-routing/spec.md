# model-provider-routing

## Purpose

Route AI model requests to the correct provider API (OpenAI vs DeepSeek) based on model name prefix, eliminating the hardcoded DeepSeek default in `agent_node()` and `board_classifier`.

## Requirements

| ID | Requirement | N |
|----|------------|---|
| MPR-001 | `agent_node()` MUST select ChatOpenAI config by model prefix | 3 |
| MPR-002 | `board_classifier` MUST route classifier model to its provider | 1 |
| MPR-003 | Unknown model names MUST fall back gracefully with warning | 1 |

### MPR-001: Provider Resolution in agent_node

- GIVEN resolved model is `gpt-4o` or `gpt-4o-mini`
  WHEN `agent_node()` creates `ChatOpenAI`
  THEN `openai_api_base` is OpenAI URL, `openai_api_key` is OPENAI_API_KEY

- GIVEN resolved model is `deepseek-chat` or `deepseek-r1`
  WHEN `agent_node()` creates `ChatOpenAI`
  THEN `openai_api_base` is DeepSeek URL, `openai_api_key` is DEEPSEEK_API_KEY

- GIVEN resolved model is `deepseek-chat`
  WHEN `agent_node()` runs
  THEN API call goes to DeepSeek (NOT OpenAI)

### MPR-002: Board Classifier Provider

- GIVEN classifier model is `gpt-4o-mini`
  WHEN `board_classifier` executes
  THEN API request goes to OpenAI endpoint (not DeepSeek default)

### MPR-003: Unknown Model Fallback

- GIVEN resolved model is an unrecognized name (e.g., `unknown-model-v2`)
  WHEN `agent_node()` creates `ChatOpenAI`
  THEN fall back to default provider, log `WARNING` with model name
  AND the request MUST NOT crash with an unhandled KeyError
