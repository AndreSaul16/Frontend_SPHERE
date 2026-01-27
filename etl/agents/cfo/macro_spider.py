"""
CFO Spiders - Macroeconomía
============================
Spiders para análisis macroeconómicos y memos de inversión.
Incluye: Howard Marks, Damodaran, Ray Dalio, Sequoia memos.
"""

import os
import sys
import time

# Importar clase base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.base_spider import BaseTechSpider


class MacroSpider(BaseTechSpider):
    """
    Spider base para análisis macroeconómicos.
    """
    
    MACRO_KEYWORDS = [
        'risk', 'market cycle', 'recession', 'inflation',
        'interest rate', 'capital allocation', 'equity premium',
        'valuation', 'crisis', 'treasury', 'fed', 'monetary policy'
    ]
    
    def matches_macro_keywords(self, title, content=""):
        """Verifica si contiene keywords macro."""
        combined = (title + " " + content).lower()
        return any(keyword in combined for keyword in self.MACRO_KEYWORDS)


class HowardMarksSpider(MacroSpider):
    """Spider para memos de Howard Marks (Oaktree Capital)."""
    
    MEMOS = [
        {
            "title": "Risk Revisited",
            "url": "https://www.oaktreecapital.com/insights/memo/risk-revisited",
            "concept": "Understanding market cycles and risk"
        }
    ]
    
    def run(self, limit=1):
        print(f"\n💼 [{self.__class__.__name__}] Howard Marks Memos...")
        
        count = 0
        for memo in self.MEMOS[:limit]:
            try:
                print(f"\n📝 {memo['title']}")
                
                if self.url_exists(memo['url']):
                    print(f"   💤 Ya existe")
                    continue
                
                markdown = self.extract_content(memo['url'])
                
                if not markdown or len(markdown) < 1000:
                    print(f"   ⚠️ Contenido insuficiente")
                    continue
                
                filepath = self.save_raw_html(memo['url'], memo['title'], agent_subdir="cfo/macro", prefix="HowardMarks_")
                
                doc = {
                    "source": "Howard Marks - Oaktree Capital",
                    "title": memo['title'],
                    "url": memo['url'],
                    "file_path": filepath,
                    "content_markdown": f"# {memo['title']}\n\n**Concepto**: {memo['concept']}\n\n---\n\n{markdown}",
                    "tags": ["risk-management", "market-cycles", "investment-philosophy", "howard-marks"],
                    "curated_category": "macro_investment",
                    "agent_target": "CFO"
                }
                
                self.save_knowledge(doc)
                count += 1
                print(f"   ✅ Guardado")
                time.sleep(2)
                
            except Exception as e:
                print(f"   🔥 Error: {e}")
        
        print(f"\n📊 Howard Marks: {count} memos procesados")


class DamodaranSpider(MacroSpider):
    """Spider para data de Aswath Damodaran (NYU Stern)."""
    
    RESOURCES = [
        {
            "title": "Equity Risk Premiums (ERP) - Latest Data",
            "url": "http://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html",
            "concept": "Country risk premiums for WACC calculation"
        }
    ]
    
    def run(self, limit=1):
        print(f"\n📈 [{self.__class__.__name__}] Aswath Damodaran Data...")
        
        count = 0
        for resource in self.RESOURCES[:limit]:
            try:
                print(f"\n📊 {resource['title']}")
                
                if self.url_exists(resource['url']):
                    print(f"   💤 Ya existe")
                    continue
                
                markdown = self.extract_content(resource['url'])
                
                if not markdown or len(markdown) < 200:
                    print(f"   ⚠️ Contenido insuficiente")
                    continue
                
                filepath = self.save_raw_html(resource['url'], resource['title'], agent_subdir="cfo/macro", prefix="Damodaran_")
                
                doc = {
                    "source": "Aswath Damodaran - NYU Stern",
                    "title": resource['title'],
                    "url": resource['url'],
                    "file_path": filepath,
                    "content_markdown": f"# {resource['title']}\n\n**Concepto**: {resource['concept']}\n\n---\n\n{markdown}",
                    "tags": ["equity-risk-premium", "wacc", "cost-of-capital", "valuation", "damodaran"],
                    "curated_category": "macro_data",
                    "agent_target": "CFO"
                }
                
                self.save_knowledge(doc)
                count += 1
                print(f"   ✅ Guardado")
                time.sleep(2)
                
            except Exception as e:
                print(f"   🔥 Error: {e}")
        
        print(f"\n📊 Damodaran: {count} datasets procesados")


