import os
from pathlib import Path
from typing import TypedDict, Literal, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

# Importar RAG
from app.core.rag import retrieve_context

# Cargar Entorno (ruta absoluta desde este archivo)
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)

# --- CONFIG DEEPSEEK ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# Modelo Rápido (Router)
llm_router = ChatOpenAI(
    model="deepseek-chat", 
    openai_api_key=DEEPSEEK_API_KEY,
    openai_api_base=DEEPSEEK_BASE_URL,
    temperature=0
)

# Modelo Inteligente (Agente Experto)
# Aquí podrías usar 'deepseek-reasoner' si quieres razonamiento profundo (Thinking Mode)
llm_expert = ChatOpenAI(
    model="deepseek-chat", 
    openai_api_key=DEEPSEEK_API_KEY,
    openai_api_base=DEEPSEEK_BASE_URL,
    temperature=0.3
)

class AgentState(TypedDict):
    messages: List[str]
    next_agent: Literal["CEO", "CTO", "CFO", "CMO", "FINAL"]
    query: str
    final_response: str

# --- PROMPTS ---
ROUTER_PROMPT = """
Eres el Gatekeeper de SPHERE. Clasifica la consulta en: CTO, CEO, CFO, CMO o FINAL.
Responde SOLO con el nombre del rol.
"""

AGENT_PROMPT_TEMPLATE = """
Actúa como el {role} de una startup tecnológica de alto nivel.
Usa el siguiente CONTEXTO recuperado de tu base de conocimiento para responder.

CONTEXTO:
{context}

PREGUNTA DEL USUARIO:
{query}

INSTRUCCIONES:
1. Responde en primera persona ("Yo opino...", "Desde mi perspectiva técnica...").
2. Cita las fuentes del contexto si las usas.
3. Sé directo, profesional y ejecutivo.
"""

# --- NODOS ---

def router_node(state: AgentState):
    """Clasifica la intención."""
    query = state["query"]
    print(f"🚦 Router: '{query}'")
    response = llm_router.invoke([SystemMessage(content=ROUTER_PROMPT), HumanMessage(content=query)])
    decision = response.content.strip().upper()
    
    # Normalización simple
    for role in ["CTO", "CEO", "CFO", "CMO"]:
        if role in decision: return {"next_agent": role}
    return {"next_agent": "FINAL"}

def agent_node(state: AgentState):
    """El Experto consulta la DB y responde."""
    role = state["next_agent"]
    query = state["query"]
    
    print(f"   🧠 {role} está pensando... (Consultando RAG)")
    
    # 1. Recuperar Contexto Real de Mongo
    context = retrieve_context(query, role)
    
    # 2. Generar Respuesta con DeepSeek
    prompt = AGENT_PROMPT_TEMPLATE.format(role=role, context=context, query=query)
    response = llm_expert.invoke([HumanMessage(content=prompt)])
    
    print(f"   ✅ {role} ha respondido.")
    return {"final_response": response.content}

def final_node(state: AgentState):
    """Respuestas genéricas."""
    return {"final_response": "Hola. Soy SPHERE. Por favor, hazme una pregunta sobre Estrategia, Tecnología, Marketing o Finanzas."}

# --- GRAFO ---
workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("expert_agent", agent_node)
workflow.add_node("general_chat", final_node)

workflow.set_entry_point("router")

def decide_next(state):
    if state["next_agent"] == "FINAL": return "general_chat"
    return "expert_agent"

workflow.add_conditional_edges(
    "router",
    decide_next,
    {"expert_agent": "expert_agent", "general_chat": "general_chat"}
)

workflow.add_edge("expert_agent", END)
workflow.add_edge("general_chat", END)

app = workflow.compile()

# --- TEST ---
if __name__ == "__main__":
    # Prueba real
    q = "Cómo escalamos la base de datos para aguantar picos de tráfico?"
    # q = "Necesito una estrategia para viralizar el producto"
    
    print(f"\n🧪 TEST FINAL: {q}")
    result = app.invoke({"query": q, "messages": []})
    
    print("\n" + "="*40)
    print(f"🤖 RESPUESTA FINAL SPHERE ({result['next_agent']}):")
    print("="*40)
    print(result["final_response"])
