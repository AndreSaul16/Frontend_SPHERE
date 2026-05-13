import os
import time
from pymongo import MongoClient
from dotenv import load_dotenv
from openai import OpenAI
import certifi

# 1. Cargar entorno (buscamos el .env en la raíz)
load_dotenv(dotenv_path='../.env') 

MONGO_URI = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DB_NAME", "sphere_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ Falta OPENAI_API_KEY en tu archivo .env")

# 2. Conexión Segura (con el parche certifi para el error SSL)
mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = mongo_client[DB_NAME]
collection = db["knowledge_base"]
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text):
    """
    Genera el vector usando el modelo text-embedding-3-small de OpenAI.
    Es rápido, barato y muy preciso.
    """
    # Limpiamos saltos de línea para mejorar la calidad del vector
    text = text.replace("\n", " ")
    return openai_client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def process_documents():
    # Solo buscamos documentos que NO tengan ya un vector (para poder reanudar si falla)
    query = {"embedding": {"$exists": False}}
    total_docs = collection.count_documents(query)
    
    if total_docs == 0:
        print("✅ Todos los documentos ya están vectorizados.")
        return

    print(f"📊 Documentos pendientes de vectorizar: {total_docs}")
    
    cursor = collection.find(query)
    
    for i, doc in enumerate(cursor):
        try:
            title = doc.get('title', 'Sin título')
            print(f"🧬 [{i+1}/{total_docs}] Procesando: {title[:50]}...")
            
            # Priorizamos el contenido markdown limpio, si no, el raw
            content = doc.get('content_markdown') or doc.get('content')
            
            if not content:
                print("   ⚠️ Contenido vacío. Saltando.")
                continue
                
            # Límite de seguridad de tokens (aprox 30k caracteres para el modelo small)
            # Para la Fase 4 haremos "chunking" (dividir en trozos), pero para este MVP esto funciona.
            safe_content = content[:20000] 
            
            # Generar Vector
            vector = get_embedding(safe_content)
            
            # Guardar en Mongo
            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"embedding": vector}}
            )
            print("   ✅ Vector guardado.")
            
            # Pequeña pausa para no saturar la API
            time.sleep(0.2)
            
        except Exception as e:
            print(f"   🔥 Error en documento {doc.get('_id')}: {e}")

if __name__ == "__main__":
    print("--- 🚀 INICIANDO VECTORIZACIÓN ---")
    process_documents()
    print("\n--- ✅ PROCESO TERMINADO ---")
