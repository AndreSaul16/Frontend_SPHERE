# Resumen Backend - Proyecto SPHERE

**Sistema Multi-Agente con RAG y LangGraph**

---

## 🗓️ Cronología del Trabajo

### **21 diciembre, 2025 - Configuración Inicial Backend**

#### Hitos
- ✅ Estructura inicial de FastAPI creada
- ✅ Configuración de MongoDB Atlas con conexión segura
- ✅ Endpoint `/api/v1/health` implementado
- ✅ Archivo `config.py` con pydantic-settings
- ✅ Base de conexión a MongoDB (`database.py`)

---

### **27 enero, 2026 - Sistema Multi-Agente Completo**

#### Hitos

##### 1. **Vectorización de la Base de Conocimiento**
- ✅ **74 documentos vectorizados** con OpenAI `text-embedding-3-small`
- ✅ Índice vectorial creado en MongoDB Atlas (`vector_index`)
- ✅ Script `etl/scripts/vectorize_corpus.py` funcionando al 100%
- ✅ Búsqueda semántica probada exitosamente

##### 2. **Orquestador Multi-Agente (LangGraph)**
- ✅ `app/core/orchestrator.py` implementado con LangGraph
- ✅ Router inteligente con DeepSeek (deepseek-chat)
- ✅ Clasificación automática: CTO, CEO, CFO, CMO, FINAL
- ✅ Grafo de estados: Router → Expert Agent → END

##### 3. **Sistema RAG (Retrieval Augmented Generation)**
- ✅ `app/core/rag.py` implementado
- ✅ Búsqueda vectorial filtrada por `agent_target`
- ✅ Contexto de 3 documentos más relevantes por consulta
- ✅ Integración OpenAI + MongoDB Vector Search

##### 4. **Endpoint de Chat API**
- ✅ `app/api/v1/chat.py` - POST `/api/v1/chat/`
- ✅ CORS habilitado para frontend
- ✅ Swagger UI disponible en `/docs`
- ✅ Integración completa: FastAPI → LangGraph → RAG → DeepSeek

##### 5. **Infraestructura & Bugs Corregidos**
- ✅ **Parche SSL**: Uso de `certifi` para conexiones seguras con MongoDB Atlas.
- ✅ **Compatibilidad Pydantic v2**: Migración a `model_config` y `SettingsConfigDict` para gestión de entornos.
- ✅ **Sincronización de Drivers**: Actualización de `motor` a v3.7.x para compatibilidad con `pymongo` 4.9+.
- ✅ **Límite de Tokens**: Implementación de corte de seguridad a 20k caracteres en el pipeline de vectorización.

##### 6. **Dependencias Instaladas**
```
langgraph==1.0.7
langchain-openai==1.1.7
langchain-mongodb==0.11.0
langchain-core==1.2.7
motor==3.7.1
pydantic-settings (v2.x)
certifi
```

---

### **30 enero, 2026 - Streaming SSE y Optimización API**

#### Hitos
- ✅ **Implementación de Streaming (SSE)**: Migración de respuesta estática a Server-Sent Events para una experiencia de chat en tiempo real.
- ✅ **Refactor de Orquestación**: Ajustes en el `orchestrator.py` para soportar la emisión de tokens por roles.
- ✅ **Nuevo Endpoint `/api/v1/chat/stream`**: Endpoint especializado para streaming con manejo de errores robusto.
- ✅ **Mejora en Prompting**: Ajustes en el Router para asegurar que los agentes generen bloques de código y tablas detectables por el frontend.

---

## 📊 Estado Actual del Sistema

### Arquitectura
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI   │────▶│  LangGraph   │────▶│  DeepSeek   │
│   /chat     │     │ Orchestrator │     │   (LLM)     │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐     ┌─────────────┐
                    │     RAG      │────▶│  MongoDB    │
                    │  retrieve()  │     │  Vector DB  │
                    └──────────────┘     └─────────────┘
```

### Endpoints Disponibles
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/docs` | Swagger UI |
| GET | `/api/v1/health/` | Health check |
| POST | `/api/v1/chat/` | Chat con SPHERE |

