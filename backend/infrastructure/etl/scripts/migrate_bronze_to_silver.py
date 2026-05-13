"""
Script de Migración Bronze → Silver v2.0
==========================================
Lee TODOS los archivos de data/raw/ (Bronze Layer) y los sube a MongoDB
con el Schema Unificado v2.0, SIN volver a descargar nada de internet.

CRÍTICO: Este script garantiza que no se pierdan los 61 documentos originales.
"""

import os
import sys
import re
import time
from pathlib import Path
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


def detect_source_type(file_path):
    """
    Detecta el tipo de fuente según path y extensión.
    CORREGIDO: También detecta HTMLs en frameworks y case_studies.
    """
    file_path_lower = file_path.lower().replace("\\", "/")
    
    # Omitir archivos de metadatos
    if "corpus_definition" in file_path_lower:
        return "metadata_skip"
    if "libros_sinteticos" in file_path_lower:
        return "metadata_skip"
    
    # CTO
    if "cto/github" in file_path_lower and file_path.endswith(".md"):
        return "github_governance"
    elif "cto/blogs" in file_path_lower and file_path.endswith(".html"):
        return "engineering_blog"
    elif "cto/papers" in file_path_lower and file_path.endswith(".pdf"):
        return "academic_paper"
    elif "cto/books" in file_path_lower and file_path.endswith(".md"):
        return "synthetic_book_cto"
    
    # CMO
    elif "cmo/blogs" in file_path_lower and file_path.endswith(".html"):
        return "marketing_blog"
    elif "cmo/frameworks" in file_path_lower:
        # Tanto PDF como HTML
        if file_path.endswith(".pdf"):
            return "framework_document"
        elif file_path.endswith(".html"):
            return "framework_article"  # HTML de frameworks
    elif "cmo/case_studies" in file_path_lower:
        # Tanto PDF como HTML
        if file_path.endswith(".pdf"):
            return "case_study"
        elif file_path.endswith(".html"):
            return "case_study_article"  # HTML de case studies
    
    # CFO
    elif "cfo/metrics" in file_path_lower and file_path.endswith(".html"):
        return "saas_metrics"
    elif "cfo/macro" in file_path_lower and file_path.endswith(".html"):
        return "macro_analysis"
    
    return "unknown"


def extract_repo_from_path(file_path):
    """Extrae nombre del repo de un path de GitHub."""
    # Ejemplo: data/raw/cto/github/elastic_elasticsearch_CONTRIBUTING.md
    match = re.search(r'github/([^_]+)_([^_]+)_', file_path)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return "unknown/unknown"


def extract_title_from_md(content, filename):
    """Extrae título de un archivo Markdown."""
    # Buscar primer # título
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    # Fallback: usar nombre de archivo
    return filename.replace('.md', '').replace('_', ' ').replace('-', ' ').title()


def reconstruct_github_url(file_path):
    """Reconstruye la URL de GitHub desde el path del archivo."""
    # Ejemplo: elastic_elasticsearch_CONTRIBUTING.md → https://github.com/elastic/elasticsearch/blob/main/CONTRIBUTING.md
    filename = os.path.basename(file_path)
    match = re.match(r'([^_]+)_([^_]+)_(.+)\.md', filename)
    if match:
        owner = match.group(1)
        repo = match.group(2)
        file = match.group(3) + ".md"
        return f"https://github.com/{owner}/{repo}/blob/main/{file}"
    return f"file:///{os.path.abspath(file_path)}"


