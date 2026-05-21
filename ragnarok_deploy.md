# 🚀 Ragnarök Deploy — Changelog & Guía de Despliegue

> **Fecha:** 2026-05-20  
> **Autor:** Auditoría automatizada pre-producción  
> **Archivos tocados:** 12 | **Líneas:** +155 / -59

---

## 📝 CHANGELOG COMPLETO — Qué se tocó y por qué

### 1. `backend/app/presentation/api/v1/stream.py`
**Tipo:** 🔴 Fix Crítico (CRIT-01 + CRIT-03)

**Problema original:** El `DistributedLock` que previene mensajes concurrentes al mismo chat se liberaba en el bloque `finally` del endpoint HTTP. Pero `StreamingResponse` de FastAPI retorna control inmediatamente — el generador corre en background. Resultado: el lock se liberaba en el milisegundo 1, permitiendo enviar múltiples mensajes paralelos y corrompiendo el grafo de LangGraph.

Además, cuando un usuario cerraba la pestaña durante el streaming, el `GeneratorExit` no reembolsaba el crédito cobrado.

**Cambios realizados:**
- Se añadió el parámetro `lock: Optional[DistributedLock]` al generador `generate_chat_events()`
- El lock ahora se pasa desde el endpoint al generador
- `lock.release()` se ejecuta en el `finally` del **generador** (no del endpoint)
- Si hay error antes de crear el `StreamingResponse`, el lock se libera con un `except` explícito
- `GeneratorExit` ahora ejecuta `credit_manager.arefund()` para devolver créditos en desconexión

```diff
- async def generate_chat_events(query, session_id, user_id, ...):
+ async def generate_chat_events(query, session_id, user_id, ..., lock=None):

  except GeneratorExit:
+     if already_charged and charge_ctx and credit_manager:
+         await credit_manager.arefund(charge_ctx, reason="client_disconnected")
      return

+ finally:
+     if lock:
+         await lock.release()

- # En el endpoint:
-     finally:
-         await lock.release()  # ← SE EJECUTABA INMEDIATAMENTE
+ # En el endpoint:
+     return StreamingResponse(generate_chat_events(..., lock=lock))
+     except Exception as inner_e:
+         await lock.release()  # Solo si falla ANTES del stream
+         raise inner_e
```

---

### 2. `backend/app/core/auth.py`
**Tipo:** 🔴 Fix Crítico (CRIT-02)

**Problema original:** Si un usuario se registraba con el mismo email pero diferente `firebase_uid` (ej: primero con Google, luego con Email/Password), MongoDB lanzaba `DuplicateKeyError`. El catch asumía que el usuario ya existía bajo el nuevo UID y ejecutaba `update_one({"firebase_uid": nuevo_uid})`, que no matcheaba nada. El usuario quedaba como "fantasma" — navegaba en memoria pero nunca se persistía.

**Cambios realizados:**
- Cuando hay `DuplicateKeyError` por email, ahora se busca al usuario **existente** por email
- Si se encuentra, se retorna ese usuario (con su UID original) en lugar de crear uno fantasma
- Se añade logging de warning para detectar estos casos
- El caso edge de `email=""` duplicado mantiene su lógica original

```diff
  except Exception as e:
      if "duplicate key" in str(e).lower():
+         if email:
+             existing = await users_col.find_one({"email": email})
+             if existing:
+                 logger.warning(f"Email '{email}' ya registrado bajo UID {existing['firebase_uid']}")
+                 await users_col.update_one({"_id": existing["_id"]}, {"$set": {"last_login_at": now}})
+                 existing = await _ensure_wallet(existing["firebase_uid"], existing)
+                 return existing
-         logger.debug(f"Usuario ya existe (email duplicado), actualizando login: {uid}")
+         logger.debug(f"DuplicateKey sin email, actualizando login: {uid}")
```

---

