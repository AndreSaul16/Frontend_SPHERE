# Proposal: fix-platform-stability

**Status**: draft
**Created**: 2026-05-14
**Author**: Saul (via Gentle AI orchestrator)

---

## Executive Summary

SPHERE tiene 5 issues que bloquean la experiencia del usuario real: el sistema de créditos no funciona en producción (nadie puede usar el producto), el balance se muestra en 0 aunque haya créditos, los botones de Stripe no tienen keys configuradas, el scroll en Configuración está roto en mobile, y n8n no está desplegado. Este cambio los aborda todos en UN ciclo SDD.

---

## Problem Statements

### P1: CRÍTICO — Credit System Not Working

**Severity**: BLOCKER — nadie puede usar el producto sin créditos.

**Root cause analysis**:

1. `_ensure_wallet()` (backend/app/core/auth.py:105-134) tiene un guard temprano en línea 108:
   ```python
   if "wallet" in user_doc:
       return user_doc
   ```
   Si el documento MongoDB tiene `wallet: {}` (objeto vacío) o `wallet: null`, la key existe en el dict, por lo que `_ensure_wallet` retorna sin inicializar. El usuario queda sin créditos.

2. El credit check en stream.py:374-378 hace:
   ```python
   wallet = user.get("wallet") or {}
   total_balance = wallet.get("pro_messages_balance", 0) + wallet.get("topup_messages_balance", 0)
   if total_balance <= 0: raise 402
   ```
   Si el wallet es `{}`, `total_balance = 0`, y el usuario recibe 402. **Esto es correcto como safety net**, pero expone el bug de inicialización.

3. La transacción de crédito (`credit_transactions`) nunca se crea porque el `CreditManager.areserve_and_charge` (stream.py:396) solo se ejecuta si `total_balance > 0`. Como nunca hay balance, nunca hay transacciones.

**Files involved**: `backend/app/core/auth.py`, `backend/app/presentation/api/v1/stream.py`, `backend/app/application/credit_manager.py`

### P2: Balance Shows 0 in Frontend

**Severity**: HIGH — el usuario no sabe cuántos créditos tiene.

**Root cause analysis**:

1. `useBillingStore` (frontend/src/store/useBillingStore.ts) tiene `refresh()` que consulta `GET /api/v1/billing/me`. El store inicializa con `pro_messages_balance: 0, topup_messages_balance: 0, loaded: false`.

2. `BillingPage.tsx` llama `refresh()` en `useEffect` al montar, pero **no hay polling ni suscripción a eventos**. Si el endpoint `/billing/me` falla (401, error de red), el store queda en 0 permanentemente.

3. Posible race condition: el componente se monta antes de que Firebase auth esté listo, `authHeaders()` lanza error, `refresh()` falla silenciosamente (`console.warn` en línea 63), y el store nunca se actualiza.

4. No hay refresh automático después de que el stream consume créditos. El `decrementOptimistic` existe pero no se llama desde ningún lado visible.

**Files involved**: `frontend/src/store/useBillingStore.ts`, `frontend/src/pages/BillingPage.tsx`

### P3: Stripe Keys Not Configured

**Severity**: HIGH — los botones de pago no funcionan.

**Root cause analysis**:

1. Los botones "Suscribirse" en `BillingPage.tsx` llaman a `handleCheckout(planId)`, que hace POST a `/api/v1/billing/checkout`.

2. El backend necesita `STRIPE_SECRET_KEY` para crear Checkout Sessions. Si la variable está vacía (`""`) en Railway, Stripe lanza error y el endpoint devuelve 5xx.

3. El frontend no muestra feedback al usuario cuando el checkout falla — solo `console.error` (línea 65).

4. No hay verificación server-side de que Stripe esté configurado al iniciar la app.

**Files involved**: `frontend/src/pages/BillingPage.tsx`, `backend/app/presentation/api/v1/billing.py` (endpoint checkout), Railway environment config.

### P4: Settings Page Scroll Issue

**Severity**: MEDIUM — UX rota en mobile.

**Root cause analysis**:

1. `SettingsPage.tsx:50` tiene `overflow-hidden` en el contenedor raíz.

2. `SettingsPage.tsx:87` — el tab bar mobile usa `absolute top-14 left-0 right-0`, fuera del flujo normal.

3. El `<main>` (línea 108) intenta compensar con `pt-14 sm:pt-6` y `overflow-y-auto`, pero el `overflow-hidden` del padre (línea 50) **mata el scroll** — el contenido que excede la altura se recorta en lugar de scrollear.

4. El `overflow-hidden` del padre probablemente está ahí para los decorative blobs/effects de fondo, pero rompe la funcionalidad.

**Files involved**: `frontend/src/pages/SettingsPage.tsx`

### P5: n8n Service Not Deployed

**Severity**: LOW — funcionalidad no disponible.

**Root cause analysis**:

1. n8n es un servicio de automatización de workflows que debe correr como contenedor separado.

2. No está configurado en Railway (no hay service definition).

3. Posiblemente requiere variables de entorno adicionales (n8n credentials, webhook URL, etc.).

