"""
Procesador de PDFs Sintéticos Nuevos (CEO/CFO/CMO)
====================================================
Procesa SOLO los 15 PDFs nuevos de Deep Research que nunca se han procesado.

PDFs target:
- CEO (5): Estrategia de Negocio, Estrategia IA, Océano Azul, Grove, Horowitz
- CFO (5): Blitzscaling, Damodaran, Inteligencia Financiera, Subscribed, Venture Deals
- CMO (5): Cialdini, Cruzando el Abismo, Growth Hacking, Posicionamiento, StoryBrand
"""

import os
import sys
import re
import time
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv
import pymupdf4llm

# Configuración
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

# Cargar .env desde la raíz del proyecto
ENV_PATH = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(dotenv_path=ENV_PATH)

MONGODB_URL = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DB_NAME", "sphere_db")

RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")


def extract_references_section(content):
    """
    Detecta y extrae la sección de referencias del final del documento.
    CORREGIDO: Patrones actualizados para coincider con el formato real de PDFs.
    
    El texto real es: "Referencias Integradas en el Corpus de Análisis:"
    NO tiene asteriscos markdown ni # al inicio.
    """
    reference_patterns = [
        # Patrones exactos del formato de Deep Research
        r'Referencias Integradas en el Corpus de Análisis[:\.]',
        r'Referencias Integradas[:\.]',
        r'Obras citadas',
        # Patrones con markdown (por si acaso)
        r'\n#{1,4}\s*\*\*Referencias Integradas\*\*',
        r'\n#{1,4}\s*\*\*Obras citadas\*\*',
        r'\n#{1,4}\s*Referencias',
        # Patrones genéricos
        r'\nReferencias\s*\n',
        r'\nFuentes\s*\n',
        r'\nSources\s*\n',
        r'\nBibliography\s*\n',
        # Patrón por URL pattern al final (muchas URLs seguidas)
        r'(?:https?://[^\s]+\s*\n){5,}',  # 5+ URLs seguidas indica sección de referencias
    ]
    
    split_position = None
    matched_pattern = None
    
    for pattern in reference_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            split_position = match.start()
            matched_pattern = pattern
            print(f"   🔍 Patrón encontrado: {pattern[:40]}...")
            break
    
    if split_position is None:
        print("   ⚠️ No se encontró sección de referencias")
        return content, []
    
    clean_content = content[:split_position].rstrip()
    references_section = content[split_position:]
    
    # Extraer URLs de la sección de referencias
    url_pattern = r'https?://[^\s\)\,]+'
    urls = re.findall(url_pattern, references_section)
    # Limpiar URLs
    cleaned_urls = [url.rstrip(').,') for url in urls]
    
    print(f"   ✅ Sección de referencias cortada: {len(references_section)} chars, {len(cleaned_urls)} URLs")
    
    return clean_content, cleaned_urls


def remove_numeric_markers(content):
    """
    Elimina marcadores numéricos [1], [2], etc. del contenido.
    Reutilizado de process_synthetic_books.py
    """
    content = re.sub(r'\[(\d+)\]', '', content)
    content = re.sub(r'\^(\d+)', '', content)
    return content


def extract_tags_from_filename(filename):
    """Extrae tags relevantes del nombre del archivo."""
    filename_lower = filename.lower()
    tags = ["synthetic", "deep-research"]
    
    # Tags específicos por contenido
    if "estrategia" in filename_lower:
        tags.extend(["strategy", "business"])
    if "grove" in filename_lower or "horowitz" in filename_lower:
        tags.extend(["management", "leadership"])
    if "oceano azul" in filename_lower or "blue ocean" in filename_lower:
        tags.extend(["innovation", "strategy"])
    if "damodaran" in filename_lower or "valoracion" in filename_lower:
        tags.extend(["valuation", "finance"])
    if "blitzscaling" in filename_lower:
        tags.extend(["scaling", "growth"])
    if "venture deals" in filename_lower:
        tags.extend(["fundraising", "investment"])
    if "cialdini" in filename_lower:
        tags.extend(["persuasion", "psychology"])
    if "posicionamiento" in filename_lower or "positioning" in filename_lower:
        tags.extend(["branding", "marketing"])
    if "storybrand" in filename_lower:
        tags.extend(["narrative", "conversion"])
        
    return tags


