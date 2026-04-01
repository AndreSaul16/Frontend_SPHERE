# 📔 Bitácora de Desarrollo: Proyecto SPHERE

**Semana: 26 - 30 de Enero, 2026**
**Objetivo: De Prototipo RAG a Ecosistema Multi-Agente Premium**

---

## 🌟 Resumen de la Semana

Esta semana hemos transformado SPHERE de una API de chat básica en una plataforma de orquestación inteligente con una interfaz de usuario de nivel empresarial.

### 🌓 Martes - Miércoles: El Cerebro (Backend)
- Consolidamos la base de conocimientos con **74 documentos vectorizados especializados**.
- Implementamos el **Orquestador LangGraph**, permitiendo que un Router inteligente (DeepSeek) delegue tareas entre el CEO, CTO, CFO y CMO.
- Perfeccionamos el sistema **RAG** para asegurar que cada agente tenga acceso solo a su documentación relevante.

### 🌔 Jueves: Los Sentidos (Frontend & Streaming)
- Lanzamos el **"Midnight Protocol"**, una estética visual oscura con acentos cian y púrpura.
- Implementamos **Streaming SSE**, permitiendo que las respuestas de los agentes fluyan palabra a palabra, mejorando drásticamente la percepción de velocidad.
- Añadimos la capacidad de personalizar la identidad de los agentes (renombrar y cambiar colores).

### 🌕 Viernes: La Maestría (Mobile & Artifacts)
Hoy ha sido el día de mayor impacto en la UX del usuario final:
- **Perfección Móvil**: Erradicación de bugs de scroll y solapamiento mediante `dvh`.
- **Artifacts Workspace**: Separación de la conversación del valor técnico con tarjetas descargables y visores de alta fidelidad.

### 🌑 Sábado: El Ecosistema (Custom Agents & Multisesión) - **HOY**
Hoy SPHERE ha dejado de ser un sistema cerrado para convertirse en una plataforma extensible:

#### 1. Agent Launcher: El Centro de Mando
Hemos reemplazado la lista fija de agentes por un **Lanzador Global**. 
- **Acción Unificada**: Un botón de "Nuevo Chat" que abre un selector categorizado (Core Board vs. Especialistas).
- **Búsqueda Instantánea**: Filtrado en tiempo real de expertos por nombre o especialidad.

#### 2. Expertos Personalizados (Custom Agents)
El usuario ahora tiene el poder de crear su propio equipo:
- **CRUD Completo**: Interfaz para crear, nombrar y dar instrucciones específicas (System Prompt) a nuevos agentes.
- **Inyección Dinámica**: El orquestador ya no depende de prompts estáticos; recupera las instrucciones del experto directamente de MongoDB.

#### 3. Multisesión Concurrente
Refactorización total del estado para permitir el multitasking:
- **Independencia Total**: Puedes hablar con el CTO en una pestaña mientras el CFO analiza datos en otra, con streamings que no interfieren entre sí.
- **Historial Vivo**: Indicadores de actividad animada en el sidebar para saber qué sesiones están recibiendo actualizaciones en segundo plano.

---
 
 ## 🛠️ Detalle Técnico: Consolidación del Cerebro (27 de Enero)
 
 ### Ingeniería de Datos & Vectorización
 - **`vectorize_corpus.py`**: Implementación del script de vectorización masiva usando el modelo `text-embedding-3-small` de OpenAI.
 - **Parchado de Seguridad**: Integración de `certifi` para resolver errores de apretón de manos SSL (`TLSV1_ALERT_INTERNAL_ERROR`) con MongoDB Atlas.
 - **Optimización de Contexto**: Ajuste dinámico del límite de tokens (corte a 20,000 caracteres) para evitar errores de longitud en documentos extensos de ArXiv.
 - **Validación Semántica**: Creación de `test_search.py` para verificar la precisión del `$vectorSearch` de MongoDB, logrando scores de relevancia de ~0.71 en conceptos abstractos.
 
 ### Backend & Orquestación
 - **Orquestador LangGraph**: Diseño del primer grafo de estados (`orchestrator.py`) con un Router inteligente basado en DeepSeek para clasificación de roles (CTO, CEO, CFO, CMO).
 - **Módulo RAG Atómico**: Creación de `rag.py` con filtrado por `agent_target`, asegurando que cada experto solo consulte su base de conocimientos específica.
 - **Migración de Pydantic v2**: Refactorización de `config.py` para usar `model_config` y `SettingsConfigDict`, resolviendo incompatibilidades de esquemas.
 - **Cuerpo FastAPI**: Implementación del primer endpoint de chat real (`/api/v1/chat/`) conectando el orquestador con el mundo exterior.
 
 ---
 
 ## 🛠️ Detalle Técnico de Hoy (31 de Enero)

