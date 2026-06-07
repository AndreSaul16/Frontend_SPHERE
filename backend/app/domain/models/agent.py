"""Pydantic models para agentes personalizados."""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

from app.core.llm_models import DEEPSEEK_REASONING, normalize_model, ALLOWED_AGENT_MODELS

# Backward-compat: algunos módulos importan ALLOWED_MODELS desde aquí.
ALLOWED_MODELS = ALLOWED_AGENT_MODELS


class AgentIdentity(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    role: str = "specialist"
    color: str = "blue"
    avatar_style: Optional[str] = "cyberpunk"
    description: Optional[str] = Field(None, max_length=500)


class BrainConfig(BaseModel):
    model: str = DEEPSEEK_REASONING
    temperature: float = Field(0.3, ge=0.0, le=2.0)
    system_prompt: str = Field(..., min_length=10, max_length=10000)

    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        # Normaliza nombres legacy/inválidos a un model ID de DeepSeek válido.
        return normalize_model(v)


class CustomAgentCreate(BaseModel):
    owner_user_id: str
    is_public: bool = False
    identity: AgentIdentity
    brain_config: BrainConfig
    default_tools: List[str] = []
    knowledge_bases: List[str] = []


class CustomAgentUpdate(BaseModel):
    identity: Optional[AgentIdentity] = None
    brain_config: Optional[BrainConfig] = None
    default_tools: Optional[List[str]] = None
    knowledge_bases: Optional[List[str]] = None
    is_public: Optional[bool] = None


class CustomAgentResponse(BaseModel):
    agent_id: str
    owner_user_id: str
    is_public: bool
    identity: AgentIdentity
    brain_config: BrainConfig
    default_tools: List[str]
    knowledge_bases: List[str]
    documents_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
