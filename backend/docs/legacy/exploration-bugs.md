# Exploration: Bug Hunt — SPHERE Project

## Current State
El proyecto tiene un frontend React+Vite (Docker/nginx) y un backend FastAPI+MongoDB+LangGraph. Los errores reportados en consola revelan múltiples bugs interconectados.

## Bugs Encontrados

### 🔴 BUG 1 (CRÍTICO): `scoped_find` es async pero se llama sin `await`

**Archivo:** `backend/app/api/v1/sessions.py:224` + `backend/app/core/tenant.py:15`

```python
# sessions.py línea 224 — FALTA await
cursor = scoped_find(sessions_collection, user_id)  # ← devuelve coroutine, NO cursor
cursor = cursor.sort("created_at", -1).limit(...)    # ← AttributeError en coroutine
```

`scoped_find` en `tenant.py` está declarada como `async def`, pero `collection.find()` en Motor es **síncrono** (devuelve cursor sin await). Al llamarla sin `await`, `cursor` es un objeto coroutine que no tiene `.sort()` ni `.limit()`.

**Resultado:** `AttributeError` → capturado por `except Exception` → **HTTP 500**.

Este es EL bug principal que causa el `GET /sessions/ 500`.

**Fix:** Cambiar `scoped_find` de `async def` a `def` (como `collection.find()` no es coroutine):
```python
# tenant.py
def scoped_find(  # ← quitar async
    collection: AsyncIOMotorCollection,
    user_id: str,
    filter: Optional[dict] = None,
    **kwargs,
) -> AsyncIOMotorCursor:
    query = {**(filter or {}), "user_id": user_id}
    return collection.find(query, **kwargs)
```

---

### 🟡 BUG 2 (MEDIO): `VITE_API_URL` undefined en Docker build

**Archivo:** `frontend/Dockerfile`

El Dockerfile no pasa `VITE_API_URL` como build arg. Vite bakea las env vars al momento de `npm run build`, pero el `.env` del frontend probablemente no existe o no tiene la variable.

```dockerfile
# Falta:
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
```

**Resultado:** El frontend usa el fallback `http://localhost:8000/api/v1`. Esto funciona en desarrollo local pero falla en Docker (el backend está en `sphere-backend:8000`, no `localhost:8000`).

**Fix:** Agregar ARG/ENV al Dockerfile Y pasar el arg en `compose.yaml`:
```yaml
# compose.yaml - frontend service
frontend:
  build:
    context: ./frontend
    args:
      VITE_API_URL: http://localhost:8000/api/v1  # o la URL correcta
```

---

### 🟡 BUG 3 (MEDIO): `fetchSessions` no propaga errores al ErrorOverlay

**Archivo:** `frontend/src/store/useChatStore.ts:172-179`

```python
fetchSessions: async () => {
    try {
        const sessions = await chatService.getSessions();
        set({ sessions });
    } catch (error) {
        console.error('Error fetching sessions:', error);
        // ← NO actualiza errorStates, el usuario nunca ve el error
    }
},
```

El error se loggea pero no se setea en `errorStates`, así que el `ErrorOverlay` nunca muestra nada. El usuario ve una pantalla vacía sin saber qué pasó.

**Fix:**
```typescript
} catch (error: any) {
    console.error('Error fetching sessions:', error);
    set((state) => ({
        errorStates: { ...state.errorStates, fetch_agents: error.message }
    }));
}
```

---

### 🟡 BUG 4 (MEDIO): `sessionBaseAgent: undefined` — downstream de BUG 1

**Archivo:** `frontend/src/store/useChatStore.ts:409-410`

```typescript
const session = state.sessions.find(s => s.session_id === sessionId);
let detectedAgentId = session?.base_agent_id || 'group-chat';
```

Como `fetchSessions` falla (BUG 1), `state.sessions` está vacío, entonces `session` es `undefined` y `detectedAgentId` cae a `'group-chat'` siempre. Esto rompe la carga de historial de sesiones directas.

**Fix:** Se resuelve automáticamente al fixear BUG 1. Pero el código debería manejar el caso gracefully:
```typescript
if (!session) {
    console.warn(`Session ${sessionId} not found in cache, fetching from server...`);
    // Podríamos hacer un fetch individual aquí
}
```

---

### 🟢 BUG 5 (LOW): `proxy.js:1 Uncaught Error: Attempting to use a disconnected port object`

**No es un bug del proyecto.** Es un error de React DevTools / browser extension. Ocurre cuando el extension port se desconecta (navegación, refresh, etc.). Se puede ignorar.