def process_synthetic_pdf(pdf_path, agent):
    """
    Procesa PDF sintético con PyMuPDF4LLM.
    """
    print(f"\n📚 Procesando: {os.path.basename(pdf_path)}")
    
    try:
        # Extraer texto a Markdown
        print("   🔄 Extrayendo texto con PyMuPDF4LLM...")
        md_text = pymupdf4llm.to_markdown(pdf_path)
        
        # Limpiar referencias
        print("   🧹 Limpiando referencias...")
        clean_content, source_urls = extract_references_section(md_text)
        clean_content = remove_numeric_markers(clean_content)
        
        # Generar título limpio
        title = os.path.basename(pdf_path).replace('.pdf', '').replace('_', ': ')
        
        # Construir documento
        doc = {
            "source": "Synthetic - Deep Research Books",
            "title": title,
            "url": f"file:///{os.path.abspath(pdf_path)}",
            "file_path": os.path.relpath(pdf_path, PROJECT_ROOT),
            "content_markdown": clean_content,
            "tags": extract_tags_from_filename(pdf_path),
            "agent_target": agent,
            "curated_category": "synthetic_book",
            "word_count": len(clean_content.split()),
            "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": {
                "source_type": "synthetic",
                "is_synthetic": True,
                "generated_by": "Gemini Deep Research",
                "original_format": "pdf",
                "extraction_method": "pymupdf4llm",
                "original_sources": source_urls,
                "references_count": len(source_urls)
            }
        }
        
        print(f"   ✅ Procesado: {len(clean_content)} chars, {len(source_urls)} referencias")
        return doc
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def process_new_synthetic_pdfs():
    """
    Procesa los 15 PDFs sintéticos nuevos de CEO/CFO/CMO.
    """
    print("=" * 70)
    print("📚 PROCESAMIENTO DE PDFs SINTÉTICOS NUEVOS")
    print("=" * 70)
    
    # Conectar a MongoDB
    try:
        client = MongoClient(
            MONGODB_URL,
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=30000
        )
        db = client[DB_NAME]
        collection = db["knowledge_base"]
        client.admin.command('ping')
        print(f"✅ Conectado a MongoDB ({DB_NAME})\n")
    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        return 0
    
    # Listar PDFs por agente
    agents_pdfs = {
        "CEO": [],
        "CFO": [],
        "CMO": []
    }
    
    for agent in ["ceo", "cfo", "cmo"]:
        agent_dir = os.path.join(RAW_DATA_DIR, agent)
        if os.path.exists(agent_dir):
            for file in os.listdir(agent_dir):
                if file.endswith('.pdf'):
                    agents_pdfs[agent.upper()].append(os.path.join(agent_dir, file))
    
    # Resumen
    total_pdfs = sum(len(pdfs) for pdfs in agents_pdfs.values())
    print(f"📂 PDFs encontrados:")
    for agent, pdfs in agents_pdfs.items():
        print(f"   {agent}: {len(pdfs)} PDFs")
    print(f"\n🎯 Total a procesar: {total_pdfs} PDFs\n")
    
    # Procesar cada PDF
    processed = 0
    errors = 0
    
    for agent, pdfs in agents_pdfs.items():
        print(f"\n{'='*70}")
        print(f"📊 Agente: {agent}")
        print(f"{'='*70}")
        
        for pdf_path in pdfs:
            doc = process_synthetic_pdf(pdf_path, agent)
            
            if doc:
                # Subir a MongoDB
                try:
                    collection.update_one(
                        {"url": doc["url"]},
                        {"$set": doc},
                        upsert=True
                    )
                    processed += 1
                    print(f"   💾 Guardado en MongoDB")
                except Exception as e:
                    print(f"   ❌ Error MongoDB: {e}")
                    errors += 1
            else:
                errors += 1
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE PROCESAMIENTO")
    print("=" * 70)
    print(f"✅ PDFs procesados: {processed}")
    print(f"❌ Errores: {errors}")
    print(f"📦 Total en MongoDB: {collection.count_documents({})}")
    
    return processed


if __name__ == "__main__":
    processed_count = process_new_synthetic_pdfs()
    print(f"\n✅ Procesamiento completado: {processed_count} PDFs nuevos")
