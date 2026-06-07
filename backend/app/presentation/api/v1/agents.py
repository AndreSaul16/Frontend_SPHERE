"""
API de Agentes Personalizados - SPHERE Backend.
CRUD multi-tenant para gestionar agentes custom creados por el usuario.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.infrastructure.database import get_custom_agents_collection, db, get_users_collection
from app.core.auth import get_current_user
from app.core.tenant import require_owner
from app.core.logger import api_logger as logger
from app.core.plan_limits import get_plan_id, get_max_custom_agents
from app.core.llm_models import DEEPSEEK_REASONING, normalize_model

router = APIRouter()


# --- Schemas ---

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
        # Normaliza cualquier nombre legacy/inválido (deepseek-chat, deepseek-r1,
        # gpt-4o, ...) a un model ID de DeepSeek válido y actual.
        return normalize_model(v)


class CustomAgentCreate(BaseModel):
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


# --- Templates Endpoints ---

@router.get("/templates")
async def list_agent_templates(category: Optional[str] = None):
    """Lista todos los templates de agentes disponibles."""
    from app.core.templates import get_all_templates, get_templates_by_category
    if category:
        return get_templates_by_category(category)
    return get_all_templates()


@router.get("/templates/{template_id}")
async def get_agent_template(template_id: str):
    """Obtiene un template específico por ID."""
    from app.core.templates import get_template_by_id
    template = get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template no encontrado")
    return template


# --- Agent CRUD ---

@router.post("/", response_model=CustomAgentResponse)
async def create_custom_agent(
    agent_data: CustomAgentCreate,
    user: dict = Depends(get_current_user),
):
    """Crea un nuevo agente. El owner se obtiene del JWT."""
    user_id = user["firebase_uid"]

    # Cap de agentes custom por plan.
    from app.core.errors import ErrorCode, agents_error
    plan_id = get_plan_id(user)
    max_agents = get_max_custom_agents(plan_id)
    if max_agents != -1:
        collection = get_custom_agents_collection()
        current_count = await collection.count_documents({"owner_user_id": user_id})
        if current_count >= max_agents:
            msg = (
                "Tu plan no permite crear agentes custom."
                if max_agents == 0
                else f"Tu plan permite máx. {max_agents} agentes custom. Sube a Premium para ilimitados."
            )
            raise agents_error(
                ErrorCode.AGENTS_QUOTA_EXCEEDED,
                403,
                msg,
                plan_id=plan_id,
                current_count=current_count,
                max_allowed=max_agents,
            )

    agent_id = str(uuid.uuid4())
    new_agent = {
        "agent_id": agent_id,
        "owner_user_id": user_id,
        "is_public": agent_data.is_public,
        "identity": agent_data.identity.model_dump(),
        "brain_config": agent_data.brain_config.model_dump(),
        "default_tools": agent_data.default_tools,
        "knowledge_bases": agent_data.knowledge_bases,
        "documents_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    try:
        collection = get_custom_agents_collection()
        logger.info(f"Creando agente: {agent_id} - '{agent_data.identity.name}' por {user_id}")
        await collection.insert_one(new_agent)
        new_agent.pop("_id", None)

        # Mantener contador en user.limits para mostrar en /billing/me.
        users_col = get_users_collection()
        await users_col.update_one(
            {"firebase_uid": user_id},
            {"$inc": {"limits.custom_agents_count": 1}},
        )
        return new_agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando agente: {e}")
        raise HTTPException(status_code=500, detail="Error al crear agente")


@router.get("/", response_model=List[CustomAgentResponse])
async def list_custom_agents(
    user: dict = Depends(get_current_user),
):
    """Lista los agentes del usuario autenticado + agentes públicos."""
    try:
        collection = get_custom_agents_collection()
        user_id = user["firebase_uid"]

        # Mis agentes + públicos de otros
        cursor = collection.find(
            {"$or": [{"owner_user_id": user_id}, {"is_public": True}]}
        ).sort("created_at", -1)

        agents = []
        async for agent in cursor:
            agent.pop("_id", None)
            agent.setdefault("documents_count", 0)
            agent.setdefault("updated_at", agent.get("created_at"))
            agents.append(agent)
        return agents
    except Exception as e:
        logger.error(f"Error obteniendo agentes: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener agentes")


@router.get("/{agent_id}", response_model=CustomAgentResponse)
async def get_custom_agent(
    agent_id: str,
    user: dict = Depends(get_current_user),
):
    """Obtiene los detalles de un agente (si es del usuario o público)."""
    try:
        collection = get_custom_agents_collection()
        user_id = user["firebase_uid"]

        agent = await collection.find_one({"agent_id": agent_id})
        if not agent:
            raise HTTPException(status_code=404, detail="Agente no encontrado")

        # Solo el dueño o agentes públicos
        if agent.get("owner_user_id") != user_id and not agent.get("is_public"):
            raise HTTPException(status_code=404, detail="Agente no encontrado")

        agent.pop("_id", None)
        agent.setdefault("documents_count", 0)
        agent.setdefault("updated_at", agent.get("created_at"))
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo agente: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener agente")


@router.patch("/{agent_id}", response_model=CustomAgentResponse)
async def update_custom_agent(
    agent_id: str,
    updates: CustomAgentUpdate,
    user: dict = Depends(get_current_user),
):
    """Actualización parcial de un agente personalizado (solo el dueño)."""
    user_id = user["firebase_uid"]
    try:
        collection = get_custom_agents_collection()

        # Verificar ownership
        agent = await collection.find_one({"agent_id": agent_id})
        require_owner(agent, user_id, "Agente")

        update_data = {"updated_at": datetime.now(timezone.utc)}

        if updates.identity is not None:
            for field, value in updates.identity.model_dump(exclude_unset=True).items():
                update_data[f"identity.{field}"] = value
        if updates.brain_config is not None:
            for field, value in updates.brain_config.model_dump(exclude_unset=True).items():
                update_data[f"brain_config.{field}"] = value
        if updates.default_tools is not None:
            update_data["default_tools"] = updates.default_tools
        if updates.knowledge_bases is not None:
            update_data["knowledge_bases"] = updates.knowledge_bases
        if updates.is_public is not None:
            update_data["is_public"] = updates.is_public

        result = await collection.find_one_and_update(
            {"agent_id": agent_id, "owner_user_id": user_id},
            {"$set": update_data},
            return_document=True,
        )

        if not result:
            raise HTTPException(status_code=404, detail="Agente no encontrado")

        result.pop("_id", None)
        result.setdefault("documents_count", 0)
        logger.info(f"Agente {agent_id} actualizado")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando agente {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar agente")


@router.delete("/{agent_id}")
async def delete_custom_agent(
    agent_id: str,
    user: dict = Depends(get_current_user),
):
    """Elimina un agente y toda su knowledge base asociada (solo el dueño)."""
    user_id = user["firebase_uid"]
    try:
        collection = get_custom_agents_collection()

        # Verificar ownership
        agent = await collection.find_one({"agent_id": agent_id})
        require_owner(agent, user_id, "Agente")

        result = await collection.delete_one(
            {"agent_id": agent_id, "owner_user_id": user_id}
        )

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Agente no encontrado")

        # Decrementar contador de agentes en user.limits (clamp a 0).
        users_col = get_users_collection()
        await users_col.update_one(
            {"firebase_uid": user_id},
            {"$inc": {"limits.custom_agents_count": -1}},
        )
        await users_col.update_one(
            {"firebase_uid": user_id, "limits.custom_agents_count": {"$lt": 0}},
            {"$set": {"limits.custom_agents_count": 0}},
        )

        # Limpiar vectores de knowledge_base
        async_db = db.get_async_db()
        kb_del = await async_db["knowledge_base"].delete_many(
            {"agent_target": agent_id, "user_id": user_id}
        )

        # Limpiar archivos de GridFS
        try:
            from app.infrastructure.database import get_gridfs_bucket
            bucket = get_gridfs_bucket()
            async for grid_file in bucket.find(
                {"metadata.agent_id": agent_id, "metadata.user_id": user_id}
            ):
                await bucket.delete(grid_file._id)
        except Exception as gridfs_err:
            logger.error(
                f"Error limpiando archivos GridFS del agente {agent_id}: {gridfs_err}. "
                f"Pueden quedar archivos huérfanos en GridFS."
            )

        logger.info(f"Agente {agent_id} eliminado. Vectores: {kb_del.deleted_count}")
        return {"status": "deleted", "agent_id": agent_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando agente: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar agente")