### Backend Engineering
- **`agents.py`**: Implementación de la API CRUD para `custom_agents`.
- **`orchestrator.py`**: Refactor para interceptar IDs de agentes externos y realizar retrieval de prompts bajo demanda.
- **`database.py`**: Integración de nuevas colecciones para persistencia de expertos.
- **`stream.py` (Fix Crítico)**: Reparada la persistencia de mensajes; ahora se carga el estado previo del checkpoint (`aget_state`) para evitar sobreescribir el historial con arrays vacíos.

### Frontend Engineering
- **`useChatStore.ts`**: Migración a un modelo de mensajes indexados por sesión (`messagesBySession`). Implementado sistema de aislamiento `sessionsByAgent` y optimización de carga con caché local en `loadSession`.
- **`AgentSelectorModal.tsx`**: HUD táctico para la selección y creación de expertos.
- **`api.ts` (Validación)**: Implementado chequeo de `response.ok` en la creación de sesiones para erradicar las "sesiones fantasma" por fallos de red o backend.

---

### 🌑 Sábado (Noche): Refactorización Profunda y Estabilidad
Tras detectar los bugs críticos de persistencia, iniciamos una operación de "corazón abierto" en el backend:

#### 1. Arquitectura Dual de MongoDB (El Hito Técnico)
Hemos resuelto la incompatibilidad entre FastAPI y LangGraph:
- **Separación de Poderes**: Implementamos un cliente **Asíncrono (Motor)** para la API y un cliente **Síncrono (PyMongo)** exclusivo para el Checkpointer de LangGraph.
- **Fin de los Bloqueos**: Esta arquitectura elimina los riesgos de "Thread Starvation" y asegura que la memoria de los agentes sea inquebrantable.

#### 2. Blindaje con Testing (29 Tests en Verde)
No solo arreglamos el código, creamos el escudo:
- **Suite Completa**: 29 tests automatizados que validan desde la conexión hasta la persistencia de conversaciones complejas.
- **Resiliencia**: Corregimos errores de "Event Loop is closed" sincronizando los scopes de ejecución, asegurando que el backend sea estable en cualquier entorno (Docker, Local o CI/CD).

#### 3. Monitorización Táctica (Structured Logging)
SPHERE ahora "habla" en la terminal:
- **Logs Coloreados e ISO**: Implementamos un sistema de logging profesional que permite ver en tiempo real cómo el router toma decisiones y cómo fluyen los datos hacia MongoDB.

---

## 🚀 Febrero: Consolidación y Documentación (01 - 02 de Febrero)

### 🌓 Domingo 01 de Febrero: Refinado de Infraestructura
Cierre definitivo de la migración a la nube y ajustes de entorno:
- **Desconexión Total Local**: Eliminamos definitivamente el contenedor de MongoDB del `compose.yaml`. SPHERE ahora opera 100% sobre **MongoDB Atlas** en todos los entornos.
- **Persistencia Verificada**: Pruebas de estrés confirmaron que las sesiones se mantienen intactas tras reinicios de servicios, con metadatos en `sphere_db` y checkpoints en `checkpointing_db`.
- **Troubleshooting de Entorno**: Resolución de conflictos con variables de entorno para asegurar que los agentes puedan ejecutar procesos autónomos (como exploradores o scripts) sin restricciones.
- **Limpieza de UI y Estabilidad**: Erradicación del efecto "blob" en los mensajes y corrección de la sincronización del header del chat. Ejecución de suite de Stress Tests ("Caos en los Límites") con resultados satisfactorios.


