# SPHERE n8n Workflows

Workflows pre-configurados para n8n. Solo importar y listo.

## Cómo importar

1. Abrí n8n (http://localhost:5678)
2. Andá a **Workflows** → **Import from File**
3. Importá cada archivo JSON
4. Activá el workflow (toggle en la esquina superior derecha)

## Workflows incluidos

| Archivo | Servicio | Webhook Path |
|---------|----------|--------------|
| `google-calendar-list.json` | Google Calendar | `shared/calendar-list` |
| `google-calendar-create.json` | Google Calendar | `shared/calendar-create` |
| `whatsapp-send.json` | WhatsApp | `shared/whatsapp-send` |
| `linkedin-post.json` | LinkedIn | `cmo/linkedin-post` |
| `jules-create.json` | Jules | `cto/jules-create` |

## Cómo funciona

```
SPHERE envía payload con credenciales
  → n8n recibe webhook
  → Extrae credenciales del payload
  → Usa credenciales para llamar a la API del servicio
  → Devuelve resultado a SPHERE
```

## Configuración en SPHERE

Una vez importados los workflows:

1. Andá a **Settings** → **API Keys** en SPHERE
2. Configurá tu API key para cada servicio
3. Probá la conexión con el botón "Test"
4. ¡Listo! Los agentes ya pueden usar los servicios

## Ejemplo de payload

```json
{
  "date_from": "2026-03-20",
  "date_to": "2026-03-21",
  "max_results": 10,
  "user_credentials": {
    "google_calendar": {
      "api_key": "AIzaSy...",
      "calendar_id": "primary"
    }
  }
}
```

## Notas

- Los workflows están configurados para usar credenciales dinámicas
- No necesitás configurar credenciales en n8n (vienen en el payload)
- Cada usuario tiene sus propias credenciales en SPHERE
- n8n es un "executor tonto" - solo ejecuta lo que le piden

## Troubleshooting

**Error 401 en n8n:**
- Verificá que el webhook esté activo
- Verificá que el path coincida exactamente

**Error en la API externa:**
- Verificá que la API key sea válida
- Usá el botón "Test" en SPHERE para diagnosticar

**n8n no recibe el webhook:**
- Verificá que n8n esté corriendo
- Verificá la URL en `config.py` (`N8N_BASE_URL`)