### Ejemplo de Uso
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Cómo escalamos la base de datos?"}'
```

**Respuesta:**
```json
{
  "role": "CTO",
  "response": "Desde mi perspectiva técnica..."
}
```

---

### **31 enero, 2026 - Infraestructura de Persistencia y Testing (Refactorización)**
 
 #### Hitos
 - ✅ **Arquitectura Dual de MongoDB**: Implementación de clientes separados (Motor Async + PyMongo Sync). Erradicación de bloqueos de hilos.
 - ✅ **Suite de Testing (29 tests)**: Validación exhaustiva de conexiones, CRUD y checkpointer.
 - ✅ **Frontend Fantasma (CLI)**: Creación de `phantom_front.py` integrado directamente en el backend como herramienta de diagnóstico SSE/Stress.
  - ✅ **Auditoría Técnica de 9 Puntos**: Certificación de estabilidad total:
      - **Memoria Real**: Corregida inyección de mensajes con `add_messages`.
      - **Fix de Persistencia Crítica**: Resuelto bug en `stream.py` que sobrescribía el historial con arrays vacíos. Implementada carga de estado previo con `aget_state()` antes de procesar nuevos tokens.
      - **Stress Test**: Soportados flujos paralelos masivos sin degradación.
      - **Concurrencia Intra-Sesión**: Validación de seguridad en el mismo `thread_id`.
 - ✅ **Deployment GitHub**: Lanzamiento del core al repositorio multi-repo oficial.
 
 ---
 
 ### **01 - 02 febrero, 2026 - Migración Total Cloud y Estabilidad**
 
 #### Hitos
- ✅ **Cloud Migration Final**: Remoción total del servicio local de MongoDB en `compose.yaml`.
- ✅ **Atlas Connectivity**: Validación de conexión segura TLS con MongoDB Atlas para `sphere_db` y `checkpointing_db`.
- ✅ **Entorno Dinámico**: Resolución de conflictos de variables de entorno ($HOME) para ejecución de agentes autónomos.
- ✅ **Persistencia Certificada**: Verificación de que la memoria de LangGraph se mantiene íntegra tras resets del contenedor.

 ---
 
 ## 📊 Estado Actual del Sistema
 
 ### Arquitectura de Conexión
 ```mermaid
 graph LR
     subgraph FastAPI_App
         A[API Endpoints] -->|Motor Async| B[(MongoDB)]
     end
     subgraph LangGraph_Engine
         C[Checkpointer] -->|PyMongo Sync| B
     end
     subgraph Diagnostic_Tool
         D[Phantom CLI] -->|httpx| A
     end
 ```

 ### Endpoints Disponibles
 | Método | Endpoint | Descripción |
 |--------|----------|-------------|
 | GET | `/api/v1/health/health` | Health check + Latencia DB |
 | POST | `/api/v1/sessions/` | Crear sesión de chat |
 | GET | `/api/v1/sessions/` | Listar sesiones históricas |
 | POST | `/api/v1/stream/` | Chat Streaming (SSE) con Memoria |

 ---

 ### **10 febrero, 2026 - Auditoría y Consolidación de Esquema DB**

 #### Hitos
- ✅ **Documentación de `sessions_metadata`**: Definición del esquema que soporta overrides visuales (`override_name`, `avatar`, `color`).
- ✅ **Esquema de `custom_agents`**: Estructura de perfiles para agentes dinámicos, incluyendo la persistencia del `system_prompt`.
- ✅ **Mapeo de Relaciones**: Clarificación del vínculo entre `session_id` y `thread_id` en la colección de checkpoints.
- ✅ **Diagnóstico de Identidad de Mensajes**: Identificado que el `agent_id` no se está persistiendo en los `additional_kwargs` de los `AIMessage`, lo que causaba que el frontend perdiera la referencia del agente al recargar el historial.

---

### **10 febrero, 2026 - Investigación de Integridad de Mensajes**

#### Hitos
- 🔍 **Debugging de Persistencia**: Análisis de la serialización de mensajes en `orchestrator.py`. Confirmado que los mensajes del LLM requieren inyección explícita de metadatos para mantener la identidad del agente entre sesiones.
- 🔍 **Auditoría de Orquestador**: Revisión de `agent_node` para asegurar que las respuestas del experto viajen con su ID correspondiente hacia el checkpointer de MongoDB.

---

### **10 febrero, 2026 - Restauración de Infraestructura & Local Fallback (Noche)**

#### Hitos
- ✅ **Recuperación de Podman**: Guía y ejecución de reset de máquina Podman en Windows (`machine init/start`) tras pérdida de conectividad.
- ✅ **Docker Restoration**: Restauración de `Dockerfile` y `.dockerignore` críticos para el despliegue de la imagen frontend a través de `podman-compose`.
- ✅ **Ejecución Local de Emergencia**: Validada la disponibilidad del backend mediante ejecución directa con `uvicorn` para desbloquear el desarrollo del frontend mientras se estabilizaban los contenedores.
- ✅ **Verificación de Signos Vitales**: Confirmada la escucha en puerto 8000 y respuesta JSON del servidor local.


 ### Colecciones Principales (`sphere_db`)
 1. **`sessions_metadata`**:
    - Campos: `session_id`, `title`, `base_agent_id`, `created_at`, `metadata`.
    - Propósito: Personalización UI y catálogo de chats.
 2. **`custom_agents`**:
    - Campos: `agent_id`, `name`, `description`, `system_prompt`, `role`, `color`.
    - Propósito: Definición de personalidades dinámicas para el Orquestador.
 3. **`checkpoints`**:
    - Gestionada por: `langgraph-checkpoint-mongodb`.
    - Propósito: Memoria de estado y mensajes.

 ---

### **10 febrero, 2026 - Ingeniería de Datos Avanzada y Refacto de Proyecto (Noche)**

#### Hitos
- ✅ **ArXiv PDF Pipeline**: Implementación de `arxiv_pdf_spider.py`. Descarga exitosa de 7 papers clave (12.9 MB).
- ✅ **Ingesta de Libros Sintéticos CTO**: Integración de 7 libros del CTO (30,135 palabras) en MongoDB.
- ✅ **Pipeline de Datos CMO**:
    - Implementación de 3 spiders: `blogs_spider.py` (filtros avanzados por keywords), `frameworks_spider.py` (PDF & Web) y `case_studies_spider.py`.
    - Ingesta exitosa de 27 documentos CMO con arquitectura dual Bronze/Silver.
- ✅ **Pipeline de Datos CFO**:
    - Implementación de spiders especializados en Métricas SaaS, Regulación y Macroeconomía.
    - Debugging de error de infraestructura: identificado bloqueo SSL en MongoDB Atlas que impide el guardado remoto temporal.
- ✅ **Limpieza de "Noise"**: Algoritmo de extracción de referencias que eliminó 222 URLs embebidas, moviéndolas a metadatos para optimizar RAG.
- ✅ **Tooling de Procesamiento**: Lanzamiento de `pdf_processor.py` (Backend dual PyPDF2/pdfplumber).
- ✅ **Automatización Operativa**: Creación de `run_etl_cron.bat` y `README_CRON.md` para ejecuciones periódicas e incrementales.
- ✅ **Professional Environment**: Limpieza profunda de archivos temporales y optimización de `.gitignore` para estándares GitHub.

---

### **10 febrero, 2026 - Validación de Contratos y Conectividad (Noche)**

#### Hitos
- ✅ **Auditoría de CORS**: Verificación de la configuración en `main.py` para asegurar que el frontend en el puerto 3000 pueda comunicarse sin restricciones.
- ✅ **Validación de Contrato API**: Sincronización de esquemas entre `ChatRequest`/`ChatResponse` del backend y la interfaz `api.ts` del frontend.

---

### **10 febrero, 2026 - Evolución de la API de Sesiones (Noche)**

#### Hitos
- ✅ **Diseño de Endpoint `PATCH`**: Especificación técnica para permitir actualizaciones parciales de sesiones y su persistencia en `sessions_metadata`.
- ✅ **Auditoría de API**: Verificación de requerimientos para soportar Overrides visuales persistentes en el flujo de orquestación.

---

### **10 febrero, 2026 - Fase de Persistencia Atómica y Diferenciación de Chats (Cierre)**

#### Hitos
- ✅ **Evolución del Modelo de Sesión**: Implementación de `SessionType` (Enum: `group`, `direct`) en `sessions.py`.
- ✅ **Esquema de Metadatos Atómicos**: Extensión de `VisualConfig` para soportar `bubble_color` (propio de la sesión 1:1) y `theme` (propio del grupo), garantizando el aislamiento de personalizaciones.
- ✅ **Gestión de Miembros**: Habilitada la persistencia y actualización del campo `members` en las sesiones de grupo para control de orquestación.
- ✅ **CRUD de Sesiones Evolucionado**: Actualización de los endpoints `POST /` y `PATCH /{session_id}` para manejar la nueva lógica de tipos y metadatos extendidos.
- ✅ **Blindaje con Tests**: Creación de `tests/test_session_atomicity.py` para asegurar que las actualizaciones visuales sean atómicas por thread_id/session_id.
- ✅ **Arquitectura Lógica de 9 Capas**: Mapeo exhaustivo del orquestador (ADN a Escudo Térmico) documentado para máxima transparencia técnica.
- ✅ **README Profesional**: Despliegue de la guía técnica del orquestador premium en GitHub.
- ✅ **Skins (Lógica Side-Server)**: Implementada la recuperación automática de la identidad del agente desde los metadatos de la sesión en el flujo de streaming SSE.

---

### **10 febrero, 2026 - API de Actualización de Sesiones (Cierre de Sesión)**

#### Hitos
- ✅ **Endpoint PATCH Sessions**: Implementación de `PATCH /api/v1/sessions/{session_id}` en `sessions.py` para actualizaciones parciales.
- ✅ **Actualización Atómica de Metadatos**: Lógica para modificar títulos y `visual_config` sin alterar el resto del documento de sesión.
- ✅ **Integración con Motor**: Optimización de la consulta de actualización en MongoDB Atlas para asegurar atomicidad y consistencia.

---

 ## 🎯 Logros Clave
 
 ### ✅ Técnicos
 1. **Memoria Inquebrantable**: Uso de `add_messages` para persistencia histórica real en el grafo.
 2. **Resiliencia de Concurrencia**: Capacidad de manejar múltiples flujos en la misma sesión sin colisiones.
 3. **Atomicidad de Datos**: Garantizada la independencia de configuraciones visuales entre sesiones paralelas.
 4. **Deduplicación Inteligente**: Sistema incremental que evita descargas redundantes mediante `url_exists()`.
 5. **Medallion Architecture**: Pipeline Bronze → Silver consolidado con 31 documentos curados para el CTO.
 
 ---
 
 ---

### **19 marzo, 2026 - Evolución Masiva: RAG Personalizado, Agent CRUD Completo y UX Premium**

Sesión de alto impacto que transforma el backend de un prototipo funcional en una plataforma de agentes personalizados con knowledge base por agente, comparable a Google Gemini Gems.

#### Hitos — Fase 1: Bug Fixes Críticos (6 correcciones)

- ✅ **Validación de Agente Custom en Stream**: Añadida verificación en `stream.py` de que el agente custom asignado a una sesión sigue existiendo en MongoDB antes de iniciar el streaming. Si fue eliminado, devuelve HTTP 422 con mensaje claro en lugar de un 500 genérico. En `sessions.py`, `get_session_history` ahora devuelve `warning: "agent_deleted"` si el agente fue borrado.
- ✅ **Campo `agent_ref_type`**: Nuevo campo `"core" | "custom"` en el modelo `SessionBase` y `CreateSessionRequest`. Auto-detectado en `create_session`: si `base_agent_id` está en `CORE_AGENT_IDS` → `"core"`, si no → `"custom"`. Usado en `stream.py` para resolver `target_role` correctamente según el tipo de agente.
- ✅ **Modelo Dinámico por Agente Custom**: Nuevo campo `model_config: Optional[dict]` en `AgentState`. En `router_node`, al cargar un agente custom, se extrae `model` y `temperature` de su `brain_config`. En `agent_node`, si `model_config` existe, se crea un `ChatOpenAI` dinámico en lugar de usar el `llm_expert` global. Esto permite que cada agente custom use su propio modelo y temperatura.
- ✅ **Fix de Modelo Default**: Cambiado el default de `BrainConfig.model` de `"deepseek-r1"` a `"deepseek-chat"` para alinearse con el modelo real usado en el orquestador.
- ✅ **Limpieza de Checkpoints on Delete**: `delete_session` ahora elimina también los documentos de las colecciones `checkpoints` y `checkpoint_writes` donde `thread_id == session_id`, liberando la memoria de LangGraph al borrar una sesión.
- ✅ **Mejora de Prompts de Junta Directiva**: Refactorización completa de `DEFAULT_CORE_PROMPTS` en `orchestrator.py`. Cada agente (Oberon/CEO, Nexus/CTO, Vortex/CMO, Ledger/CFO) ahora tiene identidad, personalidad y contexto organizacional. Incluye directiva anti-imitación para que el LLM no copie patrones de respuestas previas del historial.
- ✅ **Filtrado de SystemMessages en Historial**: `agent_node` ahora filtra `SystemMessage` del historial para que el prompt actual siempre domine sobre conversaciones anteriores.

#### Hitos — Fase 2: Agent CRUD Completo

- ✅ **Endpoint `PATCH /api/v1/agents/{agent_id}`**: Actualización parcial de agentes con dot-notation de MongoDB (mismo patrón que `sessions.py`). Incluye `updated_at` timestamp automático.
- ✅ **Enhanced DELETE**: Al eliminar un agente, ahora también se eliminan todos sus vectores de `knowledge_base` donde `agent_target == agent_id` y todos sus archivos de GridFS donde `metadata.agent_id == agent_id`.
- ✅ **Validaciones de BrainConfig**: `system_prompt` (10-10,000 chars), `temperature` (0.0-2.0), `model` (validado contra `ALLOWED_MODELS`). Nuevo campo `description` en `AgentIdentity`.
- ✅ **Campo `documents_count`**: Nuevo campo en `CustomAgentResponse` que trackea el número de documentos subidos al agente.

#### Hitos — Fase 3: Sistema de Templates de Prompts

- ✅ **Nuevo módulo `app/core/templates.py`**: Catálogo estático con 10 templates de agentes especializados:
  - ⚖️ Asesor Legal (compliance, contratos)
  - 🧠 Psicólogo Clínico (CBT, bienestar)
  - 📊 Contador Público (impuestos, auditoría)
  - 🔬 Data Scientist (ML, estadística)
  - ✍️ Copywriter Creativo (branding, contenido)
  - 👥 Especialista en RRHH (talento, cultura)
  - 🎯 Sales Coach (negociación, pipeline)
  - 🎓 Tutor Académico (investigación, metodología)
  - 📋 Project Manager (agile, delivery)
  - 🏥 Asesor Médico (orientación basada en evidencia)
- ✅ **Endpoints**: `GET /api/v1/agents/templates` (con filtro por `category`) y `GET /api/v1/agents/templates/{template_id}`. Rutas definidas ANTES de `/{agent_id}` para evitar colisión con FastAPI.

#### Hitos — Fase 4: Pipeline de Documentos y RAG Personalizado

- ✅ **Nuevo módulo `app/core/document_processor.py`**: Pipeline completo de procesamiento:
  - **Parsing**: PDF (pymupdf/fitz), DOCX (python-docx), TXT/MD (UTF-8)
  - **Chunking**: Token-aware con tiktoken (cl100k_base), 512 tokens por chunk con 64 de overlap
  - **Embedding**: Batch con OpenAI `text-embedding-3-small` (1536 dims), batches de 20
  - **Storage**: Vectores en `knowledge_base` con `agent_target = agent_id` (reutiliza patrón existente)
  - **Cleanup**: `delete_document_vectors()` y `delete_agent_vectors()`
- ✅ **GridFS para Archivos Raw**: Nueva función `get_gridfs_bucket()` en `database.py`. Bucket `agent_files` con metadata de status de procesamiento (`pending` → `processing` → `completed` / `failed`).
- ✅ **Nuevo módulo `app/api/v1/documents.py`**: Endpoints RESTful anidados bajo `/api/v1/agents/{agent_id}/documents`:
  - `POST` — Upload (multipart), validación de tipo/tamaño/límite, procesamiento en `BackgroundTasks`
  - `GET` — Listar documentos del agente con status
  - `GET /{file_id}` — Status de procesamiento individual (para polling)
  - `DELETE /{file_id}` — Eliminar archivo + vectores
- ✅ **Integración RAG**: Cambio de UNA línea en `orchestrator.py` (`rag_role = target_role` en lugar de `"all"` para custom agents). El UUID del agente se pasa como `agent_target` al filtro de `$vectorSearch`.
- ✅ **Fallback RAG**: En `rag.py`, si un agente custom no tiene documentos propios (0 resultados), se hace fallback a `agent_target = "all"` para no dar contexto vacío.
- ✅ **Nuevos Índices**: `knowledge_base.agent_target`, `knowledge_base.source_file_id`, `message_ratings.(session_id, message_id)`.
- ✅ **Dependencias**: `python-multipart`, `pymupdf`, `python-docx`, `tiktoken` añadidas a `requirements.txt`.

#### Hitos — Fase 6 (Backend): Endpoints UX

- ✅ **Pins**: `POST/DELETE/GET /api/v1/sessions/{session_id}/pins` — Array `pinned_messages` en el documento de sesión usando `$addToSet` y `$pull` de MongoDB.
- ✅ **Ratings**: `POST /api/v1/sessions/{session_id}/ratings` — Colección `message_ratings` con upsert por `(session_id, message_id)`. Almacena rating (`up`/`down`), feedback opcional y metadata. Datos valiosos para futuro entrenamiento de IAs propias.
- ✅ **Folders/Tags**: Campos `folder` y `tags` añadidos a `UpdateSessionRequest` y procesados en `update_session`.

#### Hitos — Fase 7: Clean Architecture

- ✅ **Extracción de Pydantic Models**: Nuevo directorio `app/models/` con:
  - `session.py`: `SessionType`, `VisualConfig`, `ContextFile`, `SessionBase`, `CreateSessionRequest`, `UpdateSessionRequest`, `PinRequest`, `RatingRequest`
  - `agent.py`: `AgentIdentity`, `BrainConfig`, `CustomAgentCreate`, `CustomAgentUpdate`, `CustomAgentResponse`, `ALLOWED_MODELS`
  - `__init__.py`: Re-exports centralizados

---

## 📊 Estado Actual del Sistema

### Arquitectura Actualizada
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI    │────▶│  LangGraph   │────▶│  DeepSeek   │
│  /stream     │     │ Orchestrator │     │  (LLM)      │
│  /agents     │     │ + model_cfg  │     │  + Custom    │
│  /documents  │     └──────────────┘     └─────────────┘
│  /sessions   │            │
│  /templates  │            ▼
└─────────────┘     ┌──────────────┐     ┌─────────────┐
                    │     RAG      │────▶│  MongoDB    │
                    │  per-agent   │     │  Atlas      │
                    │  + fallback  │     │  + GridFS   │
                    └──────────────┘     └─────────────┘
```

