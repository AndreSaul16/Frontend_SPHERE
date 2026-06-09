"""
CMO Spiders - Case Studies
===========================
Spiders para casos de estudio de growth hacking y marketing.
"War Room": ingeniería inversa de tácticas exitosas.
"""

import os
import sys
import time
import certifi
from bs4 import BeautifulSoup
import requests

# Importar clase base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.base_spider import BaseTechSpider


class CaseStudySpider(BaseTechSpider):
    """
    Spider para casos de estudio de growth hacking.
    Extrae tácticas, métricas y lecciones aplicables.
    """
    
    # Casos de estudio prioritarios
    CASE_STUDIES = [
        {
            "company": "Airbnb",
            "title": "Craigslist Integration (Technical Growth Hack)",
            "url": "https://growthhackers.com/growth-studies/airbnb/",
            "tactic": "API Integration / Gray-hat SEO",
            "category": "technical_hack",
            "priority": "critical"
        },
        {
            "company": "Dropbox",
            "title": "Viral Referral Program",
            "url": "https://viral-loops.com/blog/dropbox-grew-3900-simple-referral-program/",
            "tactic": "Double-sided Incentive Referral",
            "category": "viral_loop",
            "priority": "critical"
        },
        {
            "company": "Salesforce",
            "title": "No Software Campaign (Enemy Creation)",
            "url": "https://www.salesforce.com/news/stories/the-history-of-salesforce/",
            "tactic": "Category Design / Positioning",
            "category": "branding",
            "priority": "high"
        },
        {
            "company": "HubSpot",
            "title": "Inbound Marketing (Category Creation)",
            "url": "https://www.hubspot.com/hs-fs/hub/53/file-13201504-pdf/docs/hubspotinboundmarketingworkbook-pdf.pdf",
            "tactic": "Content-Led Growth",
            "category": "category_creation",
            "priority": "high"
        },
        {
            "company": "Red Bull",
            "title": "Media House Strategy (Content as Product)",
            "url": "https://www.uni-potsdam.de/fileadmin/projects/professional-services/downloads/skripte-ws/Wintersemester2018/MS270_Red_Bull_Business_Case_080415.pdf",
            "tactic": "Content Marketing at Scale",
            "category": "content_strategy",
            "priority": "medium"
        },
        {
            "company": "Liquid Death",
            "title": "Branding Disruptivo (Death to Plastic)",
            "url": "https://h16m.com/wp-content/uploads/2024/06/Liquid-Death-Case-study.pdf",
            "tactic": "Counter-positioning / Meme Marketing",
            "category": "branding",
            "priority": "high"
        },
        {
            "company": "Slack",
            "title": "Product-Led Growth (Bottom-up)",
            "url": "https://openviewpartners.com/wp-content/uploads/2018/07/OpenView-Product-Led-Growth-Playbook.pdf",
            "tactic": "Freemium + Viral Collaboration",
            "category": "plg",
            "priority": "critical"
        }
    ]
    
    def __init__(self, agent_name="CMO"):
        super().__init__(agent_name)
        self.processed_count = 0
        self.failed_count = 0
    
    def extract_case_study_content(self, url, is_pdf=False):
        """
        Extrae contenido de caso de estudio.
        Detecta automáticamente si es PDF o HTML.
        """
        try:
            # Detectar tipo de contenido
            if url.endswith('.pdf') or is_pdf:
                return self._extract_pdf_case_study(url)
            else:
                return self.extract_content(url)
                
        except Exception as e:
            print(f"   ❌ Error extrayendo contenido: {e}")
            return None
    
    def _extract_pdf_case_study(self, url):
        """Extrae contenido de caso de estudio en PDF."""
        try:
            import pdfplumber
            import io
            
            response = requests.get(url, headers=self.headers, timeout=30, verify=certifi.where())
            response.raise_for_status()
            
            pdf = pdfplumber.open(io.BytesIO(response.content))
            
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n\n"
            
            pdf.close()
            return full_text
            
        except ImportError:
            print("   ⚠️ pdfplumber no disponible para PDFs")
            return None
        except Exception as e:
            print(f"   ❌ Error procesando PDF: {e}")
            return None
    
    def extract_growth_metrics(self, content):
        """
        Intenta extraer métricas clave del contenido.
        Busca patrones como: 3900%, 10x, $1M ARR, etc.
        """
        import re
        
        metrics = []
        
        # Patrones comunes de métricas
        patterns = [
            r'\d+%\s*growth',
            r'\d+x\s*increase',
            r'\$\d+[KMB]?\s*(?:ARR|revenue|sales)',
            r'\d+%\s*conversion',
            r'\d+(?:,\d+)*\s*users',
            r'\d+%\s*retention'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            metrics.extend(matches)
        
        return list(set(metrics))[:5]  # Top 5 métricas únicas
    
    def run(self, limit=None):
        print(f"\n🎯 [{self.__class__.__name__}] Case Studies (War Room)...")
        
        cases_to_process = self.CASE_STUDIES if not limit else self.CASE_STUDIES[:limit]
        
        for case in cases_to_process:
            try:
                print(f"\n📊 {case['company']}: {case['title']}")
                print(f"   Táctica: {case['tactic']}")
                print(f"   Categoría: {case['category']}")
                
                # Verificar si ya existe
                if self.url_exists(case['url']):
                    print(f"   💤 Ya existe en la base de datos")
                    continue
                
                # Detectar si es PDF
                is_pdf = case['url'].endswith('.pdf')
                
                # Guardar archivo raw
                if is_pdf:
                    # Guardar PDF
                    try:
                        response = requests.get(case['url'], headers=self.headers, timeout=30, verify=certifi.where())
                        response.raise_for_status()
                        
                        import re
                        clean_title = re.sub(r'[^\w\s-]', '', case['title']).strip().lower()
                        clean_title = re.sub(r'[-\s]+', '-', clean_title)[:50]
                        filename = f"{case['company']}_{clean_title}.pdf"
                        
                        save_dir = os.path.join(
                            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                            "data", "raw", "cmo", "case_studies"
                        )
                        os.makedirs(save_dir, exist_ok=True)
                        
                        filepath = os.path.join(save_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        print(f"   ✅ PDF guardado")
                        
                    except Exception as e:
                        print(f"   ⚠️ Error guardando PDF: {e}")
                        filepath = None
                else:
                    filepath = self.save_raw_html(
                        case['url'], 
                        f"{case['company']}_{case['title']}", 
                        agent_subdir="cmo/case_studies"
                    )
                
                # Extraer contenido
                content = self.extract_case_study_content(case['url'], is_pdf)
                
                if not content or len(content) < 300:
                    print(f"   ⚠️ Contenido insuficiente o no disponible")
                    self.failed_count += 1
                    
                    # Guardar metadata mínima
                    doc = {
                        "source": "Case Study",
                        "title": f"{case['company']}: {case['title']}",
                        "url": case['url'],
                        "file_path": filepath,
                        "content_markdown": f"# {case['company']}: {case['title']}\n\n**Táctica**: {case['tactic']}\n\n*Contenido pendiente de extracción*",
                        "tags": ["case-study", case['category'], case['company'].lower()],
                        "curated_category": "case_study",
                        "company": case['company'],
                        "tactic": case['tactic'],
                        "priority": case['priority'],
                        "extraction_status": "failed"
                    }
                    self.save_knowledge(doc)
                    continue
                
                # Extraer métricas si es posible
                metrics = self.extract_growth_metrics(content)
                
                # Crear markdown enriquecido
                markdown = f"""# {case['company']}: {case['title']}

**Táctica aplicada**: {case['tactic']}  
**Categoría**: {case['category']}  
**Prioridad**: {case['priority']}

"""
                
                if metrics:
                    markdown += f"""## Métricas clave detectadas

{chr(10).join(f'- {metric}' for metric in metrics)}

"""
                
                markdown += f"""---

## Contenido del Caso de Estudio

{content}
"""
                
                # Crear documento
                doc = {
                    "source": "Case Study",
                    "title": f"{case['company']}: {case['title']}",
                    "url": case['url'],
                    "file_path": filepath,
                    "content_markdown": markdown,
                    "tags": ["case-study", case['category'], case['company'].lower(), "war-room"],
                    "curated_category": "case_study",
                    "company": case['company'],
                    "tactic": case['tactic'],
                    "category": case['category'],
                    "priority": case['priority'],
                    "metrics_detected": metrics,
                    "word_count": len(content.split()),
                    "extraction_status": "success"
                }
                
                self.save_knowledge(doc)
                self.processed_count += 1
                print(f"   ✅ Caso de estudio procesado")
                
                time.sleep(3)
                
            except Exception as e:
                print(f"   🔥 Error procesando {case['company']}: {e}")
                self.failed_count += 1
                continue
        
        # Resumen
        print(f"\n{'='*70}")
        print(f"📊 Resumen de Case Studies:")
        print(f"   ✅ Procesados exitosamente: {self.processed_count}/{len(cases_to_process)}")
        print(f"   ❌ Fallidos: {self.failed_count}/{len(cases_to_process)}")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    print("🚀 Iniciando spider de Case Studies...\n")
    
    spider = CaseStudySpider(agent_name="CMO")
    spider.run()
    
    print("\n✅ Ejecución completada")
