"""
Script para Procesar Libros Sintéticos
=======================================
Limpia referencias externas del contenido y las mueve a metadata.

PROBLEMA RESUELTO:
- Elimina "Obras citadas" / "Referencias" del final del texto
- Elimina marcadores [1], [2], [3] del cuerpo
- Extrae URLs a campo metadata.original_sources
- Mantiene citas in-context ("Según IFRS 9...")

HIGIENE DE DATOS para Fine-Tuning:
- Evita que el agente aprenda a generar bibliografías en sus respuestas
- Previene alucinación de URLs
- Reduce tokens de ruido
"""

import os
import sys
import re
from pymongo import MongoClient
from dotenv import load_dotenv

# Configuración
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

MONGODB_URL = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DB_NAME", "sphere_db")

# Rutas
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SYNTHETIC_DIR = os.path.join(PROJECT_ROOT, "data", "synthetic", "cto", "books")


def extract_references_section(content):
    """
    Detecta y extrae la sección de referencias del final del documento.
    
    Returns:
        tuple: (contenido_limpio, lista_de_urls)
    """
    # Patrones para detectar inicio de sección de referencias
    reference_patterns = [
        r'\n#{1,4}\s*\*\*Referencias Integradas\*\*',
        r'\n#{1,4}\s*\*\*Obras citadas\*\*',
        r'\n#{1,4}\s*Referencias',
        r'\n#{1,4}\s*Fuentes',
        r'\n#{1,4}\s*Sources',
        r'\n#{1,4}\s*Bibliography'
    ]
    
    # Buscar la primera coincidencia
    split_position = None
    for pattern in reference_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            split_position = match.start()
            break
    
    if split_position is None:
        # No se encontró sección de referencias
        return content, []
    
    # Dividir contenido
    clean_content = content[:split_position].rstrip()
    references_section = content[split_position:]
    
    # Extraer URLs de la sección de referencias
    url_pattern = r'https?://[^\s\)]+(?:\([^\)]*\))?'
    urls = re.findall(url_pattern, references_section)
    
    # Limpiar URLs (quitar paréntesis finales si existen)
    cleaned_urls = [url.rstrip(')') for url in urls]
    
    return clean_content, cleaned_urls


def remove_numeric_markers(content):
    """
    Elimina marcadores numéricos [1], [2], etc. del contenido.
    
    CUIDADO: Mantiene citas de autoridad in-context.
    """
    # Eliminar [1], [2], [123], etc.
    # Pero NO eliminar [IFRS 9], [CEO], etc.
    content = re.sub(r'\[(\d+)\]', '', content)
    
    # También eliminar superíndices numéricos si existen
    content = re.sub(r'\^(\d+)', '', content)
    
    return content


def extract_book_metadata(filepath):
    """
    Extrae metadatos del nombre del archivo y ruta.
    """
    filename = os.path.basename(filepath)
    # Remover extensión .md
    title = filename.replace('.md', '')
    # Limpiar guiones bajos y símbolos
    title = title.replace('_', ' ').replace(':', ' -')
    
    return {
        'title': title,
        'filename': filename,
        'file_path': filepath
    }


def process_book(filepath):
    """
    Procesa un libro sintético completo.
    
    Returns:
        dict: Documento listo para MongoDB
    """
    print(f"\n📚 Procesando: {os.path.basename(filepath)}")
    
    # Leer contenido
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_content = f.read()
    
    # 1. Extraer sección de referencias
    content_without_refs, source_urls = extract_references_section(raw_content)
    print(f"   📎 Referencias encontradas: {len(source_urls)}")
    
    # 2. Eliminar marcadores numéricos
    clean_content = remove_numeric_markers(content_without_refs)
    
    # 3. Extraer metadata del archivo
    metadata = extract_book_metadata(filepath)
    
    # 4. Crear documento para MongoDB
    doc = {
        "source": "Synthetic - Deep Research Books",
        "title": metadata['title'],
        "url": f"file:///{filepath}",  # URL local para referencia
        "file_path": filepath,
        "content_markdown": clean_content.strip(),
        "tags": ["synthetic", "deep-research", "book", "cto"],
        "agent_target": "CTO",
        "metadata": {
            "is_synthetic": True,
            "generated_by": "Gemini Deep Research",
            "original_filename": metadata['filename'],
            "original_sources": source_urls,
            "references_count": len(source_urls)
        },
        "curated_category": "synthetic_book"
    }
    
    print(f"   ✅ Limpio: {len(clean_content)} chars (vs {len(raw_content)} original)")
    print(f"   📊 Reducción: {len(raw_content) - len(clean_content)} chars de ruido eliminados")
    
    return doc


def main():
    """
    Procesa todos los libros sintéticos y los guarda en MongoDB.
    """
    print("=" * 70)
    print("📚 SPHERE - Procesador de Libros Sintéticos")
    print("=" * 70)
    
    # Conectar a MongoDB
    try:
        client = MongoClient(MONGODB_URL)
        db = client[DB_NAME]
        collection = db["knowledge_base"]
        client.admin.command('ping')
        print(f"✅ Conectado a MongoDB ({DB_NAME})")
    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        return
    
    # Buscar archivos .md en el directorio de sintéticos
    if not os.path.exists(SYNTHETIC_DIR):
        print(f"❌ Directorio no encontrado: {SYNTHETIC_DIR}")
        return
    
    md_files = [f for f in os.listdir(SYNTHETIC_DIR) if f.endswith('.md')]
    
    if not md_files:
        print(f"⚠️ No se encontraron archivos .md en {SYNTHETIC_DIR}")
        return
    
    print(f"\n📂 Encontrados {len(md_files)} libros para procesar\n")
    
    # Procesar cada libro
    processed = 0
    skipped = 0
    
    for filename in md_files:
        filepath = os.path.join(SYNTHETIC_DIR, filename)
        
        try:
            # Procesar libro
            doc = process_book(filepath)
            
            # Verificar si ya existe
            if collection.count_documents({"url": doc["url"]}, limit=1) > 0:
                print(f"   💤 Ya existe en BD, actualizando...")
            
            # Guardar/actualizar en MongoDB
            collection.update_one(
                {"url": doc["url"]},
                {"$set": doc},
                upsert=True
            )
            
            processed += 1
            
        except Exception as e:
            print(f"   ❌ Error procesando {filename}: {e}")
            skipped += 1
    
    # Resumen
    print("\n" + "=" * 70)
    print("✅ PROCESAMIENTO COMPLETADO")
    print("=" * 70)
    print(f"📊 Libros procesados: {processed}")
    print(f"⚠️ Libros con errores: {skipped}")
    print(f"🗄️ Total en base de conocimiento: {collection.count_documents({})}")
    print("\n💡 Los libros ahora están limpios y listos para fine-tuning")


if __name__ == "__main__":
    main()