### Endpoints Disponibles (Actualizado)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/stream/` | Streaming SSE con memoria + validación de agente |
| POST | `/api/v1/sessions/` | Crear sesión (con `agent_ref_type`) |
| GET | `/api/v1/sessions/` | Listar sesiones |
| PATCH | `/api/v1/sessions/{id}` | Actualizar sesión (+ folders/tags) |
| DELETE | `/api/v1/sessions/{id}` | Eliminar sesión + checkpoints |
| GET | `/api/v1/sessions/{id}/history` | Historial con warning de agente eliminado |
| POST | `/api/v1/sessions/{id}/pins` | Pinear mensaje |
| DELETE | `/api/v1/sessions/{id}/pins/{msg}` | Despinear mensaje |
| GET | `/api/v1/sessions/{id}/pins` | Listar mensajes pineados |
| POST | `/api/v1/sessions/{id}/ratings` | Rating de mensaje (up/down + feedback) |
| POST | `/api/v1/agents/` | Crear agente custom |
| GET | `/api/v1/agents/` | Listar agentes |
| GET | `/api/v1/agents/{id}` | Detalle de agente |
| PATCH | `/api/v1/agents/{id}` | Actualizar agente |
| DELETE | `/api/v1/agents/{id}` | Eliminar agente + KB + GridFS |
| GET | `/api/v1/agents/templates` | Catálogo de templates |
| GET | `/api/v1/agents/templates/{id}` | Template específico |
| POST | `/api/v1/agents/{id}/documents` | Upload documento (multipart) |
| GET | `/api/v1/agents/{id}/documents` | Listar documentos del agente |
| GET | `/api/v1/agents/{id}/documents/{fid}` | Status de procesamiento |
| DELETE | `/api/v1/agents/{id}/documents/{fid}` | Eliminar documento + vectores |
| GET | `/api/v1/health/health` | Health check + latencia DB |

