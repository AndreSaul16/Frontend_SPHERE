# Conexiones + herramientas n8n — guía de activación

**Fecha:** 2026-06-12

Esta guía cubre lo necesario para que las **herramientas de los agentes** (Calendar, WhatsApp, LinkedIn, Instagram, finanzas, Jules) funcionen para usuarios reales, y para que la **página de Conexiones** (`/settings/integrations` y `/settings/contacts`) opere al 100%.

El código ya está completo (registry de tools, cliente n8n, auto-deploy de workflows, inyección de credenciales cifradas, CRUD de contactos, OAuth). Lo que queda es **configuración de entorno + un instancia n8n**, que es responsabilidad de operación (no de código).

---

## 1. Qué ya funciona en el código (tras este PR)

- **Auto-deploy de workflows n8n**: en cada arranque del backend, `deploy_all_workflows()` sube y activa los 16 workflows de `backend/infrastructure/n8n-workflows/`. Ahora además **actualiza** los que cambian de contenido (antes solo creaba los que faltaban).
- **Contactos CRUD**: arreglado el bug por el que los contactos volvían sin `id` y no se podían borrar. Añadir/listar/borrar funciona en la UI.
- **Google Calendar por OAuth**: Calendar ya NO se conecta con una "api_key" (que Google rechaza) — ahora es OAuth real (`/settings/integrations` → Google Calendar). El token se auto-refresca y se inyecta en los workflows de calendario.
- **Inyección multi-tenant de credenciales**: cada llamada a n8n lleva las credenciales cifradas del usuario (`user_credentials` en el payload).

---

## 2. Variables de entorno (Railway — servicio backend)

| Variable | Para qué | Valor |
|---|---|---|
| `N8N_BASE_URL` | URL del n8n al que el backend despliega y llama webhooks | URL del servicio n8n (ej. `https://n8n-production-xxxx.up.railway.app` o `http://n8n:5678` si es servicio interno) |
| `N8N_API_KEY` | API key del n8n (para crear/activar workflows) | JWT de n8n (Settings → API en n8n). Ya tienes uno en `.env` |
| `N8N_WEBHOOK_SECRET` | Firma HMAC de los webhooks + firma del state OAuth | Secreto fuerte (genera uno y ponlo IGUAL en backend y, si añades verificación, en los workflows) |
| `FERNET_KEY` | Cifrado de credenciales de usuario | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `OAUTH_REDIRECT_BASE_URL` | Base del callback OAuth | `https://<tu-backend>.up.railway.app/api/v1/integrations` |

> ⚠️ Sin `N8N_BASE_URL` los workflows no se despliegan y las tools fallan con error claro (no crashea). Sin `FERNET_KEY` el backend no arranca (lo viste en los tests). `N8N_WEBHOOK_SECRET` vacío hace que el state OAuth y las firmas sean falsificables — ponlo en producción.

---

## 3. Instancia n8n

1. Despliega n8n (Railway tiene template, o usa tu instancia). Debe ser **alcanzable desde el backend** por `N8N_BASE_URL`.
2. Activa la API pública de n8n y copia la API key → `N8N_API_KEY`.
3. Reinicia el backend: en el log verás `📦 Deployando 18 workflows a n8n...` y `✅ Deploy de n8n completado`. El usuario nunca toca n8n.

**Variables OBLIGATORIAS en el servicio n8n (Railway):**

| Variable | Por qué |
|---|---|
| `N8N_USER_FOLDER=/home/node` | ⚠️ **Sin esto se pierde TODO en cada redeploy.** Con `RAILWAY_RUN_UID=0` n8n corre como root y guarda la DB en `/root/.n8n`, fuera del volumen (montado en `/home/node/.n8n`). Incidente real: 2026-06-12, un redeploy borró workflows + API key. |
| `NODE_FUNCTION_ALLOW_BUILTIN=crypto` | El nodo `Verify Signature` usa `require('crypto')` para la verificación HMAC. |
| `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` | n8n ≥2.x bloquea `$env` en nodos Code por defecto; el nodo de verificación lee `$env.N8N_WEBHOOK_SECRET`. |
| `N8N_WEBHOOK_SECRET` | Mismo valor que en el backend (la firma se verifica dentro de cada workflow). |