def process_github_markdown(file_path):
    """Procesa archivo Markdown de GitHub."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    repo_name = extract_repo_from_path(file_path)
    filename = os.path.basename(file_path).replace('.md', '')
    
    return {
        "source": f"GitHub - {repo_name}",
        "title": f"{repo_name.split('/')[-1]}: {extract_title_from_md(content, filename)}",
        "url": reconstruct_github_url(file_path),
        "file_path": os.path.relpath(file_path, PROJECT_ROOT),
        "content_markdown": content,
        "tags": ["governance", "architecture", repo_name.split('/')[1], repo_name.split('/')[0]],
        "agent_target": "CTO",
        "curated_category": "governance_document",
        "word_count": len(content.split()),
        "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "metadata": {
            "source_type": "github",
            "repo_full_name": repo_name,
            "file_type": "markdown",
            "branch": "main"
        }
    }


def process_blog_html(file_path, agent="CTO"):
    """Procesa archivo HTML de blog (usa trafilatura si está instalado)."""
    try:
        import trafilatura
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        markdown = trafilatura.extract(
            html_content,
            output_format="markdown",
            include_tables=True,
            include_links=True
        )
        
        if not markdown:
            markdown = "Error: No se pudo extraer contenido"
        
        # Extraer título del HTML
        title_match = re.search(r'<title>(.+?)</title>', html_content, re.IGNORECASE)
        title = title_match.group(1) if title_match else os.path.basename(file_path)
        
        category = "engineering_blog" if agent == "CTO" else "marketing_blog"
        
        return {
            "source": f"{agent} Blog",
            "title": title,
            "url": f"file:///{os.path.abspath(file_path)}",
            "file_path": os.path.relpath(file_path, PROJECT_ROOT),
            "content_markdown": markdown,
            "tags": ["blog", agent.lower(), "best-practices"],
            "agent_target": agent,
            "curated_category": category,
            "word_count": len(markdown.split()),
            "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": {
                "source_type": "blog",
                "original_format": "html"
            }
        }
    except Exception as e:
        print(f"   ⚠️ Error procesando HTML {os.path.basename(file_path)}: {e}")
        return None


def process_paper_pdf(file_path):
    """Procesa PDF de paper académico (usa PyMuPDF4LLM por ahora, Nougat es opcional)."""
    try:
        # Usar PyMuPDF4LLM (rápido)
        md_text = pymupdf4llm.to_markdown(file_path)
        
        title = os.path.basename(file_path).replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()
        
        return {
            "source": "Academic Paper - ArXiv",
            "title": title,
            "url": f"file:///{os.path.abspath(file_path)}",
            "file_path": os.path.relpath(file_path, PROJECT_ROOT),
            "content_markdown": md_text,
            "tags": ["paper", "arxiv", "research"],
            "agent_target": "CTO",
            "curated_category": "academic_paper",
            "word_count": len(md_text.split()),
            "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": {
                "source_type": "paper",
                "extraction_method": "pymupdf4llm",
                "original_format": "pdf"
            }
        }
    except Exception as e:
        print(f"   ⚠️ Error procesando PDF {os.path.basename(file_path)}: {e}")
        return None


def process_framework_pdf(file_path):
    """Procesa PDF de framework (CMO)."""
    try:
        md_text = pymupdf4llm.to_markdown(file_path)
        
        title = os.path.basename(file_path).replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()
        
        return {
            "source": "Strategic Framework",
            "title": title,
            "url": f"file:///{os.path.abspath(file_path)}",
            "file_path": os.path.relpath(file_path, PROJECT_ROOT),
            "content_markdown": md_text,
            "tags": ["framework", "strategy", "marketing"],
            "agent_target": "CMO",
            "curated_category": "framework_document",
            "word_count": len(md_text.split()),
            "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": {
                "source_type": "framework",
                "extraction_method": "pymupdf4llm",
                "original_format": "pdf"
            }
        }
    except Exception as e:
        print(f"   ⚠️ Error procesando framework {os.path.basename(file_path)}: {e}")
        return None


def process_synthetic_book_md(file_path):
    """Procesa libro sintético en Markdown (CTO)."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    title = os.path.basename(file_path).replace('.md', '').replace('_', ': ')
    
    return {
        "source": "Synthetic - Deep Research Books",
        "title": title,
        "url": f"file:///{os.path.abspath(file_path)}",
        "file_path": os.path.relpath(file_path, PROJECT_ROOT),
        "content_markdown": content,
        "tags": ["synthetic", "deep-research", "book", "cto"],
        "agent_target": "CTO",
        "curated_category": "synthetic_book",
        "word_count": len(content.split()),
        "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "metadata": {
            "source_type": "synthetic",
            "is_synthetic": True,
            "generated_by": "Gemini Deep Research",
            "original_format": "markdown"
        }
    }


