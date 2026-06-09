# Frontend Deploy Status — SPHERE

> 🟢 Backend: **OK** | 🔴 Frontend: **BLOQUEADO**
>
> Último intento de deploy del frontend: commit `e778dc9`
> Commits posteriores sin deployar: `9912148`, `16ccfc3`, `f9cb672`

---

## 1. Qué se tocó del frontend

### Archivos modificados

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `frontend/vite.config.ts` | Añadidos `define` globals (`__GIT_COMMIT_SHA__`, `__BUILD_TIMESTAMP__`, `__VERSION__`, `__RAILWAY_SERVICE_NAME__`) inyectados en build-time | +15 |
| `frontend/src/App.tsx` | Nueva ruta pública `/status` (StatusPage, sin auth) | +2 |
| `frontend/src/components/sidebar/Sidebar.tsx` | Añadido `<DeployStatusIndicator />` en el footer del sidebar | +2 |
| `frontend/src/services/api.ts` | Añadido `deployService.getStatus()` — fetch a `/api/v1/health/deploy` | +23 |

### Archivos nuevos

| Archivo | Qué hace | Líneas |
|---------|----------|--------|
| `frontend/src/pages/StatusPage.tsx` | Página `/status` pública. Muestra tarjetas de estado (backend + frontend) con indicadores de color: verde (OK), amarillo (deploying), rojo (failed). Incluye loading skeleton y estado de error si el backend no responde. | 179 |
| `frontend/src/store/useDeployStore.ts` | Zustand 5 store. Maneja fetch de estado de deploy con polling cada 60s, reintentos, y estado de loading/error. | 43 |
| `frontend/src/components/deploy/DeployStatusIndicator.tsx` | Indicador tipo "health dot" para el sidebar. Verde/amarillo/rojo según estado. Tooltip con commit SHA. | 55 |
| `frontend/src/vite-env.d.ts` | Declaraciones de tipo para las variables globales inyectadas por Vite `define`. | 7 |

### Archivos de tests nuevos

| Archivo | Tests | Líneas |
|---------|-------|--------|
| `frontend/tests/store/useDeployStore.test.ts` | 6 tests unitarios del store Zustand (fetch exitoso, fallo de API, estado deploying, timeout, polling, reintentos) | 101 |
| `frontend/tests/components/StatusPage.test.tsx` | 5 tests de integración (renderiza ambas tarjetas, muestra versión, maneja backend caído, indicadores de color correctos, muestra SHA) | 127 |
| `frontend/tests/components/DeployStatusIndicator.test.tsx` | 4 tests de integración (renderiza, color verde para success, color rojo para failure, tooltip con SHA) | 99 |

### Archivos NO tocados (relevantes para el build)

- `frontend/tsconfig.json` — sin cambios
- `frontend/tsconfig.app.json` — sin cambios
- `frontend/tsconfig.node.json` — sin cambios
- `frontend/package.json` — sin cambios en dependencias
- `frontend/package-lock.json` — restaurado al estado previo (HEAD)
- `frontend/Dockerfile` — **eliminado** en commit `f9cb672` (debug)
- `frontend/railway.toml` — restaurado al estado previo (HEAD)

---

## 2. Estado actual de los deploys

### Railway — últimos deploys

| Servicio | Commit | Estado | Detalle |
|----------|--------|--------|---------|
| **Backend_SHPERE** | `f9cb672` | ✅ SUCCESS | Deployó correctamente. Endpoint `/api/v1/health/deploy` funcionando. |
| **Frontend_SPHERE** | `e778dc9` | ❌ FAILED | `tsc -b` falla con `tsconfig.json(1,40): TS1127 Invalid character`. Railway NO está auto-deployando los commits posteriores. |

### Commits en Frontend_SPHERE/main (GitHub) que Railway NO ha deployado

| Commit | Mensaje | Cambios relevantes al frontend |
|--------|---------|-------------------------------|
| `9912148` | fix(deploy): remover GitHub Actions workflows | Ninguno (solo delete de `.github/workflows/`) |
| `16ccfc3` | debug(frontend): agregar pasos de diagnóstico al Dockerfile | Debug steps en Dockerfile |
| `f9cb672` | fix(frontend): eliminar Dockerfile para que RAILPACK construya sin Docker | **Dockerfile eliminado** |

---

## 3. El error: `tsconfig.json(1,40): TS1127 Invalid character`

### Síntoma exacto