> Recomendado: **pinear la imagen** a una versión concreta (ej. `n8nio/n8n:2.25.7`) en vez de `latest` — un redeploy con `latest` puede saltar de major version sin avisar.

---

## 4. Conectar servicios (lo hace cada usuario en `/settings`)

### Google Calendar (OAuth — recomendado)
1. El usuario crea una OAuth app en Google Cloud Console → Credentials → OAuth client ID (tipo Web).
2. Habilita la **Google Calendar API** en ese proyecto.
3. Añade la Callback URL que muestra la UI (`.../api/v1/integrations/google/callback`) a los *Authorized redirect URIs*.
4. Pega `client_id` + `client_secret` en SPHERE → Conexiones → Google Calendar → "Guardar app" → "Conectar".
5. Autoriza en Google. Listo: los agentes pueden gestionar su calendario.

> Alternativa sin fricción para el usuario: registrar UNA OAuth app de Google de SPHERE y compartir su `client_id/secret` por defecto (requiere pantalla de consentimiento verificada por Google). Hoy el flujo es BYO (cada usuario su app), igual que GitHub/Notion/Slack.

### WhatsApp / LinkedIn / Instagram (api_key / token — `/settings/integrations` → credenciales)
- Estos aceptan tokens de larga duración pegables: el usuario pega el `access_token` (y `phone_number_id` para WhatsApp). Se cifran con Fernet. El botón "Test" valida contra la API real.

### Contactos (`/settings/contacts`)
- Whitelist obligatoria: los agentes solo envían a contactos que el usuario añada (anti prompt-injection). Añadir/borrar ya funciona.

---

## 5. Hardening (implementado 2026-06-12)

- **Verificación HMAC en los workflows** ✅ — cada workflow tiene un nodo `Verify Signature` tras el Webhook que recomputa la firma HMAC-SHA256 sobre la forma canónica del payload (claves ordenadas, sin espacios, UTF-8) y compara en tiempo constante con `X-Webhook-Signature`. Sin firma válida, el webhook devuelve error y la tool no se ejecuta. Requiere en el **servicio n8n**: `N8N_WEBHOOK_SECRET` (mismo valor que el backend) y `NODE_FUNCTION_ALLOW_BUILTIN=crypto`. El nodo se inserta con `backend/infrastructure/scripts/add_hmac_verification.py` (idempotente).
- **Surface de errores de tools en el chat** ✅ — el backend emite el evento SSE `tool_error` cuando una tool devuelve `{"error": true}` (el flujo `confirmation_required` NO cuenta como error); el chat muestra una card roja con el mensaje y botón **Reintentar** que pide al agente repetir la acción.
- **OAuth de Google compartido** ✅ (código) — si configuras `GOOGLE_OAUTH_CLIENT_ID` + `GOOGLE_OAUTH_CLIENT_SECRET` en el backend (Railway), los usuarios conectan Google Calendar directamente sin crear su propia app (la UI lo detecta sola). Una app BYO registrada por el usuario sigue teniendo prioridad. **Pendiente de operación:** crear la OAuth app oficial de SPHERE en Google Cloud Console (pantalla de consentimiento + verificación de Google) y poner las 2 env vars.
- **Rate limiting con Redis** ✅ — servicio Redis en Railway; `REDIS_URL` del backend apunta a `redis.railway.internal`.

## 6. Pendientes opcionales

- **Catálogo visual de integraciones con logs por servicio**: la página ya lista servicios y estado; un catálogo con historial de ejecuciones sería el siguiente nivel.
- **App OAuth de Google de SPHERE**: crearla en Google Cloud Console y configurar `GOOGLE_OAUTH_CLIENT_ID/SECRET` (ver §5).
