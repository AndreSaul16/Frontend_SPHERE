"""
Endpoint SSE para streaming de tokens en tiempo real.
Multi-tenant: user_id se extrae del JWT y se inyecta en el grafo.
Distributed lock previene concurrencia en el mismo thread.

Soporta dos modos:
1. Normal: Un solo agente responde (flujo actual)
2. Board Meeting: Todos los agentes discuten secuencialmente (CEO→CTO→CFO→CMO→CEO conclusión)

Modelo de cobro: 1 crédito por POST a /stream, cobrado AQUÍ antes del grafo.
El orchestrator respeta la bandera already_charged para no volver a cobrar.
"""

import json
import re
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.application.orchestrator import app as orchestrator_app
from app.application.orchestrator import board_app as board_orchestrator_app
from app.core.auth import get_current_user
from app.core.tenant import require_owner
from app.core.distributed_lock import DistributedLock
from app.core.error_handling import safe_error_response
from app.core.logger import stream_logger as logger

router = APIRouter()


class StreamRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10_000)
    session_id: str
    target_role: Optional[str] = None


# Regex para validar y parsear la etiqueta de apertura
OPEN_TAG_PATTERN = re.compile(r"<sphere_artifact\s+([^>]+)>")


async def generate_chat_events(
    query: str,
    session_id: str,
    user_id: str,
    target_role: Optional[str] = None,
    board_mode: bool = False,
    already_charged: bool = False,
    charge_ctx = None,
    credit_manager = None,
    lock: Optional["DistributedLock"] = None,
):
    """Generador asíncrono con aislamiento multi-tenant.

    Args:
        query: Mensaje del usuario
        session_id: ID de la sesión
        user_id: ID del usuario (Firebase UID)
        target_role: Rol objetivo (None para grupo, "CEO"/"CTO"/etc para directo)
        board_mode: True si el usuario tiene Board Meeting activado
        already_charged: True si el crédito ya fue cobrado en el endpoint
        charge_ctx: Contexto del cobro para refund en caso de error
        credit_manager: Instancia del CreditManager para refund
    """
    try:
        mode_str = "BOARD MEETING" if board_mode else "NORMAL"
        logger.info(
            f"Iniciando stream [{mode_str}] para sesión: {session_id} | User: {user_id} | Query: '{query[:50]}...'"
        )

        # thread_id multi-tenant: user_id:session_id
        thread_id = f"{user_id}:{session_id}"
        config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}

        from langchain_core.messages import HumanMessage

        new_message = HumanMessage(content=query)

        initial_state = {
            "query": query,
            "messages": [new_message],
            "target_role": target_role,
            "user_id": user_id,
            "already_charged": already_charged,
            # Board meeting defaults
            "board_mode": False,
            "board_iteration": 0,
            "board_max_iterations": 1,
            "board_agents_done": [],
        }

        # Choose the right orchestrator
        active_orchestrator = board_orchestrator_app if board_mode else orchestrator_app

        buffer = ""
        artifact_buffer = ""
        is_inside_artifact = False
        current_board_agent = None  # Track which agent is speaking in board mode
        # Token cap tracking: accumulate tokens from on_chat_model_end events
        # to call aadjust_after_completion after the stream completes.
        total_tokens_in = 0
        total_tokens_out = 0

        async for event in active_orchestrator.astream_events(
            initial_state, config=config, version="v1"
        ):
            kind = event["event"]

            # --- A. DETECCIÓN DE ROL (Router / Board Classifier) ---
            if kind == "on_chain_end":
                node_name = event.get("name", "")

                # Normal mode: router detects agent
                if node_name == "router":
                    output = event.get("data", {}).get("output")
                    if output and "next_agent" in output:
                        role = output["next_agent"]
                        logger.debug(f"Router detectó agente: {role}")
                        yield f"data: {json.dumps({'type': 'meta', 'role': role})}\n\n"

                # Board mode: detect which board agent is starting
                if "board" in node_name and node_name != "classifier":
                    # Extract role from node name (e.g., "ceo_board" → "CEO")
                    role_map = {
                        "ceo_board": "CEO",
                        "cto_board": "CTO",
                        "cfo_board": "CFO",
                        "cmo_board": "CMO",
                        "conclusion": "CEO",
                    }
                    role = role_map.get(node_name)
                    if role and role != current_board_agent:
                        current_board_agent = role
                        logger.debug(f"Board meeting: {role} hablando")
                        yield f"data: {json.dumps({'type': 'board_agent', 'role': role, 'is_conclusion': node_name == 'conclusion'})}\n\n"

            # --- A2. CHAT MODEL END — acumular tokens para ajuste post-stream ---
            if kind == "on_chat_model_end":
                output = event.get("data", {}).get("output")
                if output:
                    usage = getattr(output, "usage_metadata", None)
                    if usage:
                        tokens_in = int(usage.get("input_tokens", 0) or 0)
                        tokens_out = int(usage.get("output_tokens", 0) or 0)
                        total_tokens_in += tokens_in
                        total_tokens_out += tokens_out

            # --- B. TOOL EXECUTION EVENTS ---
            if kind == "on_tool_start":
                tool_name = event.get("name", "unknown_tool")
                tool_input = event.get("data", {}).get("input", {})
                logger.info(f"🔧 Tool start: {tool_name}")
                yield f"data: {json.dumps({'type': 'tool_start', 'tool_name': tool_name, 'args': tool_input})}\n\n"

            if kind == "on_tool_end":
                tool_name = event.get("name", "unknown_tool")
                tool_output = str(event.get("data", {}).get("output", ""))[:500]
                logger.info(f"✅ Tool end: {tool_name}")
                yield f"data: {json.dumps({'type': 'tool_result', 'tool_name': tool_name, 'result': tool_output})}\n\n"

            # --- C. STREAMING DE TOKENS ---
            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content"):
                    content = chunk.content
                    if not content:
                        continue

                    if is_inside_artifact:
                        artifact_buffer += content

                        if "</sphere_artifact>" in artifact_buffer:
                            logger.debug(f"🔒 Cierre de artefacto detectado")
                            artifact_content, chat_residue = artifact_buffer.split(
                                "</sphere_artifact>", 1
                            )

                            if artifact_content:
                                yield f"data: {json.dumps({'type': 'artifact_chunk', 'content': artifact_content})}\n\n"

                            yield f"data: {json.dumps({'type': 'artifact_close'})}\n\n"
                            is_inside_artifact = False
                            artifact_buffer = ""

                            if chat_residue:
                                yield f"data: {json.dumps({'type': 'token', 'content': chat_residue})}\n\n"

                            buffer = ""
                        else:
                            close_prefixes = [
                                "<",
                                "</",
                                "</s",
                                "</sp",
                                "</sph",
                                "</sphe",
                                "</spher",
                                "</sphere",
                                "</sphere_",
                                "</sphere_a",
                                "</sphere_ar",
                                "</sphere_art",
                                "</sphere_arti",
                                "</sphere_artif",
                                "</sphere_artifa",
                                "</sphere_artifac",
                                "</sphere_artifact",
                            ]

                            if not any(
                                artifact_buffer.endswith(p) for p in close_prefixes
                            ):
                                if "<sphere_artifact" in artifact_buffer:
                                    artifact_buffer = re.sub(
                                        r"<sphere_artifact[^>]*>", "", artifact_buffer
                                    )

                                if artifact_buffer:
                                    yield f"data: {json.dumps({'type': 'artifact_chunk', 'content': artifact_buffer})}\n\n"
                                    artifact_buffer = ""

                    else:
                        buffer += content
                        if "<sphere_artifact" in buffer:
                            tag_start = buffer.find("<sphere_artifact")
                            tag_section = buffer[tag_start:]
                            if ">" in tag_section:
                                match = OPEN_TAG_PATTERN.search(buffer)
                                if match:
                                    attrs_str = match.group(1)
                                    title_match = re.search(
                                        r'title="([^"]+)"', attrs_str
                                    )
                                    type_match = re.search(r'type="([^"]+)"', attrs_str)
                                    lang_match = re.search(
                                        r'language="([^"]*)"', attrs_str
                                    )

                                    title = (
                                        title_match.group(1)
                                        if title_match
                                        else "untitled"
                                    )
                                    artifact_type = (
                                        type_match.group(1) if type_match else "code"
                                    )
                                    language = lang_match.group(1) if lang_match else ""

                                    logger.info(
                                        f"📦 Abriendo artefacto: '{title}' ({artifact_type})"
                                    )

                                    pre_tag = buffer[:tag_start]
                                    if pre_tag.strip():
                                        yield f"data: {json.dumps({'type': 'token', 'content': pre_tag})}\n\n"

                                    yield f"data: {json.dumps({'type': 'artifact_open', 'title': title, 'artifact_type': artifact_type, 'language': language})}\n\n"

                                    is_inside_artifact = True
                                    tag_end = tag_section.find(">")
                                    residue = tag_section[tag_end + 1 :]
                                    if residue:
                                        yield f"data: {json.dumps({'type': 'artifact_chunk', 'content': residue})}\n\n"

                                    buffer = ""
                        else:
                            partial_tags = [
                                "<s",
                                "<sp",
                                "<sph",
                                "<sphe",
                                "<spher",
                                "<sphere",
                                "<sphere_",
                                "<sphere_a",
                                "<sphere_ar",
                                "<sphere_art",
                                "<sphere_arti",
                                "<sphere_artif",
                                "<sphere_artifa",
                                "<sphere_artifac",
                                "<sphere_artifact",
                            ]

                            if not any(buffer.endswith(p) for p in partial_tags):
                                yield f"data: {json.dumps({'type': 'token', 'content': buffer})}\n\n"
                                buffer = ""

        if buffer.strip():
            yield f"data: {json.dumps({'type': 'token', 'content': buffer})}\n\n"

        # Token cap adjustment: si el stream cobró (already_charged=True) y
        # la inferencia superó el cap de 4k tokens, cobrar mensaje extra.
        # Esto es SEPARADO del charge inicial — siempre debe ejecutarse.
        if already_charged and charge_ctx and credit_manager is not None and (total_tokens_in + total_tokens_out) > 0:
            cost_actual = (total_tokens_in * 0.27 + total_tokens_out * 1.10) / 1_000_000
            try:
                await credit_manager.aadjust_after_completion(
                    charge_ctx, total_tokens_in, total_tokens_out, cost_actual
                )
                logger.debug(
                    f"Post-stream adjustment: {total_tokens_in}+{total_tokens_out} tokens "
                    f"para user {user_id}"
                )
            except Exception as e:
                logger.error(f"Error en post-stream adjustment para {user_id}: {e}")

        yield "data: [DONE]\n\n"
        logger.info(f"Stream finalizado para sesión: {session_id}")

    except GeneratorExit:
        logger.info(f"🛑 Cliente desconectado (Stop Generation): {session_id}")
        if already_charged and charge_ctx and credit_manager is not None:
            try:
                await credit_manager.arefund(charge_ctx, reason="client_disconnected")
                logger.info(f"♻️ Crédito reembolsado por desconexión del cliente: {user_id}")
            except Exception as refund_error:
                logger.error(f"Error reembolsando crédito en desconexión: {refund_error}")
        return
    except Exception as e:
        # Refund on error: si ya cobramos el crédito, devolverlo
        if already_charged and charge_ctx and credit_manager is not None:
            try:
                await credit_manager.arefund(charge_ctx, reason="inference_failed")
                logger.info(f"♻️ Crédito reembolsado por error en stream: {user_id}")
            except Exception as refund_error:
                logger.error(f"Error refunding credits in stream: {refund_error}")
        error = safe_error_response(e)
        yield f"data: {json.dumps({'type': 'error', 'message': error['message']})}\n\n"
        yield "data: [DONE]\n\n"
    finally:
        if lock is not None:
            await lock.release()