class SequoiaSpider(MacroSpider):
    """Spider para memos de Sequoia Capital."""
    
    MEMOS = [
        {
            "title": "Crucible Moments - 2022 Crisis Memo",
            "url": "https://www.sequoiacap.com/article/crucible-moment/",
            "concept": "Cash management in downturns"
        }
    ]
    
    def run(self, limit=1):
        print(f"\n🏔️ [{self.__class__.__name__}] Sequoia Capital Memos...")
        
        count = 0
        for memo in self.MEMOS[:limit]:
            try:
                print(f"\n📝 {memo['title']}")
                
                if self.url_exists(memo['url']):
                    print(f"   💤 Ya existe")
                    continue
                
                markdown = self.extract_content(memo['url'])
                
                if not markdown or len(markdown) < 500:
                    print(f"   ⚠️ Contenido insuficiente")
                    continue
                
                filepath = self.save_raw_html(memo['url'], memo['title'], agent_subdir="cfo/macro", prefix="Sequoia_")
                
                doc = {
                    "source": "Sequoia Capital",
                    "title": memo['title'],
                    "url": memo['url'],
                    "file_path": filepath,
                    "content_markdown": f"# {memo['title']}\n\n**Concepto**: {memo['concept']}\n\n---\n\n{markdown}",
                    "tags": ["crisis-management", "cash-flow", "runway", "sequoia", "downturn"],
                    "curated_category": "macro_crisis",
                    "agent_target": "CFO"
                }
                
                self.save_knowledge(doc)
                count += 1
                print(f"   ✅ Guardado")
                time.sleep(2)
                
            except Exception as e:
                print(f"   🔥 Error: {e}")
        
        print(f"\n📊 Sequoia: {count} memos procesados")


class RayDalioSpider(MacroSpider):
    """Spider para contenido de Ray Dalio."""
    
    RESOURCES = [
        {
            "title": "How the Economic Machine Works",
            "url": "https://www.principles.com/big-debt-crises/",
            "concept": "Short-term and long-term debt cycles"
        }
    ]
    
    def run(self, limit=1):
        print(f"\n🌐 [{self.__class__.__name__}] Ray Dalio - Economic Principles...")
        
        count = 0
        for resource in self.RESOURCES[:limit]:
            try:
                print(f"\n📚 {resource['title']}")
                
                if self.url_exists(resource['url']):
                    print(f"   💤 Ya existe")
                    continue
                
                markdown = self.extract_content(resource['url'])
                
                if not markdown or len(markdown) < 500:
                    print(f"   ⚠️ Contenido insuficiente")
                    continue
                
                filepath = self.save_raw_html(resource['url'], resource['title'], agent_subdir="cfo/macro", prefix="Dalio_")
                
                doc = {
                    "source": "Ray Dalio - Principles",
                    "title": resource['title'],
                    "url": resource['url'],
                    "file_path": filepath,
                    "content_markdown": f"# {resource['title']}\n\n**Concepto**: {resource['concept']}\n\n---\n\n{markdown}",
                    "tags": ["economic-cycles", "debt-cycles", "macro-strategy", "ray-dalio"],
                    "curated_category": "macro_theory",
                    "agent_target": "CFO"
                }
                
                self.save_knowledge(doc)
                count += 1
                print(f"   ✅ Guardado")
                time.sleep(2)
                
            except Exception as e:
                print(f"   🔥 Error: {e}")
        
        print(f"\n📊 Ray Dalio: {count} recursos procesados")


if __name__ == "__main__":
    print("🚀 Iniciando spiders de Macroeconomía...\n")
    
    marks = HowardMarksSpider(agent_name="CFO")
    marks.run(limit=1)
    
    damodaran = DamodaranSpider(agent_name="CFO")
    damodaran.run(limit=1)
    
    sequoia = SequoiaSpider(agent_name="CFO")
    sequoia.run(limit=1)
    
    dalio = RayDalioSpider(agent_name="CFO")
    dalio.run(limit=1)
    
    print("\n✅ Macroeconomía completado")
