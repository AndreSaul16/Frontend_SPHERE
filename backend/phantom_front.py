#!/usr/bin/env python
"""
👻 SPHERE Phantom Frontend (CLI) - V2.0 (Auditoría & Stress)
Simulador avanzado con herramientas de diagnóstico y suite de validación.
"""
import asyncio
import json
import sys
import os
import time
from typing import Optional, List, Dict
import httpx
from colorama import init, Fore, Style, Back

# Inicializar colorama para Windows
init(autoreset=True)

# Configuración
BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = httpx.Timeout(120.0, connect=10.0)

# Colores por Rol
ROLE_COLORS = {
    "CEO": Fore.CYAN + Style.BRIGHT,
    "CTO": Fore.GREEN + Style.BRIGHT,
    "CFO": Fore.YELLOW + Style.BRIGHT,
    "CMO": Fore.MAGENTA + Style.BRIGHT,
    "FINAL": Fore.WHITE + Style.BRIGHT,
    "SYSTEM": Fore.RED + Style.DIM,
    "USER": Fore.BLUE + Style.BRIGHT,
    "DIAG": Fore.BLACK + Back.WHITE,
}

class PhantomFront:
    def __init__(self, debug=False):
        self.session_id: Optional[str] = None
        self.current_agent: Optional[str] = None
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT)
        self.is_inside_artifact = False
        self.debug_mode = debug

    def log_diag(self, msg: str):
        if self.debug_mode:
            print(f"\n{ROLE_COLORS['DIAG']} [DIAG] {msg} {Style.RESET_ALL}")

    async def create_session(self, title: str) -> str:
        response = await self.client.post("/sessions/", json={"title": title})
        data = response.json()
        return data["session_id"]

    async def stream_chat(self, query: str, session_id: Optional[str] = None, agent: Optional[str] = None, silent=False):
        sid = session_id or self.session_id
        target = agent or self.current_agent
        
        request_data = {"query": query, "session_id": sid}
        if target: request_data["target_role"] = target

        full_response = ""
        events_received = []

        try:
            if not silent:
                print(f"\n{ROLE_COLORS['USER']}Tú: {Style.RESET_ALL}{query}")
            
            async with self.client.stream("POST", "/stream/", json=request_data) as response:
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "): continue
                    
                    data_str = line[6:].strip()
                    if self.debug_mode and not silent:
                        print(f"\n{Fore.BLACK}{Back.YELLOW}[RAW]{Style.RESET_ALL} {data_str}")
                    
                    if data_str == "[DONE]": break

                    try:
                        event = json.loads(data_str)
                        events_received.append(event)
                        ev_type = event.get("type")

                        if ev_type == "token":
                            content = event.get("content", "")
                            full_response += content
                            if not silent: print(content, end="", flush=True)
                        elif ev_type == "meta" and not silent:
                            print(f"\n{ROLE_COLORS.get(event['role'], Fore.WHITE)}[{event['role']}]{Style.RESET_ALL} ", end="")
                        elif ev_type == "artifact_open" and not silent:
                            print(f"\n📦 [{event['title']}] ", end="")
                        elif ev_type == "artifact_close" and not silent:
                            print(f" ✅", end="")
                    except: continue
            
            return {"content": full_response, "events": events_received}
        except Exception as e:
            return {"error": str(e)}

    async def run_stress_test(self, n_concurrent=5):
        print(f"\n🔥 Iniciando Stress Test de Concurrencia ({n_concurrent} streams simultáneos)...")
        tasks = []
        for i in range(n_concurrent):
            sid = await self.create_session(f"Stress Test {i}")
            tasks.append(self.stream_chat(f"¿Quién eres? (Hilo {i})", session_id=sid, silent=True))
        
        start = time.time()
        results = await asyncio.gather(*tasks)
        end = time.time()
        
        success = [r for r in results if "error" not in r]
        print(f"\n📊 Resultado Stress Test:")
        print(f"   - Tiempo total: {end-start:.2f}s")
        print(f"   - Exitosos: {len(success)}/{n_concurrent}")
        return len(success) == n_concurrent

    async def test_memory(self):
        print(f"\n🧠 Probando Memoria de Corto Plazo...")
        sid = await self.create_session("Memory Test")
        
        # Turno 1
        secret = "Magenta-77"
        await self.stream_chat(f"Hola, me llamo Saúl y mi clave es '{secret}'. Solo di 'Entendido'.", session_id=sid, silent=True)
        
        # Turno 2
        resp = await self.stream_chat("¿Cómo me llamo y cuál es mi clave?", session_id=sid, silent=True)
        content = resp.get("content", "")
        
        passed = "Saúl" in content and secret in content
        print(f"   - Respuesta: {content[:100]}...")
        print(f"   - Resultado: {'✅ PASA' if passed else '❌ FALLA'}")
        return passed

    async def check_mongo_metadata(self, session_id):
        # Intentamos verificar vía API que la sesión existe en la lista
        resp = await self.client.get("/sessions/")
        sessions = resp.json()
        exists = any(s["session_id"] == session_id for s in sessions)
        print(f"🔍 Verificando metadatos en MongoDB (vía API): {'✅ OK' if exists else '❌ NO ENCONTRADA'}")
        return exists

    async def test_intra_session_concurrency(self):
        print(f"\n🚨 Probando Concurrencia Intra-Sesión (Mismo thread_id)...")
        sid = await self.create_session("Intra-Session Stress")
        
        # Lanzar dos consultas al mismo tiempo para la misma sesión
        tasks = [
            self.stream_chat("Enumera 10 ventajas de Python", session_id=sid, silent=True),
            self.stream_chat("Escribe un poema sobre el código", session_id=sid, silent=True)
        ]
        
        print(f"   - Enviando 2 peticiones paralelas al SID: {sid}")
        results = await asyncio.gather(*tasks)
        
        success = [r for r in results if "error" not in r]
        errors = [r for r in results if "error" in r]
        
        passed = len(success) == 2
        print(f"   - Exitosos: {len(success)}/2 | Errores: {len(errors)}")
        if errors:
            print(f"   - Detalle Error: {errors[0]['error']}")
            
        return passed

    async def run_audit(self):
        self.print_header("🛡️ AUDITORÍA TÉCNICA DE PERSISTENCIA")
        results = {}
        
        # 1. Metadatos
        sid = await self.create_session("Audit Session")
        results["T1: Metadatos"] = await self.check_mongo_metadata(sid)
        
        # 2. Concurrencia Inter-Sesión
        results["T2: Concurrencia Inter"] = await self.run_stress_test(3)
        
        # 3. Persistencia Historial
        await self.stream_chat("Mensaje de prueba para historia", session_id=sid, silent=True)
        hist_resp = await self.client.get(f"/sessions/{sid}/history")
        results["T3: Persistencia"] = len(hist_resp.json().get("messages", [])) >= 2
        
        # 4. Artefactos
        print(f"\n📦 Probando Artefactos (SSE JSON)...")
        art_resp = await self.stream_chat("Genera un artefacto de código Python que imprima 'Hola'", session_id=sid, silent=True)
        ev_types = [e.get("type") for e in art_resp.get("events", [])]
        results["T4: Artefactos"] = "artifact_open" in ev_types and "artifact_close" in ev_types
        
        # 5. Memoria
        results["T5: Memoria"] = await self.test_memory()
        
        # 6. Integridad JSON
        results["T6: Integridad JSON"] = all(isinstance(e, dict) for e in art_resp.get("events", []))
        
        # 7. Handoff
        print(f"\n🔄 Probando Enrutamiento (Handoff)...")
        hand_resp = await self.stream_chat("Pregunta al CTO sobre el servidor y al CFO sobre el coste", session_id=sid, silent=True)
        roles = set([e.get("role") for e in hand_resp.get("events", []) if e.get("type") == "meta"])
        results["T7: Handoff"] = len(roles) >= 2
        
        # 8. Aislamiento
        print(f"\n🔒 Probando Aislamiento de Sesiones...")
        sid2 = await self.create_session("Isolation Test")
        await self.stream_chat("Mi clave es 'SEC_XYZ'", session_id=sid2, silent=True)
        resp_isolated = await self.stream_chat("¿Sabes algo de una clave 'SEC_XYZ'?", session_id=sid, silent=True)
        results["T8: Aislamiento"] = "SEC_XYZ" not in resp_isolated.get("content", "")

        # 9. Concurrencia Intra-Sesión
        results["T9: Concurrencia Intra"] = await self.test_intra_session_concurrency()

        self.print_header("📊 RESUMEN FINAL DE AUDITORÍA")
        for test, passed in results.items():
            status = f"{Fore.GREEN}PASÓ" if passed else f"{Fore.RED}FALLÓ"
            print(f"{test.ljust(25)} : {status}{Style.RESET_ALL}")
        
        return results

    def print_header(self, text: str):
        print("\n" + "="*70)
        print(f" {text}")
        print("="*70)

async def main():
    front = PhantomFront(debug="--debug" in sys.argv)
    if "--audit" in sys.argv:
        await front.run_audit()
        await front.client.aclose()
        return

    # Si no hay argumentos, correr modo normal...
    # (El resto del código interactivo del script anterior se integraría aquí)
    print("Usa --audit para correr los tests o --debug para ver SSE raw.")

if __name__ == "__main__":
    asyncio.run(main())