### 3. `backend/infrastructure/etl/core/base_spider.py`
**Tipo:** 🔴 Fix Crítico (CRIT-04)

**Problema original:** `tlsAllowInvalidCertificates=True` y `verify=False` en todas las conexiones del ETL Spider. Vulnerabilidad MITM en producción.

**Cambios realizados:**
- `MongoClient`: `tlsAllowInvalidCertificates=True` → `tlsCAFile=certifi.where()`, `tlsAllowInvalidCertificates=False`
- `requests.get()`: `verify=False` → `verify=certifi.where()` (2 ocurrencias)
- Eliminados comentarios de "solución temporal"

---

### 4. `backend/app/presentation/api/v1/webhooks.py`
**Tipo:** 🟠 Fix Alto (HIGH-04)

**Problema original:** Si `stripe.Subscription.retrieve()` fallaba durante `invoice.payment_succeeded`, el error se silenciaba con `except: pass`. `period_end` quedaba como `None`.

**Cambio:** `pass` → `logger.error()` detallado con el ID de suscripción y el error.

---

### 5. `backend/app/presentation/api/v1/agents.py`
**Tipo:** 🟠 Fix Alto (HIGH-05)

**Problema original:** Al eliminar un agente, si la limpieza de archivos GridFS fallaba, se silenciaba con `except: pass`. Archivos huérfanos sin registro.

**Cambio:** `pass` → `logger.error()` con el agent_id y el error.

---

### 6. `backend/app/infrastructure/integrations/providers/notion.py`
**Tipo:** 🟡 Fix Medio (MED-03)

**Problema original:** `revoke(token)` era solo `pass`. Notion no tiene endpoint de revocación, pero no se registraba el evento.

**Cambio:** Docstring explicativo + `logger.info()` indicando que el usuario debe revocar manualmente desde Notion.

---

### 7. `backend/app/infrastructure/database.py`
**Tipo:** 🟡 Fix Medio (MED-06)

**Problema original:** 3 líneas de `property()` a nivel de módulo (no dentro de una clase) que no hacían nada.

**Cambio:** Eliminadas las 3 líneas de código muerto.

---

### 8. `frontend/src/pages/ProfilePage.tsx`
**Tipo:** 🟠 Fix Alto (HIGH-01)

**Problema original:** El nombre "Saúl" y el email "admin@sphere.ai" estaban hardcodeados. Cualquier usuario veía esos datos.

**Cambios realizados:**
- Imports: `useRef` → `useRef, useState, useEffect` + `profileService`
- `useEffect` que carga el perfil real vía `profileService.getProfile()`
- Fallback a Firebase Auth si la API falla
- `<h2>Saúl</h2>` → `<h2>{displayName}</h2>`
- `defaultValue="Saúl"` → `defaultValue={displayName}`
- `defaultValue="admin@sphere.ai"` → `defaultValue={userEmail}` con `readOnly`

---

### 9. `frontend/src/pages/AgentDetailPage.tsx`
**Tipo:** 🟠 Fix Alto (HIGH-02 + HIGH-06 + LOW-05)

**Problema original:** 
- Las peticiones fetch (GET, PATCH, DELETE) no enviaban token de autenticación → 401 en producción
- Solo 2 modelos en el frontend vs 4 en el backend
- Tildes faltantes en textos en español

**Cambios realizados:**
- Las 3 peticiones (`fetchAgent`, `handleSave`, `handleDelete`) ahora obtienen el token de Firebase y lo envían como `Authorization: Bearer`
- `ALLOWED_MODELS`: `["deepseek-chat", "deepseek-r1"]` → `["deepseek-chat", "deepseek-r1", "gpt-4o", "gpt-4o-mini"]`
- Descripciones de modelo actualizadas para los 4 modelos
- "Descripcion" → "Descripción", "accion" → "acción", "configuracion" → "configuración", etc.

---

### 10. `frontend/src/pages/BillingPage.tsx`
**Tipo:** 🟡 Fix Medio (MED-08)

