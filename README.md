# 🌌 SPHERE Frontend - Midnight Protocol UI

Interfaz de usuario ultra-premium diseñada para la orquestación de agentes de IA. Basada en una estética de "Sala de Guerra" con efectos de glassmorphism, animaciones Aurora y un espacio de trabajo dedicado para artefactos técnicos.

---

## ✨ Características Principales

- **Midnight Protocol**: Un sistema de diseño oscuro con acentos eléctricos (Cyan, Púrpura, Magenta).
- **Artifacts Workspace**: Panel lateral interactivo para visualizar y descargar código, tablas de datos, diagramas Mermaid y documentos Markdown.
- **Multisesión Concurrente**: Gestión de múltiples hilos de chat con streamings independientes y persistentes.
- **Agent Creation Wizard**: Wizard multi-step con 10 templates profesionales (Abogado, Psicólogo, Contador, etc.) y carga de archivos para RAG personalizado.
- **Knowledge Base Manager**: Gestión visual de documentos por agente con upload, progress bars, polling de status y drag & drop.
- **Agent Detail Page**: Página completa de edición de agentes con configuración de cerebro (prompt, modelo, temperatura) y knowledge base.
- **Chat UX Premium**: Búsqueda de mensajes, copiar al clipboard, regenerar respuesta, pin de mensajes, exportar conversación como Markdown, rating de respuestas (thumbs up/down).
- **SSE Integration**: Recepción de respuestas palabra por palabra para una sensación de fluidez absoluta.

---

## 🛠️ Stack Tecnológico

- **Framework**: React 18 + Vite
- **Estado Global**: Zustand (Tipado y Persistente)
- **Estilos**: Tailwind CSS v4 (Modern Design Tokens)
- **Animaciones**: Framer Motion
- **Visualización**: Mermaid.js, React-Syntax-Highlighter, React-Markdown.
- **Iconografía**: Lucide React

---

## 🏗️ Arquitectura de la Interfaz

La aplicación se organiza en componentes modulares:

- **Layout**: Sistema de paneles redimensionables mediante arrastre manual.
- **Store**: Cerebro reactivo único que centraliza la sincronización con el cluster de Atlas.
- **Artifacts Engine**: Detector inteligente basado en Regex que extrae bloques técnicos del flujo de texto e inyecta tarjetas interactivas.
- **Aurora Effects**: Sistema de partículas y degradados dinámicos para el fondo inmersivo.

---

## 🚀 Instalación y Desarrollo

### 1. Requisitos
- Node.js 18+
- Backend de SPHERE activo.

### 2. Configuración
Instala las dependencias necesarias:
```bash
npm install
```

### 3. Ejecución
Inicia el entorno de desarrollo:
```bash
npm run dev
```

---

## 📂 Estructura de Carpetas

- `src/components/chat`: ChatPanel, MessageBubble (con botones hover UX).
- `src/components/modals`: AgentSelectorModal, AgentCreationWizard (wizard multi-step).
- `src/components/agents`: KnowledgeBasePanel (gestión de documentos por agente).
- `src/components/artifacts`: ArtifactPanel, ArtifactCard.
- `src/components/sidebar`: Sidebar con historial de sesiones.
- `src/pages`: AgentDetailPage (edición de agentes), ChatSettingsPage, ProfilePage.
- `src/store`: Gestión de estado global con Zustand.
- `src/services`: Cliente API con 22+ métodos (streaming SSE, agents, documents, pins, ratings).
- `src/utils`: Exportación de chat, detección de artefactos.
- `src/types`: Interfaces TypeScript (Agent, AgentTemplate, AgentDocument, MessageRating).

---
*Firma: SPHERE Implementation Team*
*Fecha: Marzo, 2026*
