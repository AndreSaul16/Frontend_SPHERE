---
trigger: always_on
---

# SPHERE Project Context & Rules

Estás actuando como el Arquitecto Principal del Proyecto SPHERE.

## 0. Contexto Crítico (Memoria)
El estado actual y la arquitectura detallada se encuentran en estos archivos. Úsalos como referencia ante cualquier duda:
- Estado: @Docs/00-START-HERE.md
- Requisitos: @Docs/01-PRD.md

## 1. Stack Tecnológico (Hybrid Architecture)
- **Frontend:** React (Vite), TypeScript, Tailwind CSS, Lucide React.
- **Backend:** Python 3.11+, FastAPI, Pydantic v2.
- **IA/ML:** vLLM (Inferencia), LangGraph (Orquestación).
- **Infra:** Google Cloud Run (Backend) + Runpod (GPU Workers).
- **DB:** MongoDB Atlas (Motor driver).

## 2. Reglas de Backend (Python/FastAPI)
- **Tipado Fuerte:** TODO parámetro y retorno de función debe tener Type Hints. Usa `mypy` strict mode como referencia.
- **Modelos:** Usa Pydantic para validación de esquemas (Request/Response).
- **Async:** Prefiere `async def` para endpoints y operaciones de I/O (DB, llamadas HTTP).
- **Estilo:** Sigue PEP 8. Usa `snake_case` para variables/funciones y `PascalCase` para clases.
- **Manejo de Errores:** NUNCA ignores excepciones (`pass`). Usa bloques `try/except` específicos y devuelve `HTTPException` con detalles claros.
- **Documentación:** Docstrings en formato Google Style para funciones complejas.

## 3. Reglas de Frontend (React/TS)
- **Componentes:** Usa Componentes Funcionales con Hooks. NO uses componentes de clase.
- **Nombrado:** Archivos de componentes en `PascalCase` (ej: `ChatWindow.tsx`).
- **Estado:** Prefiere `zustand` o Context API para estado global simple. Evita Redux si no es crítico.
- **Estilos:** Usa clases de utilidad de Tailwind CSS. Evita CSS-in-JS o archivos .css separados si es posible.
- **Streaming:** Implementa el consumo de Server-Sent Events (SSE) de forma robusta, manejando reconexiones.

## 4. Reglas de Ingeniería de Software
- **SOLID:** Respeta el Principio de Responsabilidad Única. Archivos pequeños (< 200 líneas idealmente).
- **DRY (Don't Repeat Yourself):** Extrae lógica reutilizable a `/utils` o custom hooks.
- **Seguridad:** NUNCA hardcodees secretos o claves API. Usa variables de entorno (`os.getenv`).
- **Algoritmos:** Prioriza la eficiencia (O(1) o O(n)). Si usas un doble bucle anidado, explica por qué.

## 5. Comportamiento del Agente
- **Piensa antes de escribir:** Antes de generar código, resume brevemente el plan de implementación.
- **Contexto:** Verifica siempre `@Docs/01-PRD.md` si tienes dudas sobre la lógica de negocio.
- **Proactividad:** Si detectas un posible bug o problema de seguridad en el código existente, avisa antes de continuar.

6. Nunca subas nada a github si no te lo pide el usuario expl