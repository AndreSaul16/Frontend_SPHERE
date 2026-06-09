"""
CMO Spiders - Marketing Frameworks
===================================
Spiders para frameworks estratégicos y recursos PDF de alto valor.
Incluye documentos de investigación, modelos mentales y playbooks.
"""

import os
import sys
import time
import certifi
import requests
import io

# Importar clase base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.base_spider import BaseTechSpider

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    print("⚠️ pdfplumber no disponible. Instalar con: pip install pdfplumber")
    PDF_AVAILABLE = False


class MarketingFrameworkSpider(BaseTechSpider):
    """
    Spider para frameworks de marketing estratégico.
    Procesa PDFs y extrae contenido estructurado.
    """
    
    # Frameworks prioritarios del corpus CMO
    FRAMEWORKS = [
        {
            "title": "The Long and the Short of It (Binet & Field)",
            "url": "https://screenforce.nl/wp-content/uploads/2015/11/the-long-and-short-of-it.pdf",
            "concept": "Ratio Brand (60%) vs Performance (40%)",
            "category": "research",
            "priority": "critical"
        },
        {
            "title": "The Messy Middle (Google Research)",
            "url": "https://www.thinkwithgoogle.com/_qs/documents/9998/Decoding_Decisions_The_Messy_Middle_of_Purchase_Behavior.pdf",
            "concept": "Modelo de decisión Exploración/Evaluación",
            "category": "research",
            "priority": "critical"
        },
        {
            "title": "StoryBrand Framework (SB7)",
            "url": "https://storybrand.com/downloads/your-brand-is-not-the-hero.pdf",
            "concept": "El cliente es el héroe",
            "category": "framework",
            "priority": "high"
        },
        {
            "title": "Blue Ocean Strategy",
            "url": "https://info.eaglenet.jbu.edu/depts/odl/om/resources/om3263/BOSHBR.pdf",
            "concept": "Competir en espacios no disputados",
            "category": "framework",
            "priority": "high"
        },
        {
            "title": "HubSpot Inbound Marketing Workbook",
            "url": "https://www.hubspot.com/hs-fs/hub/53/file-13201504-pdf/docs/hubspotinboundmarketingworkbook-pdf.pdf",
            "concept": "Inbound vs Outbound",
            "category": "playbook",
            "priority": "medium"
        }
    ]
    
    def __init__(self, agent_name="CMO"):
        super().__init__(agent_name)
        self.failed_pdfs = []
    
    def extract_pdf_content(self, url):
        """
        Extrae contenido de un PDF usando pdfplumber.
        
        Returns:
            dict con 'text', 'pages', 'tables', 'size_mb'
        """
        if not PDF_AVAILABLE:
            print("   ❌ pdfplumber no disponible")
            return None
        
        try:
            print(f"   📥 Descargando PDF...")
            response = requests.get(url, headers=self.headers, timeout=30, verify=certifi.where())
            response.raise_for_status()
            
            pdf_size_mb = len(response.content) / (1024 * 1024)
            print(f"   📄 PDF descargado ({pdf_size_mb:.2f} MB)")
            
            # Abrir PDF con pdfplumber
            pdf = pdfplumber.open(io.BytesIO(response.content))
            
            # Extraer texto de todas las páginas
            full_text = ""
            tables_found = []
            
            for i, page in enumerate(pdf.pages):
                # Extraer texto
                page_text = page.extract_text()
                if page_text:
                    full_text += f"\n\n## Page {i+1}\n\n{page_text}"
                
                # Extraer tablas
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        tables_found.append({
                            'page': i+1,
                            'data': table
                        })
            
            pdf.close()
            
            return {
                'text': full_text,
                'pages': len(pdf.pages),
                'tables': tables_found,
                'size_mb': pdf_size_mb
            }
            
        except Exception as e:
            print(f"   ❌ Error procesando PDF: {e}")
            self.failed_pdfs.append({'url': url, 'error': str(e)})
            return None
    
    def save_pdf_raw(self, url, title):
        """Guarda el PDF raw en disco (Bronze Layer)."""
        try:
            response = requests.get(url, headers=self.headers, timeout=30, verify=certifi.where())
            response.raise_for_status()
            
            # Sanitizar nombre
            import re
            clean_title = re.sub(r'[^\w\s-]', '', title).strip().lower()
            clean_title = re.sub(r'[-\s]+', '-', clean_title)[:50]
            filename = f"{clean_title}.pdf"
            
            save_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "data", "raw", "cmo", "frameworks"
            )
            os.makedirs(save_dir, exist_ok=True)
            
            filepath = os.path.join(save_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return filepath
            
        except Exception as e:
            print(f"   ⚠️ Error guardando PDF: {e}")
            return None
    
    def run(self, limit=None):
        print(f"\n📚 [{self.__class__.__name__}] Marketing Frameworks (PDFs)...")
        
        frameworks_to_process = self.FRAMEWORKS if not limit else self.FRAMEWORKS[:limit]
        count = 0
        
        for framework in frameworks_to_process:
            try:
                print(f"\n📖 Procesando: {framework['title']}")
                print(f"   Concepto: {framework['concept']}")
                print(f"   Prioridad: {framework['priority']}")
                
                # Verificar si ya existe
                if self.url_exists(framework['url']):
                    print(f"   💤 Ya existe en la base de datos")
                    continue
                
                # Guardar PDF raw
                pdf_filepath = self.save_pdf_raw(framework['url'], framework['title'])
                if not pdf_filepath:
                    continue
                
                print(f"   ✅ PDF guardado en Bronze Layer")
                
                # Extraer contenido
                pdf_content = self.extract_pdf_content(framework['url'])
                
                if not pdf_content:
                    # Guardar metadata mínima aunque falle la extracción
                    doc = {
                        "source": "Marketing Framework",
                        "title": framework['title'],
                        "url": framework['url'],
                        "file_path": pdf_filepath,
                        "content_markdown": f"# {framework['title']}\n\n**Concepto clave**: {framework['concept']}\n\n*Extracción de PDF pendiente*",
                        "tags": ["framework", framework['category'], "strategic"],
                        "curated_category": "marketing_framework",
                        "core_concept": framework['concept'],
                        "priority": framework['priority'],
                        "extraction_status": "failed"
                    }
                    self.save_knowledge(doc)
                    continue
                
                # Crear documento enriquecido
                markdown = f"""# {framework['title']}

**Concepto clave**: {framework['concept']}  
**Categoría**: {framework['category']}  
**Páginas**: {pdf_content['pages']}  
**Tamaño**: {pdf_content['size_mb']:.2f} MB

---

{pdf_content['text']}
"""
                
                # Agregar información de tablas si existen
                if pdf_content['tables']:
                    markdown += f"\n\n## Tablas encontradas\n\nSe detectaron {len(pdf_content['tables'])} tablas en el documento.\n"
                
                doc = {
                    "source": "Marketing Framework",
                    "title": framework['title'],
                    "url": framework['url'],
                    "file_path": pdf_filepath,
                    "content_markdown": markdown,
                    "tags": ["framework", framework['category'], "strategic", "pdf"],
                    "curated_category": "marketing_framework",
                    "core_concept": framework['concept'],
                    "priority": framework['priority'],
                    "metadata": {
                        "pages": pdf_content['pages'],
                        "size_mb": pdf_content['size_mb'],
                        "tables_count": len(pdf_content['tables']),
                        "word_count": len(pdf_content['text'].split())
                    },
                    "extraction_status": "success"
                }
                
                self.save_knowledge(doc)
                count += 1
                print(f"   ✅ Framework procesado exitosamente")
                
                time.sleep(3)  # Rate limiting para PDFs pesados
                
            except Exception as e:
                print(f"   🔥 Error procesando {framework['title']}: {e}")
                continue
        
        print(f"\n📊 Resumen de Frameworks:")
        print(f"   ✅ Procesados exitosamente: {count}/{len(frameworks_to_process)}")
        if self.failed_pdfs:
            print(f"   ❌ PDFs fallidos: {len(self.failed_pdfs)}")
            for failed in self.failed_pdfs:
                print(f"      - {failed['url']}: {failed['error'][:50]}...")


class WebFrameworkSpider(BaseTechSpider):
    """
    Spider para frameworks disponibles como páginas web.
    Útil para contenido que no está en PDF.
    """
    
    WEB_FRAMEWORKS = [
        {
            "title": "See-Think-Do-Care Framework (Avinash Kaushik)",
            "url": "https://www.kaushik.net/avinash/see-think-do-content-marketing-measurement-business-framework/",
            "concept": "Intent-based Marketing",
            "category": "framework"
        },
        {
            "title": "Law of Shitty Clickthroughs (Andrew Chen)",
            "url": "https://andrewchen.com/the-law-of-shitty-clickthroughs/",
            "concept": "Decadencia de canales",
            "category": "principle"
        },
        {
            "title": "Product/Market Fit (Marc Andreessen)",
            "url": "https://pmarchive.com/guide_to_startups_part4.html",
            "concept": "Definición canónica de PMF",
            "category": "principle"
        },
        {
            "title": "Do Things that Don't Scale (Paul Graham)",
            "url": "https://paulgraham.com/ds.html",
            "concept": "Estrategia inicial de growth",
            "category": "principle"
        },
        {
            "title": "1,000 True Fans (Kevin Kelly)",
            "url": "https://kk.org/thetechnium/1000-true-fans/",
            "concept": "Monetización sostenible",
            "category": "principle"
        }
    ]
    
    def run(self, limit=None):
        print(f"\n🌐 [{self.__class__.__name__}] Web-based Frameworks...")
        
        frameworks_to_process = self.WEB_FRAMEWORKS if not limit else self.WEB_FRAMEWORKS[:limit]
        count = 0
        
        for framework in frameworks_to_process:
            try:
                print(f"\n🔗 Procesando: {framework['title']}")
                
                if self.url_exists(framework['url']):
                    print(f"   💤 Ya existe")
                    continue
                
                markdown = self.extract_content(framework['url'])
                
                if not markdown or len(markdown) < 500:
                    print(f"   ⚠️ Contenido insuficiente ({len(markdown) if markdown else 0} caracteres)")
                    continue
                
                filepath = self.save_raw_html(framework['url'], framework['title'], agent_subdir="cmo/frameworks")
                
                # Enriquecer con metadata
                enhanced_markdown = f"""# {framework['title']}

**Concepto clave**: {framework['concept']}  
**Categoría**: {framework['category']}

---

{markdown}
"""
                
                doc = {
                    "source": "Marketing Framework (Web)",
                    "title": framework['title'],
                    "url": framework['url'],
                    "file_path": filepath,
                    "content_markdown": enhanced_markdown,
                    "tags": ["framework", framework['category'], "principle"],
                    "curated_category": "marketing_framework",
                    "core_concept": framework['concept'],
                    "word_count": len(markdown.split())
                }
                
                self.save_knowledge(doc)
                count += 1
                print(f"   ✅ Framework guardado")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"   🔥 Error: {e}")
        
        print(f"\n📊 Web Frameworks procesados: {count}/{len(frameworks_to_process)}")


if __name__ == "__main__":
    print("🚀 Iniciando spiders de Marketing Frameworks...\n")
    
    # PDFs
    pdf_spider = MarketingFrameworkSpider(agent_name="CMO")
    pdf_spider.run(limit=5)
    
    print("\n" + "="*70 + "\n")
    
    # Web
    web_spider = WebFrameworkSpider(agent_name="CMO")
    web_spider.run(limit=5)
    
    print("\n✅ Frameworks completados")