**Cambio:** Simplificado `authHeaders()` (era duplicado de `api.ts`).

---

### 11. `frontend/src/services/api.ts`
**Tipo:** 🟢 Fix Bajo (LOW-01/02/03)

**Problema original:** `getCustomAgents()`, `createCustomAgent()`, `deleteCustomAgent()` no verificaban `response.ok`. Errores HTTP se parseaban como datos válidos.

**Cambio:** Las 3 funciones ahora verifican `response.ok` y lanzan `Error` con el status/detail.

---

### 12. `frontend/src/store/useChatStore.ts`
**Tipo:** 🟡 Fix Medio (MED-01 + MED-02)

**Cambios realizados:**
- 7 `console.log()` de debug envueltos en `if (import.meta.env.DEV)`
- 10 líneas de comentarios del desarrollador expresando dudas ("Let's assume...", "I should update...") reemplazadas por 2 líneas descriptivas

---

## 🚀 PASOS PARA DESPLEGAR EN RAILWAY

### Pre-requisitos
- Cuenta Railway con plan Developer o superior
- Repos conectados: `AndreSaul16/Backend_SHPERE` y `AndreSaul16/Frontend_SPHERE`
- MongoDB Atlas configurado
- Redis (Railway addon o externo)
- Firebase project con Auth habilitado
- Stripe account (test o live)

### Paso 1: Commit y Push

```bash
cd c:\Users\Saul\Documents\PROGRAMACION\SPHERE

git add -A

git commit -m "fix(ragnarok): critical production fixes — lock, ghost users, credits, SSL, auth, UI

CRIT-01: Move distributed lock into generator (prevents chat corruption)
CRIT-02: Fix ghost users on email collision
CRIT-03: Refund credits on client disconnect
CRIT-04: Replace SSL bypass with certifi
HIGH-01: Dynamic user data in ProfilePage
HIGH-02: Auth headers in AgentDetailPage
HIGH-04/05: Log webhook and GridFS failures
HIGH-06: Sync 4 models frontend↔backend
MED: Clean logs, dead code, Notion revoke
LOW: API response validation, Spanish accents"

# Push a los dos remotes
git push backend main
git push frontend main
```

> **Nota:** Si Railway tiene auto-deploy habilitado en los repos, el push disparará builds automáticamente.

### Paso 2: Verificar Servicios en Railway Dashboard

Deberías tener **3 servicios** en tu proyecto Railway:

| Servicio | Dockerfile | Puerto | Health Check |
|----------|-----------|--------|-------------|
| **Backend** | `backend/Dockerfile` | `$PORT` (8000) | `/health` |
| **Frontend** | `frontend/Dockerfile` | `$PORT` (3000) | `/` |
| **n8n** | `Dockerfile.n8n` | 5678 | `/healthz` |

### Paso 3: Variables de Entorno — Backend

En Railway Dashboard → Backend service → Variables:

| Variable | Valor | Notas |
|----------|-------|-------|
| `MONGODB_URL` | `mongodb+srv://user:pass@cluster.mongodb.net/sphere_db?retryWrites=true&w=majority` | Tu connection string de Atlas |
| `DB_NAME` | `sphere_db` | |
| `OPENAI_API_KEY` | `sk-...` | Clave de OpenAI/DeepSeek |
| `FERNET_KEY` | *(generar)* | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `REDIS_URL` | `redis://...` | Railway Redis addon o externo |
| `FIREBASE_CREDENTIALS_JSON` | `{"type":"service_account",...}` | Contenido completo del JSON de Firebase Admin SDK |
| `STRIPE_SECRET_KEY` | `sk_live_...` o `sk_test_...` | |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | Se obtiene al crear el webhook en Stripe Dashboard |
| `STRIPE_PRICE_MAP` | `{"starter":"price_xxx","premium":"price_yyy","topup_starter_1k":"price_zzz",...}` | IDs de precios de Stripe |
| `N8N_BASE_URL` | `https://tu-n8n.up.railway.app` | URL interna de Railway o pública |
| `N8N_API_KEY` | *(desde n8n Settings)* | Se configura después de que n8n arranque |
| `CORS_ORIGINS` | `https://tu-frontend.up.railway.app` | Separar con comas si hay múltiples |
| `WEB_CONCURRENCY` | `2` | Workers de Uvicorn (ajustar según RAM) |

