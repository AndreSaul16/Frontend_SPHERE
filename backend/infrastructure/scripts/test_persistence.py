import requests
import json
import uuid
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_persistence():
    print("🚀 Iniciando pruebas de persistencia...")
    
    # 1. Crear una sesión
    title = f"Test Session {uuid.uuid4().hex[:6]}"
    print(f"📝 Creando sesión: {title}")
    resp = requests.post(f"{BASE_URL}/sessions/", json={"title": title})
    assert resp.status_code == 200
    session = resp.json()
    session_id = session["session_id"]
    print(f"✅ Sesión creada: {session_id}")
    
    # 2. Enviar un mensaje (esto activará el checkpointer de LangGraph)
    print(f"💬 Enviando mensaje a la sesión {session_id}")
    query = "Hola, esto es una prueba de persistencia. Responde brevemente."
    payload = {
        "query": query,
        "session_id": session_id
    }
    
    # Usamos stream=True para manejar SSE
    with requests.post(f"{BASE_URL}/stream/", json=payload, stream=True) as r:
        full_response = ""
        for line in r.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    content = decoded_line[6:]
                    if content == "[DONE]":
                        break
                    try:
                        data = json.loads(content)
                        if data["type"] == "token":
                            full_response += data["content"]
                    except:
                        pass
        print(f"🤖 Respuesta recibida: {full_response[:50]}...")

    # 3. Recuperar el historial y verificar que el mensaje está ahí
    print(f"📜 Recuperando historial para {session_id}")
    resp = requests.get(f"{BASE_URL}/sessions/{session_id}/history")
    assert resp.status_code == 200
    history = resp.json()
    messages = history.get("messages", [])
    
    # Verificar que hay al menos 2 mensajes (Human + AI)
    print(f"📊 Mensajes encontrados: {len(messages)}")
    assert len(messages) >= 2
    
    # Buscar nuestro mensaje en el historial
    found = False
    for msg in messages:
        if "prueba de persistencia" in msg.get("content", ""):
            found = True
            break
    
    if found:
        print("✅ EL MENSAJE PERSISTE CORRECTAMENTE EN MONGODB")
    else:
        print("❌ EL MENSAJE NO SE ENCONTRÓ EN EL HISTORIAL")
        exit(1)

    # 4. Listar todas las sesiones y verificar que la nuestra aparece
    print("📂 Listando todas las sesiones...")
    resp = requests.get(f"{BASE_URL}/sessions/")
    assert resp.status_code == 200
    sessions = resp.json()
    ids = [s["session_id"] for s in sessions]
    if session_id in ids:
        print("✅ LA SESIÓN APARECE EN LA LISTA GLOBAL")
    else:
        print("❌ LA SESIÓN NO APARECE EN LA LISTA")
        exit(1)

if __name__ == "__main__":
    try:
        test_persistence()
        print("\n✨ TODAS LAS PRUEBAS DE PERSISTENCIA PASARON CORRECTAMENTE")
    except Exception as e:
        print(f"\n💥 ERROR EN LAS PRUEBAS: {e}")
        exit(1)