---

### 🟡 BUG 6 (MEDIO): `createNewSession` hardcodea `user_id: "default_user"`

**Archivo:** `frontend/src/store/useChatStore.ts:266`

```typescript
const sessionPayload = {
    ...
    user_id: "default_user",  // ← hardcodeado, ignora el usuario real
    ...
};
```

El backend obtiene `user_id` del JWT (`user["firebase_uid"]`), así que este campo se ignora. Pero es misleading y podría causar problemas si alguien cambia la lógica del backend.

**Fix:** Eliminar el campo `user_id` del payload (el backend lo obtiene del token).

---

### 🟡 BUG 7 (MEDIO): Error handling inconsistente en `getSessionHistory`

**Archivo:** `frontend/src/services/api.ts:261-266`

```typescript
async getSessionHistory(sessionId: string): Promise<any> {
    const response = await fetch(`${API_URL}/sessions/${sessionId}/history`, {
        headers: await authHeaders(),
    });
    return response.json();  // ← NO checkea response.ok
},
```

Si el backend devuelve 401, 403, 500, etc., el frontend parsea el body como JSON sin verificar el status. Esto puede causar errores confusos downstream.

**Fix:**
```typescript
async getSessionHistory(sessionId: string): Promise<any> {
    const response = await fetch(`${API_URL}/sessions/${sessionId}/history`, {
        headers: await authHeaders(),
    });
    if (!response.ok) throw new Error(`Error fetching history: ${response.status}`);
    return response.json();
},
```

---

### 🟢 BUG 8 (LOW): `loadSession` intenta resolver agente de sesión inexistente

**Archivo:** `frontend/src/store/useChatStore.ts:312-330`

Cuando `messagesBySession[sessionId]` existe pero está vacío (length 0), el código no entra al if del cache y va al servidor. Pero si tiene mensajes, intenta resolver el agentId de los mensajes sin verificar que la sesión existe en `sessions`. Esto es un edge case que se manifiesta cuando BUG 1 está activo.

---

### 🟡 BUG 9 (MEDIO): `updateSessionMetadata` no actualiza `members` en el store local

**Archivo:** `frontend/src/store/useChatStore.ts:722-737`

```typescript
updateSessionMetadata: async (sessionId: string, updates: { title?: string; visual_config?: any; members?: string[] }) => {
    const updatedSession = await chatService.updateSession(sessionId, updates);
    set((state) => ({
        sessions: state.sessions.map(s =>
            s.session_id === sessionId ? { ...s, ...updatedSession } : s
        )
    }));
},
```

El tipo de `updates` incluye `members`, pero el store solo pasa `title` y `visual_config` al backend. Si se llama con members, se envía al backend pero el store local no se actualiza correctamente (depende de `...updatedSession` que podría no tener el campo).

---

## Resumen de Severidad

| # | Bug | Severidad | Archivo | Fix |
|---|-----|-----------|---------|-----|
| 1 | `scoped_find` async sin await | 🔴 CRÍTICO | tenant.py:15 | Quitar `async` |
| 2 | VITE_API_URL no pasa en Docker | 🟡 MEDIO | Dockerfile | Agregar ARG |
| 3 | fetchSessions no propaga error | 🟡 MEDIO | useChatStore.ts:172 | Actualizar errorStates |
| 4 | sessionBaseAgent undefined | 🟡 MEDIO | useChatStore.ts:409 | Downstream de #1 |
| 5 | proxy.js disconnected port | 🟢 N/A | Browser ext | Ignorar |
| 6 | user_id hardcodeado | 🟡 MEDIO | useChatStore.ts:266 | Eliminar campo |
| 7 | getSessionHistory sin check ok | 🟡 MEDIO | api.ts:261 | Agregar check |
| 8 | loadSession edge case | 🟢 LOW | useChatStore.ts:312 | Se resuelve con #1 |
| 9 | updateSessionMetadata members | 🟡 MEDIO | useChatStore.ts:722 | Revisar tipos |

## Recomendación

**Orden de fix:**
1. BUG 1 (scoped_find) — es la raíz de todo, sin esto nada funciona
2. BUG 2 (Docker env) — necesario para que Docker funcione
3. BUG 3 + 4 + 8 — mejoras de UX y robustez del frontend
4. BUG 6, 7, 9 — limpieza y consistencia

## Ready for Proposal
Sí — el BUG 1 es trivial de fixear (cambiar `async def` → `def` en una línea) y resuelve el 500 inmediatamente.