### Paso 4: Variables de Entorno — Frontend

| Variable | Valor | Notas |
|----------|-------|-------|
| `VITE_API_URL` | `https://tu-backend.up.railway.app/api/v1` | **Build arg**, se hornea en el build |

> ⚠️ **IMPORTANTE:** `VITE_API_URL` es un build-time arg. Si lo cambias, debes re-deployar (rebuild) el frontend.

### Paso 5: Variables de Entorno — n8n

| Variable | Valor |
|----------|-------|
| `N8N_HOST` | `tu-n8n.up.railway.app` |
| `N8N_PORT` | `5678` |
| `N8N_PROTOCOL` | `https` |
| `WEBHOOK_URL` | `https://tu-n8n.up.railway.app` |
| `DB_TYPE` | `sqlite` |

### Paso 6: Configurar Stripe Webhooks

1. Ir a [Stripe Dashboard → Developers → Webhooks](https://dashboard.stripe.com/webhooks)
2. Añadir endpoint: `https://tu-backend.up.railway.app/api/v1/webhooks/stripe`
3. Seleccionar eventos:
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Copiar el **Signing Secret** (`whsec_...`) y ponerlo en `STRIPE_WEBHOOK_SECRET`

### Paso 7: Verificación Post-Deploy

```bash
# 1. Health check del backend
curl https://tu-backend.up.railway.app/health

# 2. Verificar que la API responde
curl https://tu-backend.up.railway.app/api/v1/billing/me \
  -H "Authorization: Bearer <tu-token-firebase>"

# 3. Verificar n8n
curl https://tu-n8n.up.railway.app/healthz
```

### Paso 8: Tests E2E Manuales

- [ ] **Auth Flow:** Login con Google → verificar nombre correcto en ProfilePage
- [ ] **Auth Flow:** Login con Email/Password → verificar mismo resultado
- [ ] **Chat:** Crear sesión → enviar mensaje → verificar respuesta streameada
- [ ] **Lock:** Enviar 2 mensajes rápido → verificar que el 2do recibe 409
- [ ] **Credits:** Cerrar pestaña durante stream → verificar en logs que se reembolsa
- [ ] **Agents:** Crear agente custom → editarlo → eliminarlo
- [ ] **Agents:** Verificar que GPT-4o aparece en el selector de modelos
- [ ] **RAG:** Subir archivo → verificar indexación → preguntar sobre el contenido
- [ ] **Billing:** Ir a facturación → ver plan actual → hacer checkout de prueba
- [ ] **n8n:** Verificar que los workflows se desplegaron en startup (ver logs del backend)

---

## ⚠️ PENDIENTES NO BLOQUEANTES

Estos items no impiden el despliegue pero deberían resolverse en sprints futuros:

1. **HIGH-03: MOCK_AGENTS** — Los agentes core están hardcodeados en el frontend. Crear endpoint `/api/v1/agents/core` y consumirlo dinámicamente.
2. **MED-04: n8n content diff** — El deployer no compara contenido de workflows. Si cambias un JSON en `n8n-workflows/`, debes borrar el workflow en n8n manualmente.
3. **MED-07: Rate Limiter** — La mezcla de `pyrate_limiter` + `fastapi_limiter` puede ser inestable. Considerar unificar.
4. **LOW-04: Test Jules** — `test_service_credential("jules")` siempre retorna `success: True`.
