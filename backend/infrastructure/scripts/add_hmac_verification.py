"""Inserta un nodo 'Verify Signature' (HMAC-SHA256) tras el Webhook en cada
workflow JSON de n8n-workflows/. Idempotente: si el nodo ya existe, lo salta.

La firma la envía el backend en X-Webhook-Signature sobre la serialización
canónica del payload (claves ordenadas, sin espacios, UTF-8). El nodo recomputa
esa forma canónica desde el body parseado y compara en tiempo constante.

Requiere en el servicio n8n: NODE_FUNCTION_ALLOW_BUILTIN=crypto (para require)
y N8N_WEBHOOK_SECRET (mismo valor que el backend).
"""
import json
import sys
from pathlib import Path

WORKFLOWS_DIR = Path(__file__).parents[1] / "n8n-workflows"

VERIFY_JS = """const crypto = require('crypto');
const input = $input.first().json;
const received = String((input.headers || {})['x-webhook-signature'] || '');
const secret = $env.N8N_WEBHOOK_SECRET || '';
if (!secret) throw new Error('N8N_WEBHOOK_SECRET no configurado en n8n');

// Forma canonica identica a la del backend:
// json.dumps(payload, separators=(',', ':'), sort_keys=True, ensure_ascii=False)
function canon(v) {
  if (v === null || typeof v !== 'object') return JSON.stringify(v);
  if (Array.isArray(v)) return '[' + v.map(canon).join(',') + ']';
  return '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + canon(v[k])).join(',') + '}';
}

const expected = crypto.createHmac('sha256', secret)
  .update(Buffer.from(canon(input.body || {}), 'utf8'))
  .digest('hex');
const a = Buffer.from(received, 'utf8');
const b = Buffer.from(expected, 'utf8');
if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) {
  throw new Error('Firma de webhook invalida');
}
return $input.all();"""


def add_verification(path: Path) -> str:
    wf = json.loads(path.read_text(encoding="utf-8"))
    if any(n.get("name") == "Verify Signature" for n in wf["nodes"]):
        return "ya tenia verificacion"

    webhook = next(
        n for n in wf["nodes"] if n.get("type") == "n8n-nodes-base.webhook"
    )
    webhook_name = webhook["name"]
    wx, wy = webhook.get("position", [250, 300])

    verify_node = {
        "parameters": {"jsCode": VERIFY_JS},
        "id": "verify-hmac-1",
        "name": "Verify Signature",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [wx + 100, wy - 160],
    }

    # Insertar justo despues del webhook en el array de nodos
    idx = wf["nodes"].index(webhook)
    wf["nodes"].insert(idx + 1, verify_node)

    # Recablear: Webhook -> Verify Signature -> (lo que apuntaba el Webhook)
    old_next = wf["connections"].get(webhook_name)
    if not old_next:
        raise ValueError(f"{path.name}: el webhook no tiene conexiones salientes")
    wf["connections"][webhook_name] = {
        "main": [[{"node": "Verify Signature", "type": "main", "index": 0}]]
    }
    wf["connections"]["Verify Signature"] = old_next

    path.write_text(
        json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return "verificacion anadida"


if __name__ == "__main__":
    files = sorted(WORKFLOWS_DIR.glob("*.json"))
    if not files:
        sys.exit(f"No hay workflows en {WORKFLOWS_DIR}")
    for f in files:
        print(f"{f.name}: {add_verification(f)}")