### Colecciones MongoDB (`sphere_db`)
1. **`sessions_metadata`**: Sesiones con `agent_ref_type`, `folder`, `tags`, `pinned_messages`
2. **`custom_agents`**: Agentes con `documents_count`, `updated_at`, validaciones
3. **`knowledge_base`**: Vectores RAG con `agent_target` (core role o agent UUID), `source_file_id`
4. **`checkpoints` / `checkpoint_writes`**: Memoria LangGraph (limpiada on delete)
5. **`message_ratings`**: Ratings de mensajes para futuro entrenamiento de IAs
6. **`agent_files.*`**: GridFS bucket para archivos raw de documentos

### Archivos Nuevos Creados
| Archivo | Propósito |
|---------|-----------|
| `app/core/templates.py` | Catálogo de 10 templates de agentes |
| `app/core/document_processor.py` | Pipeline: parse → chunk → embed → store |
| `app/api/v1/documents.py` | CRUD de documentos por agente |
| `app/models/__init__.py` | Re-exports de Pydantic models |
| `app/models/session.py` | Models de sesión extraídos |
| `app/models/agent.py` | Models de agente extraídos |

---

---

### **20 marzo, 2026 - Integración n8n + Tool-Calling (ReAct Loop)**

#### Hitos

##### 1. **Infraestructura n8n**
- ✅ Servicio `sphere-n8n` en `docker-compose.yml` (puerto 5678, volumen persistente)
- ✅ Variables de entorno `N8N_*` (auth, encryption, webhook secret)
- ✅ Settings `N8N_BASE_URL`, `N8N_WEBHOOK_SECRET` en Pydantic config