@router.post("/")
async def chat_stream_endpoint(
    request: StreamRequest,
    user: dict = Depends(get_current_user),
):
    """Endpoint SSE para streaming de respuestas. Multi-tenant con distributed lock.
    
    Cobro de crédito: 1 crédito por POST, aquí ANTES del grafo.
    El orchestrator recibe already_charged=True y no vuelve a cobrar.
    """
    try:
        user_id = user["firebase_uid"]

        # Per-plan rate limit: se resuelve AQUÍ después de saber el plan del usuario.
        # Si Redis no está disponible, el rate limit es no-op (fast-path).
        from app.infrastructure.redis_client import _redis_client
        from app.core.plan_limits import RATE_LIMIT_CHAT_BY_PLAN

        if _redis_client is not None:
            plan_id = (user.get("subscription") or {}).get("plan_id", "free")
            times, seconds = RATE_LIMIT_CHAT_BY_PLAN.get(plan_id, RATE_LIMIT_CHAT_BY_PLAN["free"])
            from pyrate_limiter import Limiter, Rate, Duration

            rate = Rate(times, Duration.SECOND * seconds)
            limiter = Limiter(rate)
            # Usar user_id como identificador (ya viene del JWT)
            if not limiter.try_acquire(user_id, blocking=False):
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded. Tu plan ({plan_id}) permite {times} requests por {seconds}s.",
                    },
                )

        # Email verification gate — debe ir ANTES del credit check.
        # Es un gate de autorización más fundamental que el billing.
        subscription = user.get("subscription") or {}
        if subscription.get("status") == "email_unverified":
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "email_unverified",
                    "message": "Verifica tu email antes de usar SPHERE.",
                },
            )

        # Pre-check de créditos ANTES de abrir SSE.
        wallet = user.get("wallet") or {}
        total_balance = (
            wallet.get("pro_messages_balance", 0)
            + wallet.get("topup_messages_balance", 0)
        )
        if total_balance <= 0:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "insufficient_credits",
                    "message": "Has agotado tus mensajes. Sube de plan o compra un top-up.",
                },
            )

        # Cobrar 1 crédito AHORA (antes del grafo, una sola vez por POST).
        charge_ctx = None
        credit_manager = None
        try:
            from app.application.credit_manager import CreditManager
            from app.core.config import settings as app_settings
            from app.infrastructure.database import db

            credit_manager = CreditManager(db.get_sync_client()[app_settings.DB_NAME])
            charge_ctx = await credit_manager.areserve_and_charge(
                user_id, "stream", "deepseek-v4-pro"
            )
            already_charged = True
        except Exception as e:
            # Si es InsufficientCreditsError, ya lanzamos 402 arriba; pero por si acaso
            from app.application.credit_manager import InsufficientCreditsError
            if isinstance(e, InsufficientCreditsError):
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "insufficient_credits",
                        "message": "Has agotado tus mensajes.",
                    },
                )
            logger.error(f"Error inesperado al cobrar crédito: {e}")
            raise HTTPException(status_code=500, detail="Error interno al procesar créditos")

        # Verificar que la sesión pertenece al usuario
        from app.infrastructure.database import (
            get_sessions_collection,
            get_custom_agents_collection,
        )

        sessions_collection = get_sessions_collection()
        session_doc = await sessions_collection.find_one(
            {"session_id": request.session_id}
        )
        require_owner(session_doc, user_id, "Sesión")

        # Distributed lock: previene concurrencia en el mismo thread
        lock = DistributedLock(
            f"checkpoint:{user_id}:{request.session_id}", ttl_seconds=60
        )
        acquired = await lock.acquire()
        if not acquired:
            raise HTTPException(
                status_code=409,
                detail="Tu mensaje anterior aún se está procesando. Espera un momento.",
            )

        try:
            final_target_role = request.target_role
            board_mode = False

            if not final_target_role and session_doc:
                session_type = session_doc.get("type", "direct")
                if session_type == "group":
                    final_target_role = None
                    logger.debug(
                        "Sesión GROUP detectada: router clasificará la consulta"
                    )

                    # Check if board meeting is enabled for this user
                    from app.infrastructure.database import get_users_collection

                    users_col = get_users_collection()
                    user_doc = await users_col.find_one(
                        {"firebase_uid": user_id},
                        {"board_meeting_enabled": 1, "board_iterations": 1},
                    )
                    if user_doc and user_doc.get("board_meeting_enabled", False):
                        board_mode = True
                        logger.info(f"Board Meeting activado para user {user_id}")
                else:
                    agent_ref_type = session_doc.get("agent_ref_type", "core")
                    base_agent_id = session_doc.get("base_agent_id", "CEO")

                    if agent_ref_type == "custom":
                        agents_col = get_custom_agents_collection()
                        agent = await agents_col.find_one({"agent_id": base_agent_id})
                        if not agent:
                            raise HTTPException(
                                status_code=422,
                                detail="El agente asignado a esta sesión fue eliminado. Crea una nueva sesión.",
                            )

                    final_target_role = base_agent_id
                    logger.debug(
                        f"Sesión DIRECT ({agent_ref_type}): target_role={final_target_role}"
                    )

            return StreamingResponse(
                generate_chat_events(
                    request.query,
                    request.session_id,
                    user_id,
                    final_target_role,
                    board_mode,
                    already_charged=already_charged,
                    charge_ctx=charge_ctx,
                    credit_manager=credit_manager,
                    lock=lock,
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        except Exception as inner_e:
            # Solo si falla ANTES de crear el StreamingResponse — liberar lock aquí
            await lock.release()
            raise inner_e

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔥 Error iniciando stream: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
