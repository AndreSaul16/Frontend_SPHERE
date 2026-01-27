"""
CFO Spiders - Regulatory & Reporting
=====================================
Spiders para documentos de regulación financiera y reporting.
Incluye: 10-Ks, Annual Reports, ASC 606, IFRS, SOX.
"""

import os
import sys
import time
import requests
import io

# Importar clase base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.base_spider import BaseTechSpider

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    print("⚠️ pdfplumber no disponible")
    PDF_AVAILABLE = False


class RegulatorySpider(BaseTechSpider):
    """
    Spider base para documentos de regulación y compliance.
    """
    
    def extract_pdf_text(self, url, max_pages=50):
        """Extrae texto de PDF con límite de páginas."""
        if not PDF_AVAILABLE:
            return None
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30, verify=False)
            response.raise_for_status()
            
            pdf = pdfplumber.open(io.BytesIO(response.content))
            
            # Limitar páginas para 10-Ks grandes
            pages_to_extract = min(len(pdf.pages), max_pages)
            
            text = ""
            for i in range(pages_to_extract):
                page_text = pdf.pages[i].extract_text()
                if page_text:
                    text += f"\n\n## Page {i+1}\n\n{page_text}"
            
            pdf.close()
            return text
            
        except Exception as e:
            print(f"   ❌ Error procesando PDF: {e}")
            return None


class AnnualReportsSpider(RegulatorySpider):
    """Spider para Annual Reports y 10-K filings."""
    
    REPORTS = [
        {
            "company": "Berkshire Hathaway",
            "title": "Annual Report 2023",
            "url": "https://www.berkshirehathaway.com/2023ar/2023ar.pdf",
            "focus": "Financial Tables - Cash Flow, Balance Sheet"
        }
    ]
    
    def run(self, limit=1):
        print(f"\n📄 [{self.__class__.__name__}] Annual Reports...")
        
        count = 0
        for report in self.REPORTS[:limit]:
            try:
                print(f"\n📊 {report['company']}: {report['title']}")
                
                if self.url_exists(report['url']):
                    print(f"   💤 Ya existe")
                    continue
                
                # Guardar PDF raw
                try:
                    response = requests.get(report['url'], headers=self.headers, timeout=30, verify=False)
                    response.raise_for_status()
                    
                    import re
                    safe_name = re.sub(r'[^\w\s-]', '', report['company']).strip().lower()
                    safe_name = re.sub(r'[-\s]+', '-', safe_name)
                    filename = f"{safe_name}_annual_report.pdf"
                    
                    save_dir = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                        "data", "raw", "cfo", "regulatory"
                    )
                    os.makedirs(save_dir, exist_ok=True)
                    
                    filepath = os.path.join(save_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"   ✅ PDF guardado ({len(response.content)/1024/1024:.1f} MB)")
                    
                except Exception as e:
                    print(f"   ⚠️ Error guardando PDF: {e}")
                    filepath = None
                
                # Extraer texto (primeras 50 páginas)
                pdf_text = self.extract_pdf_text(report['url'], max_pages=50)
                
                if pdf_text:
                    content = f"""# {report['company']} - {report['title']}

**Focus**: {report['focus']}

---

{pdf_text}
"""
                else:
                    content = f"""# {report['company']} - {report['title']}

**Focus**: {report['focus']}

*PDF disponible en archivo local. Extracción de texto pendiente.*
"""
                
                doc = {
                    "source": f"Annual Report - {report['company']}",
                    "title": f"{report['company']}: {report['title']}",
                    "url": report['url'],
                    "file_path": filepath,
                    "content_markdown": content,
                    "tags": ["annual-report", "10-k", "financial-statements", "sec"],
                    "curated_category": "regulatory_financial",
                    "company": report['company'],
                    "agent_target": "CFO"
                }
                
                self.save_knowledge(doc)
                count += 1
                print(f"   ✅ Report procesado")
                time.sleep(3)
                
            except Exception as e:
                print(f"   🔥 Error: {e}")
        
        print(f"\n📊 Annual Reports: {count} procesados")