##### 2. **Sistema de Tool-Calling (Nuevo paquete `app/tools/`)**
- ✅ **`registry.py`**: Patrón Registry con `SHARED_TOOLS` (globales) + `ROLE_TOOLS` (por rol)
- ✅ **`n8n_client.py`**: Cliente HTTP async (`httpx`) con HMAC-SHA256, timeouts y error handling
- ✅ **`shared_tools.py`**: 8 herramientas compartidas (Google Calendar + WhatsApp)
- ✅ **`ceo_tools.py`**: 3 herramientas de delegación (MongoDB directo, sin n8n)
- ✅ **`cfo_tools.py`**: 3 herramientas financieras (noticias, bolsa, análisis de mercado)
- ✅ **`cmo_tools.py`**: 4 herramientas de redes sociales (LinkedIn, Instagram, analytics, scheduling)
- ✅ **`cto_tools.py`**: 3 herramientas para Jules (agente async de Google)

##### 3. **Transformación del Grafo LangGraph (ReAct Loop)**
- ✅ `AgentState` += `tool_calls_remaining: int` (anti-loop, default 3)
- ✅ `agent_node` ahora ejecuta `llm.bind_tools(tools)` cuando el rol tiene herramientas
- ✅ Nuevo nodo `dynamic_tool_node` con `ToolNode` de `langgraph.prebuilt`
- ✅ Condición `should_use_tools`: verifica `tool_calls` en `AIMessage` + remaining > 0
- ✅ Grafo: `expert_agent → should_use_tools? → tool_node → expert_agent` (loop) o `→ END`

##### 4. **Streaming de Tool Events**
- ✅ Nuevos eventos SSE: `tool_start` (on_tool_start) y `tool_result` (on_tool_end)
- ✅ Integrados en el loop de `astream_events` sin afectar artifact streaming

##### 5. **Nuevas Colecciones MongoDB**
- ✅ `agent_tasks`: Tareas delegadas por el CEO con UUID, status, prioridad
- ✅ `tool_audit_log`: Registro de cada invocación de herramienta

### Arquitectura Actualizada (con Tool-Calling)
```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   FastAPI    │────▶│    LangGraph     │────▶│  DeepSeek   │
│  /stream     │     │  Orchestrator    │     │  (LLM)      │
│  /agents     │     │  + ReAct Loop    │     │  + bind_    │
│  /documents  │     │  + tool_node     │     │    tools()  │
│  /sessions   │     └──────────────────┘     └─────────────┘
│  /templates  │            │       │
└─────────────┘            ▼       ▼
                    ┌──────────┐  ┌──────────────┐
                    │   RAG    │  │  Tool Node   │
                    │ per-agent│  │  (21 tools)  │
                    │ +fallback│  │              │
                    └──────────┘  └──────────────┘
                         │              │
                         ▼              ▼
                    ┌──────────┐  ┌──────────────┐
                    │ MongoDB  │  │    n8n       │
                    │  Atlas   │  │  Webhooks    │
                    │ +GridFS  │  │  (16 paths)  │
                    └──────────┘  └──────────────┘
                                        │
                              ┌─────────┼─────────┐
                              ▼         ▼         ▼
                         Google    WhatsApp   Jules/
                        Calendar   Business   Social
```

### Herramientas por Rol (21 total)
| Rol | Herramientas | Via |
|-----|-------------|-----|
| **Todos** | calendar_list/create/update/delete/availability, whatsapp_send/notify/read | n8n |
| **CEO** | delegate_task, check_task_status, list_active_tasks | MongoDB |
| **CTO** | create_jules_task, check_jules_status, review_jules_output | n8n |
| **CFO** | get_financial_news, get_stock_data, get_market_analysis | n8n |
| **CMO** | post_to_linkedin, post_to_instagram, get_social_analytics, schedule_post | n8n |

### Archivos Nuevos Creados (Sesión 20 de Marzo)
| Archivo | Propósito |
|---------|-----------|
| `app/tools/__init__.py` | Package init |
| `app/tools/registry.py` | Registry: role → tools (shared + specific) |
| `app/tools/n8n_client.py` | Cliente HTTP async para n8n con HMAC |
| `app/tools/shared_tools.py` | 8 tools compartidas (Calendar + WhatsApp) |
| `app/tools/ceo_tools.py` | 3 tools de delegación (MongoDB) |
| `app/tools/cfo_tools.py` | 3 tools financieras |
| `app/tools/cmo_tools.py` | 4 tools de redes sociales |
| `app/tools/cto_tools.py` | 3 tools para Jules |

### Archivos Modificados (Sesión 20 de Marzo)
| Archivo | Cambio |
|---------|--------|
| `docker-compose.yml` | Servicio n8n + volumen |
| `.env` | Variables N8N_* |
| `app/core/config.py` | Settings N8N_BASE_URL, N8N_WEBHOOK_SECRET |
| `app/core/orchestrator.py` | ReAct loop, tool_node, bind_tools, prompts con herramientas |
| `app/api/v1/stream.py` | Eventos SSE tool_start/tool_result |
| `main.py` | Lifecycle N8NClient, load_all_tools, índices nuevos |

---

## 📋 Módulos Adicionales (Documentación Complementaria)

