from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.orchestrator import app as orchestrator_app

router = APIRouter()

# 1. Definimos qué esperamos recibir (Schema)
class ChatRequest(BaseModel):
    query: str

# 2. Definimos qué vamos a responder
class ChatResponse(BaseModel):
    role: str
    response: str

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint principal para hablar con SPHERE.
    El orquestador decide quién responde (CEO, CTO, etc).
    """
    try:
        # Ejecutar el Grafo de LangGraph
        # inputs={"query": ...} coincide con el AgentState que definimos en orchestrator.py
        result = orchestrator_app.invoke({"query": request.query, "messages": []})
        
        return ChatResponse(
            role=result["next_agent"],
            response=result["final_response"]
        )
        
    except Exception as e:
        print(f"🔥 Error en el endpoint de chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
