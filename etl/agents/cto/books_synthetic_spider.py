"""
CTO Spider - Synthetic Books Ingestion
======================================
Spider para integrar libros sintéticos a MongoDB con formato Silver Medallion.
"""

import os
import sys
import re

# Importar clase base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.base_spider import BaseTechSpider, PROJECT_ROOT


class BooksSyntheticSpider(BaseTechSpider):
    """
    Spider para integrar libros sintéticos del CTO a MongoDB.
    Limpia referencias embebidas y aplica formato Silver Medallion.
    """
    
    def __init__(self):
        super().__init__(agent_name="CTO")
        self.books_dir = os.path.join(PROJECT_ROOT, "data", "synthetic", "cto", "books")
    
    def clean_content(self, content):
        """
        Limpia el contenido eliminando la sección de referencias.
        
        Args:
            content: Contenido markdown completo del libro
        
        Returns:
            tuple: (contenido_limpio, num_referencias)
        """
        # Patrones para detectar secciones de referencias
        reference_patterns = [
            r'(?i)##?\s*(?:Referencias|Obras\s+citadas|References|Bibliography).*',
            r'(?i)####\s*\*\*Obras\scitadas\*\*.*'
        ]
        
        # Buscar el inicio de la sección de referencias
        reference_start = -1
        for pattern in reference_patterns:
            match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            if match:
                reference_start = match.start()
                break
        
        # Si se encuentra la sección, cortarla
        if reference_start != -1:
            clean_content = content[:reference_start].strip()
            references_section = content[reference_start:]
            
            # Contar referencias (buscar URLs o números de referencia)
            url_count = len(re.findall(r'https?://[^\s\)]+', references_section))
            num_count = len(re.findall(r'^\d+\.', references_section, re.MULTILINE))
            num_references = max(url_count, num_count)
        else:
            clean_content = content
            num_references = 0
        
        return clean_content, num_references
    
    def extract_metadata(self, content, filename):
        """
        Extrae metadata del contenido del libro.
        
        Args:
            content: Contenido markdown del libro
            filename: Nombre del archivo
        
        Returns:
            dict: Metadata extraída
        """
        metadata = {
            "book_category": "CTO",
            "word_count": len(content.split()),
            "filename": filename
        }
        
        # Extraer título (primer h1)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            metadata["extracted_title"] = title_match.group(1)
        
        return metadata
    
    def generate_tags(self, title, content):
        """
        Genera tags basados en el título y contenido.
        
        Args:
            title: Título del libro
            content: Contenido del libro
        
        Returns:
            list: Lista de tags
        """
        tags = ["synthetic", "book", "cto"]
        
        # Mapeo de keywords a tags
        keyword_map = {
            "accelerate": ["accelerate", "devops", "dora-metrics"],
            "dora": ["dora-metrics", "devops"],
            "microservicios": ["microservices", "architecture"],
            "microservices": ["microservices", "architecture"],
            "sre": ["sre", "reliability", "google"],
            "arquitectura": ["architecture", "design"],
            "architecture": ["architecture", "design"],
            "datos": ["data", "data-engineering"],
            "data": ["data", "data-engineering"],
            "team topologies": ["team-topologies", "organization"],
            "staff engineer": ["staff-engineer", "leadership"],
            "ingeniería": ["engineering", "systems"]
        }
        
        title_lower = title.lower()
        content_lower = content[:2000].lower()  # Solo primeros 2000 chars
        
        for keyword, related_tags in keyword_map.items():
            if keyword in title_lower or keyword in content_lower:
                tags.extend(related_tags)
        
        # Remover duplicados
        return list(set(tags))
    
    def run(self):
        """
        Ejecuta el spider:
        1. Lee todos los archivos .md de la carpeta de libros sintéticos
        2. Limpia referencias embebidas
        3. Aplica formato Silver Medallion
        4. Sube a MongoDB
        """
        print(f"\n📚 [{self.__class__.__name__}] Integrando libros sintéticos...")
        
        try:
            # Verificar que la carpeta existe
            if not os.path.exists(self.books_dir):
                print(f"   ❌ No se encontró el directorio: {self.books_dir}")
                return
            
            # Listar archivos .md
            book_files = [f for f in os.listdir(self.books_dir) if f.endswith('.md')]
            
            if len(book_files) == 0:
                print(f"   ℹ️ No se encontraron libros en {self.books_dir}")
                return
            
            print(f"   📊 Encontrados {len(book_files)} libros")
            
            ingested_count = 0
            skipped_count = 0
            
            for filename in book_files:
                filepath = os.path.join(self.books_dir, filename)
                
                # Leer contenido
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    print(f"   ❌ Error leyendo {filename}: {e}")
                    continue
                
                # Usar filepath como URL única
                file_url = f"file:///{filepath.replace(os.sep, '/')}"
                
                # Verificar si ya existe
                if self.url_exists(file_url):
                    print(f"   💤 Ya existe: {filename}")
                    skipped_count += 1
                    continue
                
                print(f"\n   📄 Procesando: {filename}")
                
                # Limpiar contenido
                clean_content, num_references = self.clean_content(content)
                
                if len(clean_content) < 5000:
                    print(f"      ⚠️ Contenido muy corto después de limpieza ({len(clean_content)} chars)")
                    continue
                
                # Extraer metadata
                metadata = self.extract_metadata(content, filename)
                metadata["has_references"] = num_references > 0
                metadata["total_references"] = num_references
                
                # Generar título desde filename si no se extrae del contenido
                title = metadata.get("extracted_title", filename.replace('.md', ''))
                
                # Generar tags
                tags = self.generate_tags(title, clean_content)
                
                # Construir documento Silver Medallion
                doc = {
                    "source": "Synthetic Books - CTO",
                    "title": title,
                    "url": file_url,
                    "file_path": filepath,
                    "content_markdown": clean_content,
                    "tags": tags,
                    "curated_category": "synthetic_book",
                    "metadata": metadata
                }
                
                # Guardar en MongoDB
                self.save_knowledge(doc)
                
                print(f"      ✅ Ingresado: {len(clean_content)} chars, {num_references} refs eliminadas")
                ingested_count += 1
            
            print(f"\n   📊 Resumen de ingesta:")
            print(f"      ✅ Ingresados: {ingested_count}")
            print(f"      💤 Ya existían: {skipped_count}")
            
        except Exception as e:
            print(f"   🔥 Error crítico en BooksSyntheticSpider: {e}")


if __name__ == "__main__":
    spider = BooksSyntheticSpider()
    spider.run()