### `app/core/logger.py` — Sistema de Logging Estructurado
| Aspecto | Detalle |
|---------|---------|
| **Propósito** | Logging profesional con colores e iconos para debugging en tiempo real |
| **Loggers disponibles** | `checkpoint_logger`, `stream_logger`, `api_logger`, `db_logger` |
| **Formato** | ISO timestamp + nivel + icono + mensaje |
| **Niveles** | DEBUG (🔍), INFO (✅), WARNING (⚠️), ERROR (🔥), CRITICAL (💀) |
| **Colores** | ANSI escape codes para terminal (verde=INFO, amarillo=WARNING, rojo=ERROR) |

### `phantom_front.py` — Stress Test del SSE
| Aspecto | Detalle |
|---------|---------|
| **Propósito** | Herramienta CLI de diagnóstico para probar el endpoint SSE del backend |
| **Funcionalidad** | Simula peticiones de streaming, mide latencia, verifica formato de eventos |
| **Uso** | `python phantom_front.py` desde el directorio `backend/` |

### `tests/` — Suite de Tests Automatizados
| Archivo | Qué valida |
|---------|------------|
| `conftest.py` | Fixtures compartidas (MongoDB test, event loop) |
| `test_connection.py` | Conexión dual a MongoDB Atlas |
| `test_sessions.py` | CRUD de sesiones, tipos group/direct |
| `test_agents.py` | CRUD de agentes custom, templates |
| `test_checkpoint.py` | Persistencia de LangGraph checkpoints |
| `test_health.py` | Health check endpoint |
| `test_session_atomicity.py` | Actualizaciones atómicas por sesión |

**Ejecución**: `pytest tests/ -v` desde `backend/`

---

## 📦 Commits del 16-17 de Marzo, 2026 (No documentados previamente)

### 16 de Marzo — Sync Multirepo
- Migración de documentación desde repos individuales al monorepo
- Sync de cambios pendientes entre máquinas de desarrollo

### 17 de Marzo — Ajustes de Configuración y Componentes
- **Backend**: Cambios en configuración de endpoints API y ajustes de entorno
- **Frontend**: Actualización de componentes de artifacts y dependencias del proyecto

---

## 🔄 Reorganización del Proyecto — 01 de Abril, 2026

### Limpieza del Monorepo
Hoy realizamos una reorganización completa del proyecto multirepo para eliminar el desorden causado por la migración de repos individuales:

**Archivos eliminados de la raíz** (eran duplicados de los subdirectorios):
- `package.json`, `package-lock.json`, `eslint.config.js`, `index.html` → pertenecen a `frontend/`
- `requirements.txt`, `Procfile` → pertenecen a `backend/`
- `tsconfig.*.json`, `tailwind.config.js`, `postcss.config.js` → pertenecen a `frontend/`
- `status_backend.txt`, `status_frontend.txt`, `build_log.txt` → artefactos temporales
- `coverage/`, `public/`, `.agent/` → directorios generados/no trackeables
- `fix_podman_path.ps1` → script de Windows obsoleto

**Documentación centralizada**:
- Los `Resumen_Backend.md`, `Resumen_Frontend.md` duplicados dentro de `backend/` y `frontend/` fueron eliminados. Las copias canónicas están en la raíz del monorepo.

**`.gitignore` actualizado**:
- Reescrito para soportar estructura multirepo (Python + Node + ETL + ML)
- Cubre: secrets, __pycache__, node_modules, IDE files, data/raw, logs, build artifacts

### Auditoría de Calidad con IA
Hoy ejecutamos una auditoría exhaustiva del proyecto usando herramientas de IA, analizando:
- **Clean Architecture**: Separación de capas, dependencias, acoplamiento
- **Principios SOLID**: SRP, OCP, LSP, ISP, DIP en backend y frontend
- **Clean Code**: Longitud de funciones, naming, error handling, magic numbers
- **Comparación con estándares de la industria**: Google, Meta, Netflix, Anthropic

**Resultado: 6.5/10** — Ver `auditoria.md` para el análisis completo.

#### ¿Por qué es importante esta auditoría?
Encontrar fallos de calidad en un proyecto **no es malo — es madurez técnica**. Los proyectos estudiantiles típicos de DAM/DAW suelen tener puntuaciones de 3-4/10 en estas métricas. SPHERE está por encima del promedio por varias razones:

1. **Documentación exhaustiva**: La mayoría de TFGs tienen un README de 10 líneas. SPHERE tiene Bitácora, Resúmenes técnicos, y documentación por capas.
2. **Arquitectura consciente**: Separar backend/frontend, usar LangGraph, Pydantic, Zustand — son decisiones que demuestran pensamiento arquitectónico.
3. **Testing**: Tener 13 archivos de test es inusual en proyectos de fin de grado.
4. **Sistema de logging**: Los estudiantes suelen usar `print()`. SPHERE tiene logging estructurado por módulo.

Los problemas encontrados (falta de DI, God stores, sin autenticación) son **normales** en esta etapa y son exactamente los que se resuelven con experiencia profesional. El hecho de IDENTIFICARLOS demuestra que el proyecto tiene una base sólida para evolucionar.

---

## 🔮 Próximos Pasos

### Inmediato
1. **Configurar workflows n8n**: Crear workflows en `localhost:5678` para cada webhook path definido.
2. **OAuth Google Calendar**: Conectar credenciales OAuth2 de Google en n8n credential store.
3. **WhatsApp Business API**: Configurar token de WhatsApp Business o Twilio en n8n.
4. **IAs Propias**: Integración de vLLM en Runpod para inferencia con modelos custom.
5. ~~**Multi-usuario**: Sistema de autenticación JWT.~~ ✅ **COMPLETADO (19 abril)** — Firebase Auth + credentials store + aislamiento multi-tenant.

### Mejoras de Calidad (ver `auditoria.md` para plan completo)
1. **Capa de servicios**: Separar lógica de negocio de los routes FastAPI
2. **Inyección de dependencias**: Eliminar imports directos de `db` en routes
3. **Modularizar stores del frontend**: Dividir el God store en slices
4. **CI/CD**: GitHub Actions con tests automáticos

---

## 🔐 **19 de Abril, 2026 — Multi-Tenant + Hardening Production-Grade**

Semana de transformación de SPHERE de demo single-tenant a plataforma multi-usuario con aislamiento completo, rate limiting, validación de inputs y personalización profunda por usuario. Plan detallado en `PLAN_AUTH_MULTITENANT.md`.

