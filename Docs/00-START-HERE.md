# 🧭 Punto de Entrada: Proyecto SPHERE

## Estado Actual: FASE 1 (Configuración & MVP)
Estamos en la etapa de inicialización (Greenfield). El objetivo es establecer una arquitectura robusta de bajo costo antes de desarrollar la lógica de negocio compleja.

## Documentación Crítica
⚠️ **Instrucción para el Agente:** Lee estos documentos antes de generar código.

1. **[01-PRD.md](./01-PRD.md)**: La "Biblia" del proyecto. Contiene la visión, el stack tecnológico híbrido y las reglas de negocio.

## Prioridades Inmediatas (Kanban: Doing)
1. Configurar el entorno local con **Podman** (Monorepo).
2. Establecer el esqueleto del Backend (**FastAPI** en Cloud Run).
3. Establecer el worker de inferencia (**vLLM** en Runpod).

## Arquitectura de Alto Nivel
* [cite_start]**Patrón:** Orquestación Centralizada (LangGraph)[cite: 177].
* [cite_start]**Infraestructura:** Híbrida Desacoplada (GCP Cloud Run + Runpod GPU)[cite: 182].
* [cite_start]**Frontend:** React + Vite (Streaming unidireccional vía SSE)[cite: 191].