**Files involved**: `railway.toml` o `railway.json` (si existe), documentación de despliegue.

---

## Proposed Solutions

### S1: Fix Credit System Initialization

**Approach**: Hardening defensivo de `_ensure_wallet` + verificación en health endpoint.

1. **Fix `_ensure_wallet` guard**: Cambiar `if "wallet" in user_doc` por `if user_doc.get("wallet") and isinstance(user_doc["wallet"], dict) and "pro_messages_balance" in user_doc["wallet"]`. Solo skip si el wallet YA está correctamente inicializado.

2. **Agregar logging de diagnóstico**: Loggear WARNING cuando se detecta un wallet en estado inválido (`{}`, sin `pro_messages_balance`).

3. **Repair script o migración**: Agregar un endpoint admin o un script que repare wallets inválidos para usuarios existentes.

4. **Test**: Agregar test unitario para `_ensure_wallet` con wallet `{}`, wallet `null`, wallet sin `pro_messages_balance`.

### S2: Fix Frontend Balance Display

**Approach**: Robustecer el flujo de refresh + optimistic updates.

1. **Retry con backoff**: Si `refresh()` falla, reintentar con exponential backoff (1s, 2s, 4s) antes de rendirse.

2. **Esperar auth**: Antes de llamar `refresh()`, esperar a que Firebase auth esté listo (`onAuthStateChanged`).

3. **Llamar `decrementOptimistic` desde el stream**: Después de cada mensaje en el chat, decrementar el balance optimísticamente y refrescar en background.

4. **Skeleton/loading state**: Mostrar "Cargando..." en lugar de 0 mientras `loaded === false`.

### S3: Stripe Configuration & Graceful Degradation

**Approach**: Validación temprana + UX graceful.

1. **Startup check**: Al iniciar FastAPI, validar que `STRIPE_SECRET_KEY` no esté vacío. Si lo está, loggear CRITICAL y deshabilitar endpoints de Stripe.

2. **Frontend graceful**: Si el endpoint `/billing/me` devuelve `stripe_configured: false`, ocultar botones de pago y mostrar mensaje "Pagos no disponibles".

3. **Railway env vars**: Documentar/Asegurar que `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` estén configuradas en Railway.

4. **Feedback al usuario**: Mostrar toast/alert cuando el checkout falla, en lugar de solo `console.error`.

### S4: Fix Settings Scroll

**Approach**: Ajuste CSS mínimo — cambiar `overflow-hidden` por `overflow-y-auto` donde corresponda.

1. **Cambiar el `overflow-hidden` del contenedor raíz** (línea 50) por `overflow-y-auto` o removerlo.

2. **Verificar que los blobs decorativos** (si los hay) sigan funcionando con `pointer-events-none`.

3. **El main content** ya tiene `overflow-y-auto` y `pt-14`, lo cual es correcto una vez que el padre permite scroll.

### S5: n8n Deployment

**Approach**: Documentación y configuración de Railway.

1. **Crear `railway.json`** o actualizar configuración existente con el servicio n8n.

2. **Docker image**: Usar `n8nio/n8n:latest`.

3. **Variables de entorno necesarias**: `N8N_HOST`, `N8N_PORT`, `N8N_PROTOCOL`, `WEBHOOK_URL`, database config.

4. **Exponer en subdominio** (ej: `n8n.sphere.app`) o path.

---

## Scope & Boundaries

**In scope**:
- Fix `_ensure_wallet` para manejar wallets vacíos/inválidos
- Robustecer `useBillingStore.refresh()` con retry + auth-aware loading
- Startup validation de Stripe keys
- Fix CSS de scroll en SettingsPage
- Railway config para n8n + documentación

**Out of scope**:
- Rewrite del sistema de créditos completo
- Migración de base de datos masiva
- Cambios en el modelo de precios
- Rediseño de SettingsPage

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| `_ensure_wallet` fix podría duplicar créditos | Validar `pro_messages_balance` existente antes de inicializar |
| Race condition en refresh del store | Usar Zustand `set` atómico + loading flags |
| Railway deploy de n8n requiere DB separada | Usar SQLite local como default, PostgreSQL opcional |
| Cambios de CSS en Settings podrían romper otros layouts | Test visual en mobile + desktop antes de mergear |

---

## Impact Assessment

- **Usuarios afectados**: Todos los usuarios nuevos (no pueden usar el producto sin créditos)
- **Usuarios existentes**: Aquellos con wallet `{}` — necesitan reparación
- **Rollback risk**: Bajo. Los cambios son incrementales y acotados.
- **Estimated effort**: 3-5 horas de desarrollo distribuido en 5 issues independientes

---

## Success Criteria

1. Usuario nuevo se registra → wallet inicializado con 5 créditos → puede enviar mensajes
2. Balance se muestra correctamente en BillingPage después del login
3. Botones de Stripe muestran estado graceful cuando keys no están configuradas
4. SettingsPage scrollea correctamente en mobile (iOS Safari + Android Chrome)
5. n8n desplegado y accesible en Railway