### 🔒 Fix de Seguridad Crítico: RAG Leak Multi-Tenant

Durante la fase de planning detectamos que `app/core/rag.py` filtraba el `$vectorSearch` solo por `agent_target`, **no por `user_id`**. En cuanto hubiera >1 usuario, uno podía recuperar fragmentos de los documentos de otro.

- ✅ **Filter compound** `{$and: [{user_id: uid}, {agent_target: role}]}` en el pipeline `$vectorSearch`.
- ✅ **Índice vectorial** `vector_index` actualizado en Atlas para declarar `user_id` como filter field.
- ✅ **Script reproducible** en `backend/scripts/vector_index_definition.json` + `backend/scripts/backfill_user_id.py` para migración retroactiva.
- ✅ **`retrieve_context(query, role, user_id)`** ahora requiere user_id; el orchestrator lo propaga desde el JWT vía `AgentState`.

### 🔐 Fase 1-2: Auth Layer con Firebase + User Profile

- ✅ **`app/core/auth.py`**: `get_current_user` dependency con `firebase-admin`, verifica ID tokens y auto-provisiona documento User en MongoDB en el primer login.
- ✅ **Endurecido post-auditoría**: si Firebase no está inicializado en `ENVIRONMENT=production` → 503 hard fail (nunca más fallback silencioso a `dev_user`). En dev solo acepta `Bearer dev-token` explícito.
- ✅ **`app/models/user.py`**: schema Pydantic rico con `UIPreferences`, `ProfessionalProfile`, `CommunicationStyle`, `FinancialPreferences`, `UsageInfo`.
- ✅ **`app/api/v1/auth.py`**: `GET/PATCH /me`, `POST /me/onboarding/complete`, `GET /me/usage`, `GET/PUT/DELETE /me/agent-overrides/{role}`, `GET/POST/DELETE /me/contacts`.
- ✅ **Todos los endpoints v1** (`sessions`, `agents`, `chat`, `stream`, `documents`, `integrations`) protegidos con `Depends(get_current_user)`.

### 🧱 Fase 3: Aislamiento Multi-Tenant (Row-Level Scoping)

- ✅ **`app/core/tenant.py`**: helpers `scoped_find`, `scoped_insert`, `scoped_update`, `scoped_delete`, `scoped_find_paginated`, `require_owner`. Todos los queries que afectan a datos del usuario los usan.
- ✅ **Quitado `user_id = "default_user"`** como default en `Session` y `Agent`. Ahora siempre viene del JWT.
- ✅ **`thread_id`** multi-tenant: `f"{user_id}:{session_id}"` en LangGraph checkpoints, aislando estados entre usuarios de forma natural.
- ✅ **Índices compuestos** creados en lifespan para todas las colecciones:
  - `sessions_metadata`: `(user_id, created_at DESC)`
  - `custom_agents`: `(owner_user_id, created_at DESC)`
  - `oauth_credentials`: `(user_id, provider)` unique
  - `contacts`: `(user_id, type, value)` unique
  - `idempotency_keys`: `(user_id, idempotency_key)` unique + TTL 24h
  - `user_agent_overrides`: `(user_id, agent_role)` unique
  - `oauth_states`: TTL 10min

### 🔑 Fase 4-5: Credentials Store + OAuth Flows (GitHub/Notion/Slack)

- ✅ **`app/core/credentials.py`**: `CredentialsService` con `get_token`, `store_token`, `refresh`, `revoke`. Cifrado Fernet en reposo.
- ✅ **`app/integrations/providers/{github,notion,slack}.py`**: módulos con `authorize_url`, `exchange_code`, `refresh`, `revoke`.
- ✅ **`app/tools/clients/{github,notion,slack}_client.py`**: clientes HTTP atómicos con httpx + timeouts.
- ✅ **`app/api/v1/integrations.py`**: flujo OAuth completo — `/{provider}/connect` → autorización → `/{provider}/callback` → intercambio de code por token → almacenamiento cifrado. CSRF state firmado con HMAC + TTL en `oauth_states`.

### 🎭 Fase 6: Agent Overlay + USER_CONTEXT Injection

- ✅ **`app/core/agent_resolver.py`**: `resolve_agent_config(user_id, agent_role, user)` — combina prompt base + override del usuario (overlay pattern) + USER_CONTEXT.
- ✅ **`app/core/user_context.py`**: `build_user_context_block(user)` genera texto inyectable con nombre, rol profesional, estilo, idioma, moneda, nivel de confirmación.
- ✅ **Orchestrator cableado**: `agent_node` llama a `resolve_agent_config` antes de cada LLM invocation. `USER_CONTEXT` se prepend al system prompt automáticamente.
- ✅ **Colección `user_agent_overrides`**: delta privado por usuario (sin duplicar el prompt base), permitiendo que mejoras al prompt sistema se propaguen a todos salvo en los campos personalizados.

### 🛡️ Fase 7: Tool Input Hardening (Contacts Whitelist)

**Problema resuelto**: las tools (`_calendar_create_event`, `_whatsapp_send_message`, etc.) aceptaban destinatarios directamente del LLM — prompt injection podía hacer que un agente enviara mensajes a contactos arbitrarios.

- ✅ **`app/core/contacts_service.py`**: `is_authorized(user_id, tool_name, contact_value, contact_type)` + normalización (E.164 para teléfonos, lowercase para emails).
- ✅ **Colección `contacts`**: whitelist por usuario con permisos granulares por tool.
- ✅ **`app/core/tool_context.py`** (nuevo): propagación vía `ContextVar` de `user_id` y `confirmation_level` desde el orchestrator a los tools — sin romper los args_schema que ve el LLM.
- ✅ **Tools protegidos** (`shared_tools.py`): `_whatsapp_send_message`, `_whatsapp_send_notification`, `_calendar_create_event` validan contra whitelist; si falla, devuelven error estructurado `{error: "contact_not_authorized", hint}` que el LLM interpreta y pide al usuario añadir el contacto.
- ✅ **Tool confirmation**: `post_to_linkedin`, `post_to_instagram`, `schedule_post` ahora tienen campo `confirmed: bool` en schema. Si `tool_confirmation_level` ≠ `"never"` y `confirmed=False`, bloquean y devuelven `{error: "confirmation_required", action_summary}`.

### 📊 Fase 8: Rate Limiting + Token Budget

