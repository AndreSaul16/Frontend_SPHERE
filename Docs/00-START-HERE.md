# 🧭 Punto de Entrada: Proyecto SPHERE

## Estado Actual: FASE 1 COMPLETADA + Tool-Calling con n8n → Transición a FASE 2 (IAs Propias)
La plataforma MVP está operativa con orquestación multi-agente, RAG personalizado, templates, file upload, UX premium y **tool-calling con 21 herramientas externas** via n8n (Google Calendar, WhatsApp, redes sociales, Jules, datos financieros, delegación de tareas). El siguiente paso es la configuración de workflows en n8n y la integración de modelos propios con vLLM en Runpod.

## Documentación Crítica
⚠️ **Instrucción para el Agente:** Lee estos documentos antes de generar código.

1. **[01-PRD.md](./01-PRD.md)**: La "Biblia" del proyecto. Contiene la visión, el stack tecnológico híbrido y las reglas de negocio.
2. **[../Bitacora_SPHERE.md](../Bitacora_SPHERE.md)**: Bitácora de desarrollo con historial completo de decisiones técnicas.
3. **[../../Backend_SHPERE/Resumen_Backend.md](../../Backend_SHPERE/Resumen_Backend.md)**: Resumen técnico del backend con cronología de 22+ endpoints.
4. **[../Resumen_Frontend.md](../Resumen_Frontend.md)**: Resumen técnico del frontend con cronología de componentes y features.

## Lo que está implementado (Marzo 2026)
- ✅ Orquestación multi-agente con LangGraph (CEO, CTO, CMO, CFO + custom agents)
- ✅ **Tool-calling con ReAct loop** — 21 herramientas externas via n8n webhooks
- ✅ **Herramientas compartidas**: Google Calendar (5 tools) + WhatsApp (3 tools) para todos los agentes
- ✅ **CEO**: Delegación de tareas a CTO/CMO/CFO (MongoDB)
- ✅ **CTO**: Integración con Jules (agente async de Google)
- ✅ **CFO**: Noticias financieras + datos de bolsa en tiempo real
- ✅ **CMO**: Publicación en LinkedIn/Instagram + analytics + scheduling
- ✅ **n8n** como capa de ejecución de workflows (contenedor Podman, puerto 5678)
- ✅ RAG con MongoDB Atlas Vector Search (filtrado por agente)
- ✅ RAG personalizado por agente (upload PDF/DOCX/TXT/MD → chunk → embed → store)
- ✅ 10 templates de agentes profesionales (Legal, Psicólogo, Contador, etc.)
- ✅ CRUD completo de agentes (POST, GET, PATCH, DELETE + documents)
- ✅ Streaming SSE con artefactos (código, markdown, mermaid, CSV) + tool events
- ✅ UX premium: búsqueda, copiar, regenerar, pins, exportar, rating
- ✅ Frontend: ToolExecutionCard con animación y estado running/completed
- ✅ Persistencia atómica de sesiones con checkpoints de LangGraph
- ✅ Clean architecture con Pydantic models extraídos

## Prioridades Inmediatas (Kanban: Doing)
1. **Configurar workflows n8n**: Crear workflows en `localhost:5678` para cada webhook path.
2. **OAuth & APIs**: Conectar Google Calendar OAuth2, WhatsApp Business API, Jules API en n8n.
3. **IAs Propias**: Integrar vLLM en **Runpod** (GPU Serverless) como motor de inferencia custom.
4. **Multi-usuario**: Sistema de autenticación JWT (actualmente `user_id` hardcodeado para testing).
5. **Deploy**: Desplegar en **Google Cloud Run** (Backend) + CDN (Frontend).

## Arquitectura de Alto Nivel
* **Patrón:** Orquestación Centralizada (LangGraph ReAct Loop) con modelo dinámico por agente.
* **Tool-Calling:** 21 herramientas via n8n webhooks + HMAC-SHA256 + LangGraph ToolNode.
* **Infraestructura:** Híbrida Desacoplada (GCP Cloud Run + Runpod GPU + n8n).
* **Frontend:** React + Vite (Streaming unidireccional vía SSE, incluyendo tool events).
* **RAG:** MongoDB Atlas Vector Search con GridFS para almacenamiento de archivos.
* **Datos:** MongoDB Atlas (sessions, agents, knowledge_base, checkpoints, ratings, agent_tasks, tool_audit_log).

## Stack Actual
| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI + LangGraph (ReAct) + LangChain |
| Tool Execution | n8n (webhooks, OAuth, workflow automation) |
| Frontend | React 19 + Vite 7 + Zustand + Tailwind v4 + Framer Motion |
| LLM | DeepSeek-Chat (temporal, será reemplazado por vLLM propio) |
| Embeddings | OpenAI text-embedding-3-small |
| DB | MongoDB Atlas (Vector Search + GridFS + Checkpointing) |
| HTTP Client | httpx (async, HMAC-SHA256 signing) |
| Contenedores | Podman (Daemonless/Rootless) |