class AccountingStandardsSpider(RegulatorySpider):
    """Spider para normas contables (ASC 606, IFRS 16, etc.)."""
    
    STANDARDS = [
        {
            "title": "ASC 606 - Revenue Recognition Guide",
            "url": "https://www.fasb.org/page/PageContent?pageId=/standards/revenue-recognition.html",
            "concept": "Revenue recognition for SaaS contracts",
            "type": "web"
        }
    ]
    
    def run(self, limit=1):
        print(f"\n⚖️ [{self.__class__.__name__}] Accounting Standards...")
        
        count = 0
        for standard in self.STANDARDS[:limit]:
            try:
                print(f"\n📋 {standard['title']}")
                
                if self.url_exists(standard['url']):
                    print(f"   💤 Ya existe")
                    continue
                
                if standard['type'] == 'web':
                    markdown = self.extract_content(standard['url'])
                    
                    if not markdown or len(markdown) < 300:
                        print(f"   ⚠️ Contenido insuficiente")
                        continue
                    
                    filepath = self.save_raw_html(standard['url'], standard['title'], agent_subdir="cfo/regulatory")
                else:
                    # PDF
                    pdf_text = self.extract_pdf_text(standard['url'])
                    markdown = pdf_text if pdf_text else "*Contenido PDF pendiente de extracción*"
                    filepath = None
                
                doc = {
                    "source": "Accounting Standards",
                    "title": standard['title'],
                    "url": standard['url'],
                    "file_path": filepath,
                    "content_markdown": f"# {standard['title']}\n\n**Concepto**: {standard['concept']}\n\n---\n\n{markdown}",
                    "tags": ["accounting", "gaap", "ifrs", "compliance", "revenue-recognition"],
                    "curated_category": "regulatory_accounting",
                    "agent_target": "CFO"
                }
                
                self.save_knowledge(doc)
                count += 1
                print(f"   ✅ Guardado")
                time.sleep(2)
                
            except Exception as e:
                print(f"   🔥 Error: {e}")
        
        print(f"\n📊 Standards: {count} procesados")


class BoardDeckSpider(RegulatorySpider):
    """Spider para templates de board decks y financial reporting."""
    
    TEMPLATES = [
        {
            "title": "Board Deck Template - Sequoia Capital",
            "url": "https://www.sequoiacap.com/article/building-a-board-deck/",
            "concept": "How to present financials to the board"
        }
    ]
    
    def run(self, limit=1):
        print(f"\n📊 [{self.__class__.__name__}] Board Deck Templates...")
        
        count = 0
        for template in self.TEMPLATES[:limit]:
            try:
                print(f"\n📋 {template['title']}")
                
                if self.url_exists(template['url']):
                    print(f"   💤 Ya existe")
                    continue
                
                markdown = self.extract_content(template['url'])
                
                if not markdown or len(markdown) < 500:
                    print(f"   ⚠️ Contenido insuficiente")
                    continue
                
                filepath = self.save_raw_html(template['url'], template['title'], agent_subdir="cfo/regulatory")
                
                doc = {
                    "source": "Board Deck Templates",
                    "title": template['title'],
                    "url": template['url'],
                    "file_path": filepath,
                    "content_markdown": f"# {template['title']}\n\n**Concepto**: {template['concept']}\n\n---\n\n{markdown}",
                    "tags": ["board-deck", "financial-reporting", "cfo-toolkit"],
                    "curated_category": "regulatory_reporting",
                    "agent_target": "CFO"
                }
                
                self.save_knowledge(doc)
                count += 1
                print(f"   ✅ Guardado")
                time.sleep(2)
                
            except Exception as e:
                print(f"   🔥 Error: {e}")
        
        print(f"\n📊 Board Decks: {count} templates procesados")


if __name__ == "__main__":
    print("🚀 Iniciando spiders de Regulatory & Reporting...\n")
    
    reports = AnnualReportsSpider(agent_name="CFO")
    reports.run(limit=1)
    
    standards = AccountingStandardsSpider(agent_name="CFO")
    standards.run(limit=1)
    
    boards = BoardDeckSpider(agent_name="CFO")
    boards.run(limit=1)
    
    print("\n✅ Regulatory completado")