### 🌔 Lunes 02 de Febrero: Transparencia Técnica y Open Source
Hoy nos enfocamos en la propiedad intelectual y la transferencia de conocimiento:
- **Documentación de Arquitectura**: Análisis exhaustivo de los 27 archivos del frontend. Generamos un mapa detallado de responsabilidades para cada componente (Zustand, SSE, Artifacts, Layout).
- **Frontend Open Source**: Lanzamiento oficial del repositorio del frontend en GitHub [AndreSaul16/Frontend_SPHERE](https://github.com/AndreSaul16/Frontend_SPHERE).
- **UML & Flowcharts**: Creación de diagramas de secuencia para el flujo de mensajes y diagramas de clases para el sistema de artefactos.

---

### 🌔 Martes 03 de Febrero: Hotfix de Navegación y Acceso a Configuración
Hoy hemos corregido un error en la experiencia de usuario que impedía el acceso rápido a la configuración del chat:
- **Hotfix de Navegación**: Modificado `ChatPanel.tsx` para redirigir al usuario a `/chat/settings` al hacer clic en el avatar del agente o en el botón de opciones del header (MoreVertical).
- **Desacoplamiento del Modal**: Se eliminó la apertura accidental del `AgentSelectorModal` desde la cabecera del chat, reservando su uso exclusivamente para el inicio de nuevas conversaciones desde la barra lateral.
- **Limpieza de Referencias**: Eliminada la dependencia de `toggleAgentModal` en el componente `ChatPanel` para optimizar el flujo de navegación y mejorar la mantenibilidad del código.

---

### 🌔 Martes 10 de Febrero: Auditoría de Esquema y Transparencia Datacentric
Hoy hemos realizado un "Deep Dive" técnico en la persistencia de SPHERE para consolidar el conocimiento del motor:
- **Auditoría de Esquema**: Documentación exhaustiva de las colecciones `sessions_metadata` y `custom_agents`.
- **Mapeo de Overrides**: Clarificación de cómo los metadatos de sesión permiten la personalización visual (avatar, color, nombre) sin afectar la lógica del agente base.
- **Estructura de Agentes Dinámicos**: Confirmación de la anatomía del `system_prompt` y metadatos en la colección de expertos, asegurando la escalabilidad del sistema de personalidades.
- **Diagnóstico de Persistencia de Identidad**: Identificado fallo en la propagación de `agent_id` hacia el checkpointer de LangGraph, afectando la recuperación del contexto visual en el frontend.

---

### 🌔 Martes 10 de Febrero (Tarde): Hotfix de UI y Navegación
Hoy hemos resuelto bugs críticos de la experiencia de usuario detectados tras la migración a la nube:
- **Sincronización de Header**: Corrección de la lógica en `useChatStore.ts` para que la cabecera utilice el `base_agent_id` de la sesión. Esto elimina el "congelamiento" visual donde el header no cambiaba al saltar entre diferentes chats.
- **Interactividad en Cabecera**: Activación de clics en el Avatar del agente y el botón de menú vertical del Header. Ahora ambos abren el modal de configuración, permitiendo ajustes rápidos de identidad sin salir del chat.
- **Refinado de UX**: Añadido feedback visual (hover y cursor de puntero) a los elementos interactivos del encabezado para cumplir con los estándares premium del proyecto.

---

### 🌔 Martes 10 de Febrero (Noche): Arquitectura Visual y Reactividad Frontend
Sesión de alto impacto en la infraestructura del cliente y el núcleo del frontend:
- **Arquitectura "WhatsApp Executive"**: Implementación de un layout de 3 columnas ultra-premium (Sidebar, Chat, Artifact Workspace) con Tailwind v4.
- **Cerebro Reactivo (Zustand)**: Creación de `useChatStore` para una gestión de estado centralizada y desacoplada del backend (Mock ready).
- **Tipado Estricto**: Definición de contratos de datos en `src/types/index.ts` para asegurar la integridad de mensajes y roles de agentes.
- **Restauración de Infraestructura**: Recuperación de `Dockerfile` y `.dockerignore` en el frontend, permitiendo el despliegue unificado con `podman-compose`.
- **Componentes de Swarm**: Creación de `Sidebar` dinámico, `ChatPanel` reactivo y el sistema de `MessageBubble` con soporte Markdown.


### 🌔 Martes 10 de Febrero (Noche): Ingeniería de Datos Avanzada y Consolidación de Corpus
Sesión de alto impacto en la base de conocimiento y el pipeline de datos:
- **Integración ArXiv**: Implementación de `arxiv_pdf_spider.py` para la descarga automatizada de 7 papers locales (13MB), actualizando el estado de procesamiento en MongoDB.
- **Libros Sintéticos CTO**: Ingesta de 7 libros especializados (30,135 palabras) con limpieza profunda de referencias embebidas (222 URLs extraídas a metadatos).
- **Pipeline CMO (Chief Marketing Officer)**: 
    - Implementación de 3 spiders especializados: `blogs_spider.py`, `frameworks_spider.py` y `case_studies_spider.py`.
    - Procesamiento de 27 documentos (Blogs, Frameworks y Casos de Estudio) en MongoDB y Bronze Layer.
    - Creación de `url_validator.py` con reporte de salud del 85.3% para el corpus de marketing.
- **Pipeline CFO (Chief Financial Officer)**:
    - Desarrollo de spiders para métricas SaaS, regulación (annual reports) y análisis macro.
    - Identificación y reporte de bug crítico: **MongoDB SSL Handshake Error (TLSV1_ALERT_INTERNAL_ERROR)**.
- **Infraestructura ETL**: Creación de `pdf_processor.py` (PyPDF2/pdfplumber) y sistema de automatización periódica `run_etl_cron.bat` con gestión de logs.
- **Auditoría de Corpus**: Consolidación de 31 documentos curados para el agente CTO, asegurando el estándar Silver Medallion.
- **Refactorización de Entorno**: Limpieza profunda de scripts temporales (`temp_*`) y profesionalización del `.gitignore` (55 líneas) para preparación de despliegue GitHub.

---

### 🌔 Martes 10 de Febrero (Noche - Fase Final): Integración Real, Estabilidad de Puertos y Seguridad
Fase final de conexión del ecosistema SPHERE:
- **Puente de Datos Real (`api.ts`)**: Implementación del servicio de comunicación con el backend, eliminando simulaciones y conectando el orquestador real.
- **Alineación de Infraestructura**: Estandarización del puerto **3000** en `vite.config.ts`, `Dockerfile` y `package.json`, resolviendo inconsistencias de conexión en contenedores.
- **Migración Tailwind v4**: Salto tecnológico a la versión 4 de Tailwind, moviendo la configuración del tema a `index.css` nativo y añadiendo fuentes premium (*Inter*, *JetBrains Mono*).
- **Blindaje XSS y Markdown**: Implementación de sanitización profunda con `rehype-sanitize` y resaltado de código con `rehype-highlight`. Se evitó el conflicto de borrado de clases mediante un orden de ejecución estrictamente planificado.
- **Aislamiento de Secretos**: Configuración de variables de entorno `.env` con prefijo `VITE_` para una gestión segura de URLs de API.

---

### 🌔 Martes 10 de Febrero (Noche - Fase de Personalización): Diagnóstico y Planificación de Configuración
- **Diagnóstico de Acceso**: Identificado el bug que impedía acceder a la configuración de los chats por falta de funcionalidad en el header de `ChatPanel.tsx`.
- **Ingeniería de Persistencia**: Diseño técnico de un endpoint `PATCH` para sesiones, permitiendo guardar overrides de identidad (nombre, avatar, color) en MongoDB.
- **Diseño de UI Reactiva**: Planificación de `SessionSettingsModal` para personalización dinámica de agentes por sesión.

### 🌔 Martes 10 de Febrero (Cierre): Persistencia Atómica y Diferenciación de Chats
Hoy hemos resuelto el problema de la "identidad compartida" entre chats y hemos dotado al sistema de la capacidad de distinguir entre grupos y conversaciones individuales:
- **Persistencia Atómica**: Refactorización total del modelo de sesiones para asegurar que las personalizaciones (nombre, colores, avatar) se guarden de forma única por cada `session_id`. Ya no se filtran cambios de un chat a otro.
- **Dualidad de Chats (Group vs Direct)**: 
    - **Chats 1:1**: Implementación de personalización individual con rueda de colores para burbujas de mensajes.
    - **Chats de Grupo**: Implementación del modo "Junta Directiva" con selección de paletas cromáticas predefinidas y gestión de miembros del grupo.
- **Ingeniería de Sincronización**: Actualización de los contratos de API y el estado de Zustand para soportar el nuevo esquema de metadatos extendido (`VisualConfig` evolucionado).
- **Validación de Integridad**: Creación de suite de pruebas para confirmar que las actualizaciones en una sesión no afectan a sesiones paralelas del mismo agente.

---

### 🌔 Martes 10 de Febrero (Noche - Final de Sesión): Transparencia y Personalización Atómica
Consolidación final de la arquitectura y la documentación del ecosistema:
- **Arquitectura de Backend (9 Capas)**: Mapeo exhaustivo del orquestador en capas lógicas (ADN, Observabilidad, Persistencia Dual, Conocimiento Semántico, Neocórtex, Gestión, Sistema Nervioso SSE, Servidor y Escudo Térmico).
- **Despliegue de READMEs Profesionales**: Lanzamiento de documentación corporativa detallada en los repositorios de GitHub, incluyendo guías de instalación, descripción de stack y diagramas lógicos.
- **Sistema de "Skins" (Meta-Customización)**: 
    - **Backend**: Implementada la persistencia de `base_agent_id` y `metadata` en la colección de sesiones. El orquestador ahora deduce la identidad lógica automáticamente desde el `session_id`.
    - **Frontend**: Implementado el renderizado jerárquico (Session Metadata > Base Agent) en `ChatPanel` y `Sidebar`, permitiendo que un mismo agente (ej: Oberon) tenga múltiples identidades visuales según el chat.

---

### 🌔 Martes 10 de Febrero (Noche - Fase de Sincronización): Consolidación de Ajustes y Persistencia Real
Cierre del ciclo de vida de configuración del chat:
- **Sincronización de Ajustes (Full Stack)**: Implementación exitosa del flujo de actualización de sesiones desde la UI hasta MongoDB Atlas.
- **Backend (API de Sesiones)**: Creación del endpoint `PATCH /api/v1/sessions/{session_id}` para permitir actualizaciones parciales de metadatos (título y configuración visual).
- **Frontend (Zustand & Store)**: Integración de la acción `updateSessionMetadata` que asegura la persistencia inmediata de los cambios del usuario sin necesidad de recargar la página.
- **UI de Configuración**: Refactorización de `ChatSettingsPage.tsx` para permitir la edición en tiempo real de la identidad de la sesión (nombre y color), priorizando los metadatos de sesión sobre el agente base.
- **Estabilidad de Tipado**: Resolución de errores de sintaxis y tipos en el store central, garantizando un despliegue sin errores de compilación (`tsc` verificado).

---

### 🌔 Martes 10 de Febrero (Noche - Fase de Estabilización y Build Final):
Sesión técnica de cierre de bugs para garantizar un despliegue de producción impecable:
- **Blindaje del Store (Zustand)**: Resolución de inconsistencias entre la interfaz `ChatState` y la implementación de `useChatStore.ts`. Se integró formalmente `updateSessionMetadata` al contrato de tipos.
- **Restauración de Configuración**: Recuperación de lógica crítica en `ChatSettingsPage.tsx` (gestión de avatares y miembros del grupo) tras refactorizaciones previas agresivas.
- **Compatibilidad TypeScript Avanzada**: Parche en `src/lib/errors.ts` para resolver el error `TS1294`. Se migró la sintaxis de los constructores para ser compatible con la regla `erasableSyntaxOnly` (Stage 3).
- **Limpieza de Build (Zero Warnings)**: Eliminación de importaciones y variables no utilizadas en `CodeBlock.tsx` y `ErrorOverlay.tsx`.
- **Hito de Verificación**: Ejecución exitosa de `npm run build` con código 0, validando que el bundle de producción está listo.

---

---

## 📔 Semana: 17 - 19 de Marzo, 2026
**Objetivo: De Ecosistema Multi-Agente a Plataforma de Agentes Personalizados con Knowledge Base**

---

## 🌟 Resumen de la Semana

Esta semana SPHERE ha dado el salto más ambicioso de su historia. Lo que era un sistema de chat multi-agente con cuatro roles fijos se ha transformado en una **plataforma completa de agentes personalizados** — comparable a Google Gemini Gems — donde el usuario puede crear expertos especializados (abogados, psicólogos, contadores), cargar documentos (PDF, DOCX, TXT) para personalizar su knowledge base, y organizar sus conversaciones con herramientas de productividad de nivel enterprise.

El trabajo se organizó en **7 fases secuenciales**, desde bug fixes críticos hasta refactoring de clean architecture, tocando **15 archivos existentes** y creando **9 archivos nuevos** con más de **5,000 líneas de código nuevo**.

### 🌓 Miércoles (Mañana): La Identidad (Prompts & Bugs)
La sesión comenzó con un diagnóstico profundo del flujo de la Junta Directiva. El CEO (Oberon) respondía como "Asistente General" en lugar de como un líder ejecutivo real. El problema era doble: prompts genéricos sin personalidad, y contaminación del historial de LangGraph con respuestas del prompt viejo.

**La solución fue quirúrgica**: prompts enriquecidos con identidad (nombre, contexto organizacional, reglas de comportamiento), filtrado de `SystemMessage` del historial, y directiva anti-imitación en el template. Adicionalmente, se identificaron y corrigieron 6 bugs críticos que afectaban la consistencia de sesiones directas, la resolución de agentes en el historial, y la limpieza de datos al borrar sesiones.

### 🌔 Miércoles (Tarde): El Cerebro Expandido (CRUD + Templates + RAG)
Con los cimientos estables, se construyeron tres capas fundamentales:

1. **CRUD Completo de Agentes**: Endpoint PATCH para actualización parcial, DELETE que limpia toda la KB asociada, y validaciones profesionales de BrainConfig.

2. **Sistema de Templates**: Un catálogo de 10 perfiles profesionales — desde Asesor Legal hasta Sales Coach — cada uno con system prompt detallado, temperatura óptima y sugerencias de archivos. El usuario ya no parte de cero al crear un experto.

3. **Pipeline de RAG Personalizado**: El hito técnico más significativo. Un pipeline completo que recibe un archivo (PDF, DOCX, TXT, MD), lo parsea con pymupdf/python-docx, lo divide en chunks de 512 tokens con overlap de 64 usando tiktoken, genera embeddings con OpenAI `text-embedding-3-small`, y los almacena en MongoDB Atlas Vector Search con `agent_target = agent_id`. La integración con el sistema existente fue elegante: **un cambio de una sola línea** en el orquestador conectó todo el pipeline, porque el filtro `agent_target` ya existía para los agentes core.

### 🌕 Miércoles (Noche): Los Sentidos (Frontend UI & UX Premium)
La sesión nocturna se dedicó a la interfaz. Tres componentes masivos construidos en paralelo:

- **AgentCreationWizard** (1455 líneas): Un wizard de 4 pasos con selección de templates por categoría, configuración detallada, carga de archivos con drag & drop, y vista de revisión final.
- **KnowledgeBasePanel** (532 líneas): Gestión visual de documentos con indicadores de status animados, upload con progress bars reales (XMLHttpRequest), y polling automático cada 3 segundos.
- **AgentDetailPage** (793 líneas): Página completa de edición con secciones para identidad, cerebro (prompt + modelo + temperatura), knowledge base embebida, y zona de peligro para eliminación.

Simultáneamente, se añadieron **8 features UX** al chat:
- 🔍 **Búsqueda de mensajes** con filtrado local y counter de resultados
- 📋 **Copiar al clipboard** con feedback visual (Check verde por 2 segundos)
- 🔄 **Regenerar respuesta** del último mensaje AI
- 📌 **Pin de mensajes** persistido en MongoDB con vista filtrada
- 📥 **Exportar conversación** como Markdown formateado
- 👍👎 **Rating de respuestas** (datos para futuro entrenamiento de IAs propias)
- 📁 **Carpetas y tags** para organización de sesiones
- ✏️ **Editar/borrar mensaje** de usuario

### 🌑 Miércoles (Cierre): La Limpieza (Refactoring)
Para cerrar, se aplicó refactoring de clean architecture: extracción de Pydantic models a `app/models/`, eliminación total de los `window[]` globals del artifact streaming (reemplazados por state de Zustand), y documentación exhaustiva.

---

## 🛠️ Detalle Técnico del 19 de Marzo

### Backend Engineering (7 archivos nuevos, 8 modificados)

**Nuevos Módulos:**
- `app/core/templates.py`: Catálogo estático con dataclasses, 10 templates con system prompts de producción
- `app/core/document_processor.py`: Pipeline parse → chunk → embed → store con error handling y background processing
- `app/api/v1/documents.py`: REST endpoints para gestión de documentos por agente
- `app/models/session.py`: Pydantic models extraídos de sessions.py
- `app/models/agent.py`: Pydantic models extraídos de agents.py

**Cambios Críticos en Archivos Existentes:**
- `orchestrator.py`: Prompts enriquecidos, `model_config` en AgentState, LLM dinámico, filtrado de SystemMessage, RAG per-agent (1 línea), metadata de agente en respuestas
- `agents.py`: Reescritura total — PATCH endpoint, templates endpoints, validaciones, enhanced DELETE con KB cleanup
- `sessions.py`: `agent_ref_type`, pins/ratings/folders endpoints, checkpoint cleanup on delete, warning de agente eliminado
- `stream.py`: Validación de agente custom, resolución por `agent_ref_type`
- `rag.py`: Fallback a "all" para custom agents sin documentos propios
- `database.py`: `get_gridfs_bucket()` para almacenamiento de archivos
- `main.py`: Router de documentos, índices para knowledge_base y message_ratings
- `requirements.txt`: python-multipart, pymupdf, python-docx, tiktoken

### Frontend Engineering (4 archivos nuevos, 7 modificados)

**Nuevos Componentes:**
- `AgentCreationWizard.tsx` (1455 líneas): Wizard multi-step con AnimatePresence
- `KnowledgeBasePanel.tsx` (532 líneas): Gestión de KB con polling y drag & drop
- `AgentDetailPage.tsx` (793 líneas): Página de edición completa
- `exportChat.ts` (52 líneas): Utilidad de exportación Markdown

**Cambios en Archivos Existentes:**
- `useChatStore.ts`: agent_ref_type, VALID_ROLES, streamingArtifactBySession (5 window[] eliminados), onRole fix
- `api.ts`: 12 nuevos métodos (templates, update agent, documents, pins, ratings)
- `types/index.ts`: AgentTemplate, AgentDocument, MessageRating, agent_ref_type en ChatSession
- `ChatPanel.tsx`: Búsqueda, pins toggle, exportar, rating props, filteredMessages
- `MessageBubble.tsx`: 7 botones hover (copy, pin, regen, rate up, rate down, edit, delete), grupo CSS
- `AgentSelectorModal.tsx`: Modelo default fix, wizard integration
- `App.tsx`: Ruta `/agents/:agentId`

### Métricas de Impacto
- **Archivos nuevos**: 9 (backend) + 4 (frontend) = 13
- **Archivos modificados**: 8 (backend) + 7 (frontend) = 15
- **Líneas nuevas estimadas**: ~5,000+
- **Endpoints nuevos**: 13 (de 5 a 22 totales)
- **Templates creados**: 10 perfiles profesionales
- **Bugs corregidos**: 8 (6 backend + 2 frontend)
- **Features UX nuevas**: 8

---

---

---

## 📔 Jueves 20 de Marzo, 2026
**Objetivo: Integración n8n + Tool-Calling para Agentes C-Suite**

---

## 🌟 Resumen de la Sesión

Esta sesión marca la transición de SPHERE de un sistema de chat inteligente a una **plataforma de agentes con capacidad de acción real**. Los agentes C-Suite ya no solo generan texto — ahora pueden ejecutar herramientas externas: consultar calendarios, enviar mensajes por WhatsApp, publicar en redes sociales, obtener datos de bolsa en tiempo real, delegar tareas a otros agentes, y enviar código a Jules (agente async de Google).

La arquitectura elegida fue **Backend Tool-Calling + n8n Webhooks**: LangGraph ejecuta un ReAct loop nativo (`bind_tools()` + `ToolNode`), y n8n maneja la complejidad de OAuth, rate limits y APIs externas como capa de ejecución de workflows.

### Decisiones Arquitectónicas Clave

1. **¿Por qué n8n y no MCP directo?**: MCP (stdio) es para integraciones locales de IDE. n8n como contenedor Podman ofrece UI visual para workflows, nodos nativos de Google Calendar, WhatsApp Business, LinkedIn, y manejo de credenciales OAuth sin tocar el backend.

2. **¿Por qué ReAct loop en LangGraph?**: `ToolNode` de `langgraph.prebuilt` + `bind_tools()` de LangChain es la forma nativa de agregar herramientas. El grafo pasó de lineal (`router → agent → END`) a cíclico (`router → agent → tools? → agent → END`), con anti-loop de 3 iteraciones máximas.

3. **¿Por qué herramientas compartidas?**: Google Calendar y WhatsApp son transversales a todos los roles ejecutivos. Se registran como `SHARED_TOOLS` en el registry y se concatenan con las tools específicas de cada rol.

---

## 🛠️ Detalle Técnico del 20 de Marzo

### FASE 0: Infraestructura n8n
- **`docker-compose.yml`**: Nuevo servicio `sphere-n8n` (imagen `n8nio/n8n:latest`), puerto 5678, volumen persistente `n8n_data`, basic auth, encryption key, timezone `America/Bogota`.
- **`.env`**: Variables `N8N_AUTH_USER`, `N8N_AUTH_PASSWORD`, `N8N_ENCRYPTION_KEY`, `N8N_BASE_URL`, `N8N_WEBHOOK_SECRET`.
- **`config.py`**: Settings `N8N_BASE_URL` y `N8N_WEBHOOK_SECRET` en Pydantic.

### FASE 1: Fundamento de Tool-Calling (Cambio más crítico)
**Nuevo paquete: `app/tools/`** con 7 módulos:

- **`registry.py`**: Patrón Registry — `SHARED_TOOLS` (globales) + `ROLE_TOOLS` (por rol). Función `get_tools_for_role(role)` retorna `shared + role_specific`. Función `load_all_tools()` importa todos los módulos de tools al inicio.

- **`n8n_client.py`**: Cliente HTTP async (`httpx.AsyncClient`) con:
  - HMAC-SHA256 en header `X-Webhook-Signature` para autenticación
  - Connection pooling, timeouts configurables por tool
  - Manejo graceful de errores (timeout, HTTP error, connection error)
  - Lifecycle: `start()` en lifespan startup, `close()` en shutdown

- **`orchestrator.py`** (cambios):
  - `AgentState` += `tool_calls_remaining: int` (anti-loop, default 3)
  - `agent_node` ahora hace `llm.bind_tools(tools)` cuando el rol tiene herramientas
  - Nuevo nodo `dynamic_tool_node`: carga tools dinámicamente según el rol actual
  - Nueva condición `should_use_tools`: verifica `tool_calls` en último `AIMessage` + remaining > 0
  - Grafo: `expert_agent → should_use_tools? → tool_node → expert_agent (loop)` o `→ END`
  - Prompts de los 4 agentes core enriquecidos con sección de herramientas disponibles

- **`stream.py`**: Nuevos eventos SSE `tool_start` (on_tool_start) y `tool_result` (on_tool_end) en el loop de `astream_events`.

- **`main.py`**: Inicialización de `N8NClient` en lifespan, `load_all_tools()`, índices MongoDB para `agent_tasks` y `tool_audit_log`.

### FASE 2: Herramientas Compartidas — Google Calendar + WhatsApp
**`shared_tools.py`**: 8 herramientas registradas como `SHARED_TOOLS`:

| Herramienta | Tipo | Webhook n8n |
|-------------|------|-------------|
| `calendar_list_events` | Lectura | `/webhook/shared/calendar-list` |
| `calendar_create_event` | Escritura | `/webhook/shared/calendar-create` |
| `calendar_update_event` | Escritura | `/webhook/shared/calendar-update` |
| `calendar_delete_event` | Escritura | `/webhook/shared/calendar-delete` |
| `calendar_check_availability` | Lectura | `/webhook/shared/calendar-availability` |
| `whatsapp_send_message` | Escritura | `/webhook/shared/whatsapp-send` |
| `whatsapp_send_notification` | Escritura | `/webhook/shared/whatsapp-notify` |
| `whatsapp_read_messages` | Lectura | `/webhook/shared/whatsapp-read` |

Cada tool implementada como `StructuredTool.from_function()` con `args_schema` Pydantic y `coroutine` async que llama al `n8n_client`.

### FASE 3: CEO — Herramientas de Delegación
**`ceo_tools.py`**: 3 tools intra-sistema (MongoDB directo, sin n8n):
- `delegate_task`: Crea documento en colección `agent_tasks` con UUID corto, assigned_to, description, priority
- `check_task_status`: Query por task_id o assigned_to
- `list_active_tasks`: Filtra status `pending`/`in_progress`

**Nueva colección MongoDB: `agent_tasks`** con schema `task_id`, `created_by`, `assigned_to`, `description`, `priority`, `status`, `result`, timestamps.

### FASE 4: CFO — Noticias Financieras y Bolsa
**`cfo_tools.py`**: 3 tools via n8n:
- `get_financial_news` → `/webhook/cfo/financial-news` (topic, date_range, limit)
- `get_stock_data` → `/webhook/cfo/stock-data` (symbol, period)
- `get_market_analysis` → `/webhook/cfo/market-analysis` (sector, metrics)

### FASE 5: CMO — Redes Sociales
**`cmo_tools.py`**: 4 tools via n8n:
- `post_to_linkedin` → `/webhook/cmo/linkedin-post`
- `post_to_instagram` → `/webhook/cmo/instagram-post`
- `get_social_analytics` → `/webhook/cmo/social-analytics`
- `schedule_post` → `/webhook/cmo/schedule-post`

### FASE 6: CTO — Integración Jules
**`cto_tools.py`**: 3 tools via n8n:
- `create_jules_task` → `/webhook/cto/jules-create` (async, retorna task_id)
- `check_jules_status` → `/webhook/cto/jules-status`
- `review_jules_output` → `/webhook/cto/jules-review`

### FASE 7: Frontend — Visualización de Tools
- **`ToolExecutionCard.tsx`**: Componente React con animación Framer Motion, estados `running`/`completed`, card colapsable con resultado expandible. Labels descriptivos en español para las 21 herramientas.
- **`api.ts`**: Callbacks `onToolStart` y `onToolResult` en `StreamCallbacks`, parser SSE extendido.
- **`useChatStore.ts`**: Handlers que insertan marcadores `[TOOL_START:name]` y `[TOOL_RESULT:name:result]` en el contenido del mensaje bot.
- **`MessageBubble.tsx`**: Regex combinado que detecta `[ARTIFACT:...]`, `[TOOL_START:...]` y `[TOOL_RESULT:...]` en un solo paso. Las tool cards reemplazan el estado `running` por `completed` cuando llega el resultado.

### Métricas de la Sesión
- **Archivos nuevos**: 8 (backend) + 1 (frontend) = 9
- **Archivos modificados**: 5 (backend) + 3 (frontend) = 8
- **Herramientas implementadas**: 21 total (8 shared + 3 CEO + 3 CFO + 4 CMO + 3 CTO)
- **Webhooks n8n definidos**: 16 paths
- **Nuevos eventos SSE**: 2 (`tool_start`, `tool_result`)
- **Nuevas colecciones MongoDB**: 2 (`agent_tasks`, `tool_audit_log`)

### Seguridad Implementada
- HMAC-SHA256 en cada request backend→n8n
- n8n UI protegido con basic auth
- Validación Pydantic estricta en args_schema
- Anti-loop: máximo 3 tool_calls por turno
- Secrets de APIs externas aislados en n8n credential store

---

## 🚀 Conclusión del Estado Actual
SPHERE ha completado su transformación de una plataforma de chat multi-agente a un **ecosistema de agentes con capacidad de acción real**. Los agentes C-Suite ahora pueden ejecutar 21 herramientas externas, desde consultar calendarios hasta delegar código a Jules y publicar en redes sociales.

**Stack actualizado**: FastAPI + LangGraph (ReAct) + n8n + MongoDB Atlas + React + Podman

**Próximos pasos**:
1. Configurar workflows en n8n UI (`localhost:5678`) para cada webhook path
2. Conectar OAuth de Google Calendar y WhatsApp Business en n8n
3. Integrar API de Jules cuando esté disponible
4. IAs propias con vLLM en Runpod
5. Autenticación multi-usuario JWT

---
*Firma: SPHERE Implementation Team*
*Fecha: 20 de Marzo, 2026*
