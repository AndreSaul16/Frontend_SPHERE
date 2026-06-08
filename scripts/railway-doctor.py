#!/usr/bin/env python3
"""
railway-doctor — diagnóstico de despliegue de SPHERE en Railway.

Responde de un vistazo a la pregunta "¿qué impide que el deploy salga?".
Para cada servicio del proyecto imprime:
  - su configuración de build (rootDirectory, railwayConfigFile, builder),
  - el estado del último deploy,
  - y si está BLOQUEADO, EL MOTIVO EXACTO:
        * SKIPPED  -> skippedReason (p.ej. "CI check suite failed")
        * FAILED   -> últimas líneas de los build logs (el error real)
        * CRASHED  -> aviso para revisar logs de runtime

Sin dependencias externas: solo stdlib (urllib, json). Funciona en
PowerShell, cmd y bash.

Uso:
    python scripts/railway-doctor.py                 # todos los servicios
    python scripts/railway-doctor.py Backend_SHPERE  # filtra por nombre
    python scripts/railway-doctor.py --logs 60       # más líneas de log

Token (en este orden):
    1) env RAILWAY_API_TOKEN
    2) env RAILWAY_TOKEN_SECRET
    3) la primera línea RAILWAY_TOKEN_SECRET=... del .env de la raíz

Project id: env RAILWAY_PROJECT_ID, o el valor por defecto de SPHERE.

Exit code 0 si todos los servicios tienen su último deploy en SUCCESS;
1 si alguno está bloqueado (útil para CI/automatización).
"""
import json
import os
import sys
import urllib.request
import urllib.error

API = "https://backboard.railway.app/graphql/v2"
DEFAULT_PROJECT_ID = "444961a0-0355-4809-813f-b50ba32ec7f9"  # SPHERE

OK_STATUSES = {"SUCCESS"}
BLOCKED_STATUSES = {"FAILED", "CRASHED", "SKIPPED", "REMOVED"}


def _repo_root() -> str:
    # scripts/ -> raíz del repo
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_token() -> str:
    tok = os.environ.get("RAILWAY_API_TOKEN") or os.environ.get("RAILWAY_TOKEN_SECRET")
    if tok:
        return tok.strip()
    env_path = os.path.join(_repo_root(), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8-sig", errors="ignore") as fh:
            for line in fh:
                if line.startswith("RAILWAY_TOKEN_SECRET="):
                    return line.split("=", 1)[1].strip().strip('"').strip()
    sys.exit(
        "ERROR: no se encontró el token. Define RAILWAY_API_TOKEN o "
        "RAILWAY_TOKEN_SECRET, o ponlo en el .env de la raíz."
    )


def gql(token: str, query: str, variables: dict) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            # Railway está tras Cloudflare, que bloquea el User-Agent por
            # defecto de urllib (error 1010). Imitamos a curl, que sí pasa.
            "User-Agent": "curl/8.4.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"ERROR HTTP {e.code} de Railway: {e.read().decode('utf-8')[:300]}")
    except urllib.error.URLError as e:
        sys.exit(f"ERROR de red hablando con Railway: {e.reason}")
    if data.get("errors"):
        sys.exit(f"ERROR GraphQL: {json.dumps(data['errors'])[:400]}")
    return data["data"]


PROJECT_Q = """
query($id: String!) {
  project(id: $id) {
    name
    services {
      edges { node {
        id name
        serviceInstances { edges { node {
          environmentId
          source { image repo }
          rootDirectory railwayConfigFile builder healthcheckPath
        } } }
      } }
    }
  }
}
"""

DEPLOYS_Q = """
query($sid: String!, $eid: String!) {
  deployments(first: 1, input: { serviceId: $sid, environmentId: $eid }) {
    edges { node { id status meta } }
  }
}
"""

BUILDLOGS_Q = """
query($id: String!, $limit: Int!) {
  buildLogs(deploymentId: $id, limit: $limit) { message severity }
}
"""


def main() -> None:
    args = sys.argv[1:]
    log_lines = 40
    name_filter = None
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-h", "--help"):
            print(__doc__)
            return
        if a == "--logs":
            log_lines = int(args[i + 1])
            i += 2
            continue
        name_filter = a
        i += 1

    token = get_token()
    project_id = os.environ.get("RAILWAY_PROJECT_ID", DEFAULT_PROJECT_ID)

    data = gql(token, PROJECT_Q, {"id": project_id})
    project = data["project"]
    print("=" * 72)
    print(f" RAILWAY DOCTOR — proyecto: {project['name']}")
    print("=" * 72)

    any_blocked = False
    services = [e["node"] for e in project["services"]["edges"]]
    services.sort(key=lambda s: s["name"])

    for svc in services:
        if name_filter and name_filter.lower() not in svc["name"].lower():
            continue
        insts = svc["serviceInstances"]["edges"]
        if not insts:
            print(f"\n■ {svc['name']}: (sin instancias)")
            continue
        inst = insts[0]["node"]
        src = inst.get("source") or {}
        src_desc = (
            f"image={src['image']}" if src.get("image") else f"repo={src.get('repo')}"
        )

        # Último deploy
        dep_data = gql(
            token,
            DEPLOYS_Q,
            {"sid": svc["id"], "eid": inst["environmentId"]},
        )
        edges = dep_data["deployments"]["edges"]
        if not edges:
            status = "(sin deploys)"
            meta = {}
            dep_id = None
        else:
            node = edges[0]["node"]
            status = node["status"]
            meta = node.get("meta") or {}
            dep_id = node["id"]

        marker = "OK " if status in OK_STATUSES else (
            "!! " if status in BLOCKED_STATUSES else ".. "
        )
        print(f"\n[{marker}] {svc['name']}  —  último deploy: {status}")
        print(f"        source        : {src_desc}")
        print(f"        rootDirectory  : {inst.get('rootDirectory')!r}")
        print(f"        railwayConfig  : {inst.get('railwayConfigFile')!r}")
        print(f"        builder        : {inst.get('builder')}")
        sha = (meta.get('commitHash') or '')[:7]
        if sha:
            msg = (meta.get('commitMessage') or '').splitlines()
            print(f"        commit         : {sha}  {msg[0][:50] if msg else ''}")

        if status in BLOCKED_STATUSES:
            any_blocked = True
            reason = meta.get("skippedReason")
            if reason:
                print(f"        >> BLOQUEADO: {reason}")
                print("        >> (deploy SALTADO: Railway esperaba a un check de GitHub "
                      "que falló; no llegó a compilar)")
            elif status in ("FAILED", "CRASHED") and dep_id:
                print(f"        >> {status}: últimas líneas de build logs:")
                try:
                    logs = gql(token, BUILDLOGS_Q, {"id": dep_id, "limit": log_lines})
                    rows = logs.get("buildLogs") or []
                    if not rows:
                        print("           (sin build logs — posible crash de runtime; "
                              "revisa logs de runtime en el dashboard o `railway logs`)")
                    for r in rows[-log_lines:]:
                        sev = r.get("severity") or "info"
                        print(f"           [{sev}] {r.get('message','').rstrip()}")
                except SystemExit:
                    print("           (no se pudieron leer los build logs)")

    print("\n" + "=" * 72)
    if any_blocked:
        print(" VEREDICTO: hay al menos un servicio BLOQUEADO (ver arriba).")
        sys.exit(1)
    print(" VEREDICTO: todos los servicios con último deploy OK.")
    sys.exit(0)


if __name__ == "__main__":
    main()