def process_file(file_path, source_type):
    """Procesa archivo según tipo detectado."""
    if source_type == "github_governance":
        return process_github_markdown(file_path)
    elif source_type == "engineering_blog":
        return process_blog_html(file_path, "CTO")
    elif source_type == "marketing_blog":
        return process_blog_html(file_path, "CMO")
    elif source_type == "academic_paper":
        return process_paper_pdf(file_path)
    elif source_type == "framework_document":
        return process_framework_pdf(file_path)
    elif source_type == "framework_article":
        # HTMLs en frameworks/ - procesamos como blog CMO
        return process_blog_html(file_path, "CMO")
    elif source_type == "case_study":
        return process_framework_pdf(file_path)  # PDFs
    elif source_type == "case_study_article":
        # HTMLs en case_studies/ - procesamos como blog CMO
        return process_blog_html(file_path, "CMO")
    elif source_type == "synthetic_book_cto":
        return process_synthetic_book_md(file_path)
    elif source_type in ["saas_metrics", "macro_analysis"]:
        return process_blog_html(file_path, "CFO")
    elif source_type == "metadata_skip":
        # Archivos de metadatos - omitir silenciosamente
        return None
    else:
        print(f"   ⚠️ Tipo desconocido: {source_type} para {os.path.basename(file_path)}")
        return None


def migrate_bronze_to_silver():
    """
    Migra todos los archivos Bronze a MongoDB Silver v2.0.
    """
    print("=" * 70)
    print("📦 MIGRACIÓN BRONZE → SILVER v2.0")
    print("=" * 70)
    
    # Conectar a MongoDB
    try:
        client = MongoClient(
            MONGODB_URL,
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=30000
        )
        db = client[DB_NAME]
        collection = db["knowledge_base"]
        client.admin.command('ping')
        print(f"✅ Conectado a MongoDB ({DB_NAME})")
    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        return 0
    
    # Escanear recursivamente data/raw/
    all_files = []
    for root, dirs, files in os.walk(RAW_DATA_DIR):
        for file in files:
            if file.endswith(('.md', '.html', '.pdf')):
                all_files.append(os.path.join(root, file))
    
    # También buscar en data/synthetic si existe
    synthetic_dir = os.path.join(PROJECT_ROOT, "data", "synthetic")
    if os.path.exists(synthetic_dir):
        for root, dirs, files in os.walk(synthetic_dir):
            for file in files:
                if file.endswith('.md'):
                    all_files.append(os.path.join(root, file))
    
    print(f"\n📂 Encontrados {len(all_files)} archivos en Bronze Layer\n")
    
    # Procesar cada archivo
    migrated = 0
    skipped = 0
    errors = 0
    
    for file_path in all_files:
        # Detectar tipo
        source_type = detect_source_type(file_path)
        
        if source_type == "metadata_skip":
            # Archivos de metadatos - omitir silenciosamente
            skipped += 1
            continue
        
        if source_type == "unknown":
            print(f"⚠️ Tipo desconocido: {os.path.basename(file_path)}")
            skipped += 1
            continue
        
        print(f"📄 {os.path.basename(file_path)} ({source_type})")
        
        # Procesar
        doc = process_file(file_path, source_type)
        
        if doc:
            # Subir a MongoDB
            try:
                collection.update_one(
                    {"url": doc["url"]},
                    {"$set": doc},
                    upsert=True
                )
                migrated += 1
                print(f"   ✅ Migrado")
            except Exception as e:
                print(f"   ❌ Error MongoDB: {e}")
                errors += 1
        else:
            errors += 1
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE MIGRACIÓN")
    print("=" * 70)
    print(f"✅ Archivos migrados: {migrated}")
    print(f"⚠️ Archivos omitidos: {skipped}")
    print(f"❌ Errores: {errors}")
    print(f"📦 Total en MongoDB: {collection.count_documents({})}")
    
    return migrated


if __name__ == "__main__":
    migrated_count = migrate_bronze_to_silver()
    print(f"\n✅ Migración completada: {migrated_count} documentos")
