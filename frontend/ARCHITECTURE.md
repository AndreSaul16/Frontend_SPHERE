# Frontend Architecture

**SPHERE Frontend** aplica principios de separación de responsabilidades a través de una arquitectura basada en **Capas (Layered)** y **Feature-Sliced Design**. Esto previene que la aplicación se vuelva un "spaghetti" de componentes y hooks acoplados a medida que crece.

## 🏗 Conceptos Clave

### 1. Estado Global vs Estado Local
Utilizamos **Zustand** para el estado global (`store`). Solo la información que debe ser accesible transversalmente (ej. estado de sesión, mensajes actuales del chat) vive aquí. El estado de la UI temporal (ej. inputs controlados, toggles de modales) se maneja localmente con `useState`.

### 2. Capa "Shared"
Cualquier botón, input o modal que no tenga lógica de negocio acoplada debe residir en `src/shared/ui/`. Estos son componentes "tontos" (Dumb Components) puramente presentacionales y estilizables con TailwindCSS.

### 3. Capa "Features" y "Widgets"
Los componentes complejos que SÍ están conectados al estado global o hacen fetching de datos se consideran "Smart Components". Se construyen ensamblando piezas de la capa `shared` y se agrupan por Feature (ej. `features/chat`, `features/auth`).

### 4. API Client Centralizado
Todas las llamadas a red están aisladas en `shared/api/`. Aquí reside la configuración del interceptor de Axios (para refresco de tokens de Firebase, inyección de headers) de forma que ningún componente de React llame directamente a `fetch()`. Esto facilita el testing y los cambios de endpoints.
