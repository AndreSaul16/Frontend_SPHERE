# 🚀 SPHERE Backend - Orquestador Multi-Agente Premium

SPHERE es un ecosistema de orquestación de agentes de IA diseñado para startups tecnológicas. Utiliza una arquitectura avanzada de **Recuperación Aumentada por Generación (RAG)** y un cerebro basado en **LangGraph** para delegar tareas entre expertos especializados (CEO, CTO, CFO, CMO) y agentes personalizados.

---

## 🛠️ Stack Tecnológico

- **Core**: Python 3.10+
- **Framework Web**: FastAPI (Asíncrono)
- **Cerebro IA**: LangGraph & LangChain
- **Modelos**: DeepSeek-Chat (Orquestación) & OpenAI (Embeddings)
- **Base de Datos**: MongoDB Atlas (Vector Search & Checkpointing)
- **Streaming**: Server-Sent Events (SSE)
- **Logging**: Colored Structured Logging

---

## 🏗️ Arquitectura Lógica (9 Capas)

El backend está diseñado de forma modular y altamente escalable:

1.  **Configuración y ADN**: Validación estricta de entorno con Pydantic Settings.
2.  **Observabilidad Estructurada**: Sistema de logs coloreados con iconos para diagnóstico rápido.
3.  **Persistencia Dual**: Cliente asíncrono para la API y síncrono para la memoria de LangGraph.
4.  **Conocimiento Semántico (RAG)**: Búsqueda vectorial filtrada por rol del agente.
5.  **Neocórtex (Orquestador)**: Grafo de estados que define la lógica de decisión y ejecución.
6.  **Gestión Administrativa**: CRUD de sesiones e identidades de agentes personalizados.
7.  **Sistema Nervioso SSE**: Generador de eventos en tiempo real para streaming de tokens y artefactos.
8.  **Servidor y Ciclo de Vida**: Gestión de startup/shutdown segura.
9.  **Auditoría y Escudo Térmico**: Suite de pruebas de estrés y validación de integridad.

---

## 🚀 Instalación y Uso

### 1. Requisitos Previos
- Python 3.10 o superior.
- Una instancia de MongoDB Atlas con Vector Search habilitado.
- API Keys de OpenAI y DeepSeek.

### 2. Configuración
Crea un archivo `.env` en la raíz con:
```env
MONGODB_URL=tu_url_de_atlas
OPENAI_API_KEY=tu_api_key
DEEPSEEK_API_KEY=tu_api_key
DB_NAME=sphere_db
```

### 3. Ejecución Local
```bash
cd backend
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows
pip install -r requirements.txt
python run_local.py --reload
```

---

## 📡 Endpoints Principales

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `POST` | `/api/v1/stream/` | Streaming SSE de chat con memoria histórica. |
| `POST` | `/api/v1/sessions/` | Creación de nuevas salas de guerra (chats). |
| `GET` | `/api/v1/health/health` | Estado del sistema y latencia de DB. |
| `POST` | `/api/v1/agents/` | Creación de agentes expertos personalizados. |

---

## 👻 Phantom Front (Diagnóstico)
El sistema incluye un simulador de frontend por consola para pruebas de stress y auditoría:
```bash
python phantom_front.py --audit
```

---
*Firma: SPHERE Implementation Team*
*Fecha: Febrero, 2026*