- ✅ **`app/core/redis_client.py`**: singleton async de Redis con health check al arranque.
- ✅ **`fastapi-limiter` + slowapi**: inicializado en lifespan con `FastAPILimiter.init(redis, identifier=user_or_ip_identifier)`. Identifier usa hash del Bearer token (no necesita verificar JWT en cada request).
- ✅ **Rate limits**: chat/stream 10 req/min, otros endpoints 30 req/min.
- ✅ **`app/core/token_budget.py`**: `check_available(user_id, estimated)` + `consume(user_id, actual)` con `$inc` atómico sobre `users.usage.tokens_used_today`. Reset automático a medianoche UTC.
- ✅ **Orchestrator integrado**: antes de cada LLM invocation llama a `check_available`; si agotó presupuesto, devuelve mensaje claro sin quemar la llamada. Después del response, consume los tokens reales (leyendo `usage_metadata` con fallback defensivo a `response_metadata.token_usage`).

### 🔐 Fase 9: Concurrencia + Transacciones + Resilience

- ✅ **Transacciones Mongo** en `sessions.create_session`: inserta session + idempotency_key atómicamente. Fallback a rollback manual si Mongo es standalone (no replica set).
- ✅ **Idempotency**: `POST /sessions` acepta header `Idempotency-Key`; si se repite, devuelve la session original sin duplicar. TTL 24h en la colección.
- ✅ **Fix bug `tool_calls_remaining`**: reset per turn en `router_node` (antes el contador decrementaba y persistía en el checkpoint, "mudando" al agente después de 3 tool calls).
- ✅ **`app/core/distributed_lock.py`**: lock Redis `SET NX EX` por `thread_id` para evitar que dos mensajes rápidos corrompan el checkpoint. Stream.py lo aplica antes de invocar el grafo.
- ✅ **Retry en n8n**: `tenacity` con exponential backoff (1s/2s/4s), 3 intentos, solo en errores transientes (5xx / timeouts).
- ✅ **`app/core/circuit_breaker.py`**: estado closed/open/half_open en Redis. Tras 5 fallos consecutivos → abierto 30s. Aplicado a `n8n_client`.
- ✅ **Stream cleanup**: `try/finally` en `stream.py` cierra cursores y httpx en `GeneratorExit`.

### 🏗️ Fase 10: Operaciones + Observabilidad

- ✅ **Fail-fast validation** en lifespan: en `ENVIRONMENT=production` aborta si faltan `FIREBASE_CREDENTIALS_PATH`, `FERNET_KEY`, `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, `REDIS_URL`. En dev solo warn.
- ✅ **Health checks** split: `/health/live` (liveness) y `/health/ready` (checa Mongo + Redis). Devuelve 503 si alguna dependencia crítica está caída.
- ✅ **Paginación**: `GET /sessions` con `limit` (max 200). Ready para extender a `agents` y `documents`.
- ✅ **Timeouts** explícitos: OpenAI embeddings 15s, DeepSeek 60s (`request_timeout` en `ChatOpenAI`), httpx clients 15-30s, n8n 30s.
- ✅ **Embedding cache** (`app/core/embedding_cache.py`): Redis con TTL 24h, key por hash normalizado del query + model. `rag.py` lo consulta antes de llamar a OpenAI.
- ✅ **Error sanitization**: `app/core/error_handling.py::safe_error_response` nunca incluye `str(e)` directo en la respuesta. `stream.py` lo usa.
- ✅ **CORS estricto**: `allow_methods=["GET","POST","PATCH","DELETE","OPTIONS"]`, `allow_headers=["Authorization","Content-Type","Idempotency-Key"]`. Quitado `["*"]`.
- ✅ **Security headers middleware**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.

### 📦 Nuevas dependencias

```
firebase-admin      # Auth layer
cryptography        # Fernet para cifrado de tokens
authlib             # OAuth flows
httpx-oauth         # Utilidades OAuth2
redis[hiredis]      # Rate limiting + locks + cache
fastapi-limiter     # Rate limiting middleware
tenacity            # Retry con backoff
fakeredis           # Tests
```

### 🔍 Auditoría Post-Implementación: Fix de Wiring

Después de la implementación inicial, verificación sistemática descubrió que 5 módulos existían pero no estaban conectados al flujo de ejecución:

| Módulo | Problema | Fix |
|---|---|---|
| `agent_resolver` + `user_context` | 0 llamadas desde orchestrator | Cableado en `agent_node` antes del LLM call |
| `token_budget.check_available/consume` | 0 llamadas | `check_available` antes del LLM, `consume` después con tokens reales |
| `contacts_service.is_authorized` | 0 llamadas desde tools | Propagación vía contextvar + check en cada tool destructivo |
| `fastapi-limiter` | En requirements, sin `init()` | `FastAPILimiter.init(redis, identifier=...)` en lifespan |
| Transacciones Mongo | No existían | `_atomic_create_session_with_idem` con fallback manual |

Este patrón — módulos presentes pero no cableados — es el típico "scaffolding sin wiring" que hace parecer un sistema más protegido de lo que realmente está. La verificación honesta y el fix posterior fueron esenciales para cerrar el loop.

### 📂 Ficheros nuevos (Backend)

**Core**:
- `app/core/auth.py`, `tenant.py`, `credentials.py`, `agent_resolver.py`, `user_context.py`, `contacts_service.py`, `token_budget.py`, `redis_client.py`, `distributed_lock.py`, `circuit_breaker.py`, `error_handling.py`, `pagination.py`, `embedding_cache.py`, **`tool_context.py`**

**Models**:
- `app/models/user.py`, `oauth_credential.py`

**API v1**:
- `app/api/v1/auth.py`, `integrations.py`

**Integraciones**:
- `app/integrations/providers/{github,notion,slack}.py`
- `app/tools/clients/{github,notion,slack}_client.py`

**Scripts**:
- `backend/scripts/vector_index_definition.json`, `backfill_user_id.py`

### 📚 Documentación

- `PLAN_AUTH_MULTITENANT.md` (raíz del repo): plan arquitectónico completo, 11 fases, decisiones con tradeoffs, estimación de esfuerzo y orden de implementación recomendado.

---

**Última actualización**: 19 de abril, 2026
**Estado del proyecto**: 🔐 **MULTI-TENANT PRODUCTION-GRADE** | Firebase Auth + row-level scoping + RAG multi-tenant seguro + OAuth GitHub/Notion/Slack + rate limiting dos capas + token budget + contacts whitelist + transacciones atómicas + distributed locks + circuit breaker. Cableado end-to-end con verificación post-implementación.