```
tsconfig.json(1,40): error TS1127: Invalid character.
tsconfig.json(1,41): error TS1127: Invalid character.
...
tsconfig.json(1,119): error TS1127: Invalid character.
tsconfig.json(1,120): error TS1005: '}' expected.
```

- Columnas 40 a 119 de la línea 1: TypeScript reporta "Invalid character"
- Columna 120: TypeScript espera `}`

### Lo que se verificó

| Verificación | Resultado |
|-------------|-----------|
| `tsc -b` local | ✅ Pasa sin errores |
| `npm run build` local (limpio, `npm ci` + `tsc -b && vite build`) | ✅ Build completo exitoso |
| `tsconfig.json` en git blob | ✅ JSON limpio, sin BOM, sin caracteres no-ASCII |
| `tsconfig.json` en GitHub (raw) | ✅ Idéntico al local |
| `tsconfig.app.json` | ✅ Sin cambios, válido |
| `tsconfig.node.json` | ✅ Sin cambios, válido |
| Archivos nuevos (StatusPage, store, vite-env.d.ts) | ✅ Solo ASCII/UTF-8 válido |
| `vite.config.ts` modificado | ✅ `tsc -b` lo compila sin errores |

### Posibles causas (no confirmadas)

1. Railway cacheó una capa rota del Docker build (`node:20-alpine`) y la reusa en builds posteriores
2. El builder RAILPACK está generando un `tsconfig.json` mergeado/distinto al nuestro
3. Railway no está respetando `rootDirectory: 'frontend'` y está leyendo archivos de la raíz del monorepo
4. Diferencia de versión de TypeScript en `node:20-alpine` vs local (aunque el lockfile debería fijar la versión)

### Por qué no se puede reproducir localmente

- Sin Docker disponible en el entorno local
- `npm run build` y `tsc -b` pasan limpiamente en el mismo setup que el Dockerfile replica

---

## 4. Bloqueantes

### 🔴 Bloqueante #1: Railway no auto-deploya nuevos commits del frontend

**Causa**: El último deploy del frontend está en estado `FAILED`. Railway parece no estar procesando los commits posteriores.

**Acción requerida**: Forzar un redeploy manual desde el dashboard de Railway para el servicio `Frontend_SPHERE`.

**Commits pendientes de deploy**: `9912148`, `16ccfc3`, `f9cb672` (el último ya sin Dockerfile).

### 🔴 Bloqueante #2: Error `tsconfig.json(1,40)` no diagnosticado

**Causa**: Imposible de reproducir localmente. El build pasa limpio en el mismo entorno.

**Plan de ataque cuando Railway retome el deploy**:
- Commit `f9cb672` eliminó el Dockerfile → RAILPACK debería construir sin Docker
- Si sigue fallando: restaurar Dockerfile con `node:22-alpine` en vez de `node:20-alpine`
- Si sigue fallando: migrar a `rootDirectory: None` como brave-art (usa `package.json` raíz → `cd frontend && npm ci && npm run build`)

### 🟡 Bloqueante #3: GitHub Actions workflows removidos

Los workflows de CI y deploy-monitor se removieron porque Railway los esperaba como checks y causaban SKIPPED. Hay que reincorporarlos después de configurar Railway para no esperar checks de CI.

---

## 5. Plan de acción recomendado

1. **Ahora**: Entrar al dashboard de Railway → `Frontend_SPHERE` → forzar redeploy manual del último commit (`f9cb672`)
2. **Si falla con el mismo error**: El problema NO es del Dockerfile → es de RAILPACK o del entorno de build
3. **Si falla con error diferente**: Comparar con el error actual para aislar la causa
4. **Si deploya OK**: Restaurar el Dockerfile, verificar endpoint `/api/v1/health/deploy` en backend, verificar página `/status` en frontend
5. **Después**: Reincorporar GitHub Actions con Railway configurado para no esperar checks

---

## 6. Resumen de cambios por commit

```
f9cb672 fix(frontend): eliminar Dockerfile para que RAILPACK construya sin Docker
16ccfc3 debug(frontend): agregar pasos de diagnóstico al Dockerfile para tsconfig
9912148 fix(deploy): remover GitHub Actions workflows temporalmente
e778dc9 feat(deploy): GitHub como fuente de verdad del deploy status ← ESTE ES EL QUE FALLÓ
df6953b fix: modelo single-plan (30 créditos/mes, RAG 20MB) + tests ← ÚLTIMO DEPLOY OK
```
